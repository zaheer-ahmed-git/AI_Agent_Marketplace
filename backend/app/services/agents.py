from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Agent, AgentVersion, Listing, User
from app.schemas.common import (
    AgentPatch,
    AgentWrite,
    PublishRequest,
    VersionCreate,
    clean_tools,
    slugify,
)
from app.timeutil import iso, utcnow


def _unique_agent_slug(db: Session, base: str) -> str:
    slug = base
    number = 2
    while db.query(Agent).filter(Agent.slug == slug).first() is not None:
        slug = f"{base}-{number}"
        number += 1
    return slug


def _unique_listing_slug(db: Session, base: str, listing_id: int | None = None) -> str:
    slug = base
    number = 2
    while True:
        found = db.query(Listing).filter(Listing.slug == slug).one_or_none()
        if found is None or found.id == listing_id:
            return slug
        slug = f"{base}-{number}"
        number += 1


def get_owned_agent(db: Session, user: User, agent_id: int) -> Agent:
    agent = db.get(Agent, agent_id)
    if agent is None or agent.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


def latest_version(db: Session, agent: Agent) -> AgentVersion:
    version = (
        db.query(AgentVersion)
        .filter(AgentVersion.agent_id == agent.id)
        .order_by(AgentVersion.version_number.desc())
        .first()
    )
    if version is None:
        raise HTTPException(status_code=400, detail="Agent has no version")
    return version


def _version_dict(version: AgentVersion) -> dict:
    return {
        "id": version.id,
        "version_number": version.version_number,
        "system_prompt": version.system_prompt,
        "model": version.model,
        "temperature": version.temperature,
        "max_steps": version.max_steps,
        "tool_names": list(version.tool_names or []),
        "memory_enabled": bool(version.memory_enabled),
        "created_at": iso(version.created_at),
    }


def agent_summary(db: Session, agent: Agent) -> dict:
    version = (
        db.query(AgentVersion)
        .filter(AgentVersion.agent_id == agent.id)
        .order_by(AgentVersion.version_number.desc())
        .first()
    )
    return {
        "id": agent.id,
        "name": agent.name,
        "slug": agent.slug,
        "description": agent.description,
        "status": agent.status,
        "updated_at": iso(agent.updated_at),
        "latest_version": version.version_number if version else None,
    }


def agent_detail(db: Session, agent: Agent) -> dict:
    versions = (
        db.query(AgentVersion)
        .filter(AgentVersion.agent_id == agent.id)
        .order_by(AgentVersion.version_number.asc())
        .all()
    )
    listing = db.query(Listing).filter(Listing.agent_id == agent.id).one_or_none()
    payload = agent_summary(db, agent)
    payload["versions"] = [_version_dict(version) for version in versions]
    payload["listing"] = None
    if listing is not None:
        payload["listing"] = {
            "slug": listing.slug,
            "category": listing.category,
            "tags": list(listing.tags or []),
            "install_count": listing.install_count,
            "version_id": listing.version_id,
        }
    return payload


def add_agent_with_version(
    db: Session,
    user: User,
    *,
    name: str,
    description: str,
    system_prompt: str,
    model: str,
    temperature: float,
    max_steps: int,
    tool_names: list[str],
    memory_enabled: bool,
) -> tuple[Agent, AgentVersion]:
    tools = clean_tools(tool_names)
    agent = Agent(
        owner_id=user.id,
        name=name.strip(),
        slug=_unique_agent_slug(db, slugify(name)),
        description=description or "",
        status="draft",
    )
    db.add(agent)
    db.flush()
    version = AgentVersion(
        agent_id=agent.id,
        version_number=1,
        system_prompt=system_prompt,
        model=model,
        temperature=temperature,
        max_steps=max_steps,
        tool_names=tools,
        memory_enabled=memory_enabled,
    )
    db.add(version)
    db.flush()
    return agent, version


def create_agent(db: Session, user: User, body: AgentWrite) -> dict:
    agent, _version = add_agent_with_version(
        db,
        user,
        name=body.name,
        description=body.description,
        system_prompt=body.system_prompt,
        model=body.model,
        temperature=body.temperature,
        max_steps=body.max_steps,
        tool_names=body.tool_names,
        memory_enabled=body.memory_enabled,
    )
    db.commit()
    db.refresh(agent)
    return agent_detail(db, agent)


def update_agent(db: Session, user: User, agent_id: int, body: AgentPatch) -> dict:
    agent = get_owned_agent(db, user, agent_id)
    if body.name is not None:
        agent.name = body.name.strip()
    if body.description is not None:
        agent.description = body.description
    agent.updated_at = utcnow()
    db.commit()
    db.refresh(agent)
    return agent_detail(db, agent)


def create_version(db: Session, user: User, agent_id: int, body: VersionCreate) -> dict:
    agent = get_owned_agent(db, user, agent_id)
    current = latest_version(db, agent)
    version = AgentVersion(
        agent_id=agent.id,
        version_number=current.version_number + 1,
        system_prompt=body.system_prompt,
        model=body.model,
        temperature=body.temperature,
        max_steps=body.max_steps,
        tool_names=clean_tools(body.tool_names),
        memory_enabled=body.memory_enabled,
    )
    db.add(version)
    agent.updated_at = utcnow()
    db.commit()
    db.refresh(version)
    return _version_dict(version)


def publish_agent(db: Session, user: User, agent_id: int, body: PublishRequest) -> dict:
    agent = get_owned_agent(db, user, agent_id)
    if body.version_id is None:
        version = latest_version(db, agent)
    else:
        version = db.get(AgentVersion, body.version_id)
        if version is None or version.agent_id != agent.id:
            raise HTTPException(status_code=404, detail="Version not found")
    listing = db.query(Listing).filter(Listing.agent_id == agent.id).one_or_none()
    base_slug = slugify(body.slug or (listing.slug if listing else agent.slug))
    tags = [tag.strip()[:40] for tag in body.tags if tag.strip()][:8]
    if listing is None:
        listing = Listing(
            agent_id=agent.id,
            version_id=version.id,
            slug=_unique_listing_slug(db, base_slug),
            category=body.category.strip(),
            tags=tags,
            install_count=0,
        )
        db.add(listing)
    else:
        listing.version_id = version.id
        listing.category = body.category.strip()
        listing.tags = tags
        listing.slug = _unique_listing_slug(db, base_slug, listing.id)
        listing.updated_at = utcnow()
    agent.status = "published"
    agent.published_version_id = version.id
    agent.updated_at = utcnow()
    db.commit()
    db.refresh(agent)
    return agent_detail(db, agent)


def archive_agent(db: Session, user: User, agent_id: int) -> dict:
    agent = get_owned_agent(db, user, agent_id)
    agent.status = "archived"
    agent.updated_at = utcnow()
    db.commit()
    db.refresh(agent)
    return agent_detail(db, agent)


def list_agents(db: Session, user: User) -> list[dict]:
    agents = (
        db.query(Agent)
        .filter(Agent.owner_id == user.id)
        .order_by(Agent.updated_at.desc(), Agent.id.desc())
        .all()
    )
    return [agent_summary(db, agent) for agent in agents]
