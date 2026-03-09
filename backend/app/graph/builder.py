from typing import Annotated

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from app.config import settings
from app.context import current_db
from app.graph.offline import choose_tool, last_human_text
from app.models import AgentVersion
from app.tools.registry import TOOL_SCHEMAS, execute_tool


class AgentState(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    agent_version_id: int
    user_id: int
    step_count: int
    max_steps: int
    tool_names: list[str]
    system_prompt: str
    model: str
    temperature: float
    memory_enabled: bool


def _content(message) -> str:
    content = getattr(message, "content", "")
    return content if isinstance(content, str) else str(content)


def _tool_calls(message) -> list[dict]:
    calls = getattr(message, "tool_calls", None) or []
    normalized = []
    for call in calls:
        if isinstance(call, dict):
            normalized.append(call)
    return normalized


def _answer_from_tools(messages) -> str:
    start = 0
    for index, message in enumerate(messages):
        if isinstance(message, HumanMessage):
            start = index
    lines = [_content(message) for message in messages[start:] if isinstance(message, ToolMessage)]
    body = "\n".join(line for line in lines if line).strip()
    if not body:
        return "I could not find a result."
    return f"Here is what I found:\n{body}"


def _visible_messages(state: AgentState):
    messages = list(state.get("messages") or [])
    if state.get("memory_enabled", True):
        return messages
    start = 0
    for index, message in enumerate(messages):
        if isinstance(message, HumanMessage):
            start = index
    return messages[start:]


def _call_openai(state: AgentState):
    from langchain_openai import ChatOpenAI

    selected = [TOOL_SCHEMAS[name] for name in state.get("tool_names") or [] if name in TOOL_SCHEMAS]
    llm = ChatOpenAI(
        model=state.get("model") or "gpt-4o-mini",
        temperature=float(state.get("temperature") or 0),
        api_key=settings.openai_api_key,
    )
    if selected:
        llm = llm.bind_tools(selected)
    prompt = [SystemMessage(content=state.get("system_prompt") or "You are a helpful agent.")]
    prompt.extend(_visible_messages(state))
    return llm.invoke(prompt)


def load_config(state: AgentState) -> dict:
    db = current_db.get()
    if db is None:
        raise RuntimeError("Database session is not available")
    version = db.get(AgentVersion, state["agent_version_id"])
    if version is None:
        raise RuntimeError("Agent version not found")
    return {
        "system_prompt": version.system_prompt,
        "model": version.model,
        "temperature": version.temperature,
        "max_steps": version.max_steps,
        "tool_names": list(version.tool_names or []),
        "memory_enabled": bool(version.memory_enabled),
    }


def agent_node(state: AgentState) -> dict:
    messages = list(state.get("messages") or [])
    step = int(state.get("step_count") or 0) + 1
    max_steps = int(state.get("max_steps") or 6)
    if step > max_steps:
        return {
            "messages": [AIMessage(content="Stopped because the step limit was reached.")],
            "step_count": step,
        }
    if messages and isinstance(messages[-1], ToolMessage):
        return {"messages": [AIMessage(content=_answer_from_tools(messages))], "step_count": step}
    if settings.use_llm and settings.openai_api_key:
        try:
            return {"messages": [_call_openai(state)], "step_count": step}
        except Exception as exc:
            return {
                "messages": [AIMessage(content=f"The model request failed: {exc}")],
                "step_count": step,
            }
    decision = choose_tool(last_human_text(messages), list(state.get("tool_names") or []))
    if decision and step < max_steps:
        name, args = decision
        message = AIMessage(
            content="",
            tool_calls=[{"id": f"call_{step}", "name": name, "args": args}],
        )
        return {"messages": [message], "step_count": step}
    return {
        "messages": [AIMessage(content="I can help with the tools configured for this agent.")],
        "step_count": step,
    }


def tools_node(state: AgentState) -> dict:
    messages = list(state.get("messages") or [])
    calls = _tool_calls(messages[-1]) if messages else []
    enabled = set(state.get("tool_names") or [])
    db = current_db.get()
    user_id = state.get("user_id")
    outputs = []
    for call in calls:
        name = str(call.get("name") or "")
        if name not in enabled:
            result = f"Error: {name} is not enabled"
        else:
            result = execute_tool(name, call.get("args") or {}, db, user_id)
        outputs.append(
            ToolMessage(content=result, tool_call_id=str(call.get("id") or name), name=name)
        )
    return {
        "messages": outputs,
        "step_count": int(state.get("step_count") or 0) + 1,
    }


def route_after_agent(state: AgentState) -> str:
    messages = list(state.get("messages") or [])
    if not messages:
        return "end"
    calls = _tool_calls(messages[-1])
    if calls and int(state.get("step_count") or 0) < int(state.get("max_steps") or 1):
        return "tools"
    return "end"


def route_after_tools(state: AgentState) -> str:
    if int(state.get("step_count") or 0) >= int(state.get("max_steps") or 1):
        return "end"
    return "agent"


def compile_graph(checkpointer):
    builder = StateGraph(AgentState)
    builder.add_node("load_config", load_config)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", tools_node)
    builder.add_edge(START, "load_config")
    builder.add_edge("load_config", "agent")
    builder.add_conditional_edges("agent", route_after_agent, {"tools": "tools", "end": END})
    builder.add_conditional_edges("tools", route_after_tools, {"agent": "agent", "end": END})
    return builder.compile(checkpointer=checkpointer)
