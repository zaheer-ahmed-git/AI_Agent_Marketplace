import re

from langchain_core.messages import HumanMessage


_PAREN_EXPR = re.compile(
    r"\((?:\d+(?:\.\d+)?\s*[\+\-\*\/]\s*)+\d+(?:\.\d+)?\)(?:\s*[\+\-\*\/]\s*\d+(?:\.\d+)?)*"
)
_FLAT_EXPR = re.compile(r"\d+(?:\.\d+)?(?:\s*[\+\-\*\/]\s*\d+(?:\.\d+)?)+")


def extract_expression(text: str) -> str | None:
    match = _PAREN_EXPR.search(text)
    if match:
        return match.group(0).strip()
    match = _FLAT_EXPR.search(text)
    if match:
        return match.group(0).strip()
    return None


def last_human_text(messages) -> str:
    text = ""
    for message in messages or []:
        if isinstance(message, HumanMessage):
            content = message.content
            text = content if isinstance(content, str) else str(content)
    return text


def choose_tool(text: str, tool_names: list[str]) -> tuple[str, dict] | None:
    """Pick one allowlisted tool from the user text when no model is configured."""
    allowed = set(tool_names or [])
    lower = text.lower()
    if "calculator" in allowed:
        expression = extract_expression(text)
        if expression:
            return "calculator", {"expression": expression}
    if "clock" in allowed and any(word in lower for word in ("time", "utc", "clock")):
        return "clock", {}
    if "notes" in allowed and any(word in lower for word in ("note", "ticket", "callback", "meeting")):
        if "save" in lower or "write" in lower:
            body = text.split(":", 1)[1].strip() if ":" in text else text
            return "notes", {"action": "create", "title": "Note", "body": body}
        return "notes", {"action": "search", "query": text}
    if "knowledge_search" in allowed and any(
        word in lower
        for word in ("search", "summarize", "summary", "policy", "guide", "knowledge", "document")
    ):
        return "knowledge_search", {"query": text}
    return None
