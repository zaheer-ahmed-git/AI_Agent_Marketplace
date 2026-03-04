from sqlalchemy.orm import Session

from app.models import Note
from app.tools.textutil import meaningful_terms


def run_notes(db: Session | None, user_id: int | None, args: dict) -> str:
    if db is None or user_id is None:
        return "Error: notes are unavailable"
    action = (args.get("action") or "search").lower()
    if action == "create":
        body = (args.get("body") or args.get("query") or "").strip()
        title = (args.get("title") or "Note").strip()[:200] or "Note"
        note = Note(user_id=user_id, title=title, body=body)
        db.add(note)
        db.flush()
        return f"Saved note '{note.title}': {note.body}"
    terms = meaningful_terms(str(args.get("query") or ""))
    notes = db.query(Note).filter(Note.user_id == user_id).order_by(Note.id.desc()).all()
    if terms:
        notes = [
            note
            for note in notes
            if any(term in f"{note.title} {note.body}".lower() for term in terms)
        ]
    if not notes:
        return "No matching notes."
    return "\n".join(f"{note.title}: {note.body}" for note in notes[:5])
