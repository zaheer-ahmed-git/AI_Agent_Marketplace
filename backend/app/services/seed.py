from sqlalchemy.orm import Session

from app.models import (
    Agent,
    AgentVersion,
    KnowledgeDocument,
    Listing,
    Note,
    TestCase,
    TestSuite,
    User,
)
from app.schemas.common import slugify
from app.security import hash_password

DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "demo-password"

KNOWLEDGE = [
    {
        "title": "Onboarding guide",
        "body": "New teammates start with the workspace tour and a mentor for the first two weeks.",
        "source": "handbook",
    },
    {
        "title": "Refund policy",
        "body": "Refunds are available within 30 days when the usage ledger shows fewer than ten runs.",
        "source": "policy",
    },
    {
        "title": "Security guide",
        "body": "API keys stay in the environment and are never written into agent prompts.",
        "source": "security",
    },
]

NOTES = [
    ("Billing ticket", "Open billing ticket: invoice 1042 is disputed and waiting on finance."),
    ("Login issue", "Login issue: user cannot reset a password after three attempts."),
    ("Meeting notes", "Standup agreed to ship the catalog filter on Thursday."),
]

SEED_AGENTS = [
    {
        "name": "Research summarizer",
        "slug": "research-summarizer",
        "description": "Summarizes seeded knowledge documents before it answers.",
        "category": "research",
        "tags": ["research", "summary"],
        "system_prompt": "You are a research summarizer. Search the knowledge base before you answer, then quote the useful phrase.",
        "tools": ["knowledge_search"],
        "memory": False,
        "cases": [
            ("Onboarding summary", "Summarize the onboarding guide", "knowledge_search", "workspace tour"),
            ("Refund policy", "Search the refund policy", "knowledge_search", "30 days"),
            ("Security keys", "What does the security guide say about API keys", "knowledge_search", "never written into agent prompts"),
        ],
    },
    {
        "name": "Support triage",
        "slug": "support-triage",
        "description": "Reads support notes and points at the matching ticket.",
        "category": "support",
        "tags": ["support", "notes"],
        "system_prompt": "You triage support issues using the user's notes. Read the matching note before you reply.",
        "tools": ["notes"],
        "memory": True,
        "cases": [
            ("Billing ticket", "Look up the open billing ticket", "notes", "invoice 1042"),
            ("Login note", "What notes mention a login issue", "notes", "cannot reset a password"),
            ("Callback note", "Save a note that the customer wants a callback tomorrow", "notes", "callback"),
        ],
    },
    {
        "name": "Meeting notes",
        "slug": "meeting-notes",
        "description": "Captures meeting notes and can read the current UTC time.",
        "category": "productivity",
        "tags": ["meetings", "notes"],
        "system_prompt": "You write meeting notes and can check the current UTC time.",
        "tools": ["notes", "clock"],
        "memory": True,
        "cases": [
            ("UTC clock", "What time is it in UTC right now", "clock", "UTC"),
            ("Save notes", "Save meeting notes: catalog review moved to Friday", "notes", "Friday"),
            ("Read notes", "Read my meeting notes", "notes", "catalog filter"),
        ],
    },
    {
        "name": "Calculator tutor",
        "slug": "calculator-tutor",
        "description": "Shows arithmetic by calling the calculator tool.",
        "category": "education",
        "tags": ["math", "calculator"],
        "system_prompt": "You teach arithmetic. Use the calculator for every numeric question and show the result.",
        "tools": ["calculator"],
        "memory": False,
        "cases": [
            ("Multiply", "What is 12 * 7?", "calculator", "84"),
            ("Parentheses", "Calculate (3 + 5) * 2", "calculator", "16"),
            ("Divide", "What is 100 / 4?", "calculator", "25"),
        ],
    },
]


def _ensure_user(db: Session) -> User:
    user = db.query(User).filter(User.email == DEMO_EMAIL).one_or_none()
    if user is not None:
        return user
    user = User(
        email=DEMO_EMAIL,
        password_hash=hash_password(DEMO_PASSWORD),
        display_name="Demo User",
    )
    db.add(user)
    db.flush()
    return user


def _ensure_knowledge(db: Session) -> None:
    if db.query(KnowledgeDocument).count():
        return
    for item in KNOWLEDGE:
        db.add(KnowledgeDocument(**item))
    db.flush()


def _ensure_notes(db: Session, user: User) -> None:
    if db.query(Note).filter(Note.user_id == user.id).count():
        return
    for title, body in NOTES:
        db.add(Note(user_id=user.id, title=title, body=body))
    db.flush()


def _ensure_agent(db: Session, user: User, spec: dict) -> None:
    existing = db.query(Agent).filter(Agent.slug == spec["slug"]).one_or_none()
    if existing is not None:
        return
    agent = Agent(
        owner_id=user.id,
        name=spec["name"],
        slug=slugify(spec["slug"]),
        description=spec["description"],
        status="published",
    )
    db.add(agent)
    db.flush()
    version = AgentVersion(
        agent_id=agent.id,
        version_number=1,
        system_prompt=spec["system_prompt"],
        model="gpt-4o-mini",
        temperature=0.2,
        max_steps=6,
        tool_names=list(spec["tools"]),
        memory_enabled=spec["memory"],
    )
    db.add(version)
    db.flush()
    agent.published_version_id = version.id
    db.add(
        Listing(
            agent_id=agent.id,
            version_id=version.id,
            slug=spec["slug"],
            category=spec["category"],
            tags=list(spec["tags"]),
            install_count=0,
        )
    )
    suite = TestSuite(agent_id=agent.id, name=f"{spec['name']} suite")
    db.add(suite)
    db.flush()
    for name, prompt, tool, phrase in spec["cases"]:
        db.add(
            TestCase(
                suite_id=suite.id,
                name=name,
                input_text=prompt,
                expected_tool=tool,
                expected_phrase=phrase,
            )
        )
    db.flush()


def seed_all(db: Session) -> None:
    user = _ensure_user(db)
    _ensure_knowledge(db)
    _ensure_notes(db, user)
    for spec in SEED_AGENTS:
        _ensure_agent(db, user, spec)
    db.commit()
