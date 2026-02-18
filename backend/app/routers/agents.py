from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models import User
from app.schemas.common import AgentPatch, AgentWrite, PublishRequest, VersionCreate
from app.services import agents as agent_service

router = APIRouter(tags=["agents"])


@router.get("/agents")
def list_agents(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return agent_service.list_agents(db, user)


@router.post("/agents", status_code=201)
def create_agent(
    body: AgentWrite,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return agent_service.create_agent(db, user, body)


@router.get("/agents/{agent_id}")
def get_agent(
    agent_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    agent = agent_service.get_owned_agent(db, user, agent_id)
    return agent_service.agent_detail(db, agent)


@router.patch("/agents/{agent_id}")
def patch_agent(
    agent_id: int,
    body: AgentPatch,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return agent_service.update_agent(db, user, agent_id, body)


@router.post("/agents/{agent_id}/versions", status_code=201)
def create_version(
    agent_id: int,
    body: VersionCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return agent_service.create_version(db, user, agent_id, body)


@router.post("/agents/{agent_id}/publish")
def publish_agent(
    agent_id: int,
    body: PublishRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return agent_service.publish_agent(db, user, agent_id, body)


@router.post("/agents/{agent_id}/archive")
def archive_agent(
    agent_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return agent_service.archive_agent(db, user, agent_id)
