import json
import time
from collections.abc import Iterator

from fastapi import HTTPException
from langchain_core.messages import HumanMessage, ToolMessage
from sqlalchemy.orm import Session

from app.context import current_db
from app.graph.runtime import get_graph
from app.models import Run, RunEvent, Thread, User
from app.services.agents import get_owned_agent, latest_version


def create_thread(db: Session, user: User, agent_id: int, title: str | None) -> dict:
    agent = get_owned_agent(db, user, agent_id)
    version = latest_version(db, agent)
    thread = Thread(
        agent_id=agent.id,
        user_id=user.id,
        version_id=version.id,
        title=(title or "Conversation")[:200],
    )
    db.add(thread)
    db.commit()
    db.refresh(thread)
    return {
        "id": thread.id,
        "agent_id": thread.agent_id,
        "version_id": thread.version_id,
        "title": thread.title,
    }


def get_owned_thread(db: Session, user: User, thread_id: int) -> Thread:
    thread = db.get(Thread, thread_id)
    if thread is None or thread.user_id != user.id:
        raise HTTPException(status_code=404, detail="Thread not found")
    return thread


def _content(message) -> str:
    content = getattr(message, "content", "")
    return content if isinstance(content, str) else str(content)


def _calls(message) -> list[dict]:
    calls = []
    for call in getattr(message, "tool_calls", None) or []:
        if isinstance(call, dict):
            calls.append({"name": call.get("name"), "args": call.get("args"), "id": call.get("id")})
    return calls


def _as_list(messages):
    if messages is None:
        return []
    if isinstance(messages, list):
        return messages
    return [messages]


def chunk_words(text: str) -> list[str]:
    parts = text.split(" ")
    chunks = []
    for index, part in enumerate(parts):
        chunks.append(part if index == len(parts) - 1 else part + " ")
    return [chunk for chunk in chunks if chunk]


def estimate_tokens(*parts: str) -> int:
    text = " ".join(part for part in parts if part)
    if not text:
        return 0
    return max(1, len(text) // 4)


def run_agent(db: Session, user: User, thread: Thread, message: str) -> Iterator[dict]:
    run = Run(thread_id=thread.id, status="running", user_message=message)
    db.add(run)
    db.commit()
    db.refresh(run)
    started = time.perf_counter()
    assistant_parts: list[str] = []
    step_count = 0
    token = current_db.set(db)
    try:
        graph = get_graph()
        config = {"configurable": {"thread_id": str(thread.id)}}
        inputs = {
            "messages": [HumanMessage(content=message)],
            "agent_version_id": thread.version_id,
            "user_id": user.id,
            "step_count": 0,
        }
        for chunk in graph.stream(inputs, config, stream_mode="updates"):
            for node_name, update in chunk.items():
                messages = _as_list((update or {}).get("messages"))
                data: dict = {"node": node_name}
                calls: list[dict] = []
                tools: list[dict] = []
                for item in messages:
                    calls.extend(_calls(item))
                    if isinstance(item, ToolMessage):
                        tools.append({"name": item.name, "result": _content(item)})
                if calls:
                    data["tool_calls"] = calls
                if tools:
                    data["tools"] = tools
                if node_name in {"agent", "tools"}:
                    step_count += 1
                data["step_count"] = step_count
                db.add(
                    RunEvent(
                        run_id=run.id,
                        node_name=node_name,
                        payload=json.dumps(data)[:4000],
                    )
                )
                yield {"event": "node", "data": data}
                if node_name == "agent":
                    for item in messages:
                        content = _content(item)
                        if content and not _calls(item):
                            for piece in chunk_words(content):
                                assistant_parts.append(piece)
                                yield {"event": "token", "data": {"text": piece}}
        assistant = "".join(assistant_parts)
        run.status = "completed"
        run.assistant_message = assistant
        run.step_count = step_count
        run.estimated_tokens = estimate_tokens(message, assistant)
        run.error = None
        run.latency_ms = int((time.perf_counter() - started) * 1000)
        yield {
            "event": "done",
            "data": {
                "run_id": run.id,
                "status": "completed",
                "latency_ms": run.latency_ms,
                "step_count": step_count,
                "estimated_tokens": run.estimated_tokens,
            },
        }
    except Exception as exc:
        run.status = "failed"
        run.error = str(exc)[:2000]
        run.step_count = step_count
        run.latency_ms = int((time.perf_counter() - started) * 1000)
        yield {
            "event": "done",
            "data": {
                "run_id": run.id,
                "status": "failed",
                "error": run.error,
                "latency_ms": run.latency_ms,
                "step_count": step_count,
            },
        }
    finally:
        db.commit()
        current_db.reset(token)
