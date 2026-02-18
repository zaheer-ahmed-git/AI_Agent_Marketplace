import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.deps import get_current_user, get_db
from app.models import User
from app.schemas.common import RunCreate, ThreadCreate
from app.services.runs import create_thread, get_owned_thread, run_agent

router = APIRouter(tags=["runs"])


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@router.post("/agents/{agent_id}/threads", status_code=201)
def open_thread(
    agent_id: int,
    body: ThreadCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_thread(db, user, agent_id, body.title)


@router.post("/threads/{thread_id}/runs")
def start_run(
    thread_id: int,
    body: RunCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    thread = get_owned_thread(db, user, thread_id)
    user_id = user.id
    owned_thread_id = thread.id
    message = body.message

    def generate():
        stream_db = SessionLocal()
        try:
            owner = stream_db.get(User, user_id)
            current = get_owned_thread(stream_db, owner, owned_thread_id)
            for item in run_agent(stream_db, owner, current, message):
                yield _sse(item["event"], item["data"])
        except Exception as exc:
            yield _sse("done", {"status": "failed", "error": str(exc)})
        finally:
            stream_db.close()

    return StreamingResponse(generate(), media_type="text/event-stream")
