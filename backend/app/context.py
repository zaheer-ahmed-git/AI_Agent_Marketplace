from contextvars import ContextVar

from sqlalchemy.orm import Session

current_db: ContextVar[Session | None] = ContextVar("current_db", default=None)
