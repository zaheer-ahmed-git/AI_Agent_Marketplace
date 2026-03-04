from sqlalchemy.orm import Session

from app.models import KnowledgeDocument
from app.tools.textutil import meaningful_terms


def search_knowledge(db: Session | None, query: str) -> str:
    if db is None:
        return "Error: knowledge search is unavailable"
    terms = meaningful_terms(query)
    scored: list[tuple[int, KnowledgeDocument]] = []
    for doc in db.query(KnowledgeDocument).all():
        haystack = f"{doc.title} {doc.body}".lower()
        score = sum(1 for term in terms if term in haystack)
        if score:
            scored.append((score, doc))
    scored.sort(key=lambda item: (-item[0], item[1].title))
    if not scored:
        return "No matching documents."
    best = scored[0][1]
    return f"{best.title}: {best.body}"
