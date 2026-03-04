from sqlalchemy.orm import Session

from app.tools.calculator import safe_calc
from app.tools.clock import current_utc
from app.tools.knowledge import search_knowledge
from app.tools.notes import run_notes

TOOL_SCHEMAS = {
    "calculator": {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Evaluate a safe arithmetic expression.",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string"}},
                "required": ["expression"],
            },
        },
    },
    "clock": {
        "type": "function",
        "function": {
            "name": "clock",
            "description": "Return the current UTC time.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    "notes": {
        "type": "function",
        "function": {
            "name": "notes",
            "description": "Search or save the signed-in user's notes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["search", "create"]},
                    "query": {"type": "string"},
                    "title": {"type": "string"},
                    "body": {"type": "string"},
                },
                "required": ["action"],
            },
        },
    },
    "knowledge_search": {
        "type": "function",
        "function": {
            "name": "knowledge_search",
            "description": "Keyword search over seeded knowledge documents.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
}


def execute_tool(name: str, args: dict, db: Session | None, user_id: int | None) -> str:
    if name == "calculator":
        return safe_calc(str(args.get("expression") or ""))
    if name == "clock":
        return current_utc()
    if name == "notes":
        return run_notes(db, user_id, args)
    if name == "knowledge_search":
        return search_knowledge(db, str(args.get("query") or ""))
    return f"Error: tool {name} is not allowed"
