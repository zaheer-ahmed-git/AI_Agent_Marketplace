import re

STOP_WORDS = {
    "about",
    "and",
    "are",
    "does",
    "from",
    "have",
    "into",
    "look",
    "mention",
    "note",
    "notes",
    "open",
    "please",
    "read",
    "save",
    "that",
    "the",
    "this",
    "what",
    "when",
    "with",
    "your",
}


def meaningful_terms(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [word for word in words if len(word) > 2 and word not in STOP_WORDS]
