from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models import User
from app.services import evaluation

router = APIRouter(tags=["tests"])


@router.get("/agents/{agent_id}/tests")
def get_tests(
    agent_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return evaluation.list_tests(db, user, agent_id)


@router.post("/agents/{agent_id}/tests/run")
def run_tests(
    agent_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return evaluation.run_suite(db, user, agent_id)
