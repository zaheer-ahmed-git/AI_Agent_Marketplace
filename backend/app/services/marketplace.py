from fastapi import HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models import Agent, AgentVersion, Install, Listing, Review, User
from app.schemas.common import ReviewCreate
from app.services.agents import add_agent_with_version
from app.timeutil import iso


def _published_query(db: Session):
    return (
        db.query(Listing, Agent)
        .join(Agent, Listing.agent_id == Agent.id)
        .filter(Agent.status == "published")
    )


def _rating(db: Session, listing_id: int) -> tuple[float | None, int]:
    reviews = db.query(Review).filter(Review.listing_id == listing_id).all()
    if not reviews:
        return None, 0
    average = sum(review.rating for review in reviews) / len(reviews)
    return round(average, 2), len(reviews)


def _card(db: Session, listing: Listing, agent: Agent, version: AgentVersion | None) -> dict:
    rating, count = _rating(db, listing.id)
    return {
        "slug": listing.slug,
        "name": agent.name,
        "description": agent.description,
        "category": listing.category,
        "tags": list(listing.tags or []),
        "install_count": listing.install_count,
        "rating": rating,
        "review_count": count,
        "tool_names": list(version.tool_names or []) if version else [],
    }


def list_marketplace(
    db: Session,
    *,
    q: str | None = None,
    category: str | None = None,
    min_rating: float | None = None,
) -> list[dict]:
    query = _published_query(db)
    if category:
        query = query.filter(Listing.category == category)
    if q:
        like = f"%{q.strip().lower()}%"
        query = query.filter(
            or_(func.lower(Agent.name).like(like), func.lower(Agent.description).like(like))
        )
    cards = []
    for listing, agent in query.order_by(Listing.install_count.desc(), Agent.name.asc()).all():
        version = db.get(AgentVersion, listing.version_id)
        card = _card(db, listing, agent, version)
        if min_rating is not None and (card["rating"] is None or card["rating"] < min_rating):
            continue
        cards.append(card)
    return cards


def get_listing_detail(db: Session, slug: str) -> dict:
    row = _published_query(db).filter(Listing.slug == slug).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Listing not found")
    listing, agent = row
    version = db.get(AgentVersion, listing.version_id)
    payload = _card(db, listing, agent, version)
    payload["system_prompt"] = version.system_prompt if version else ""
    payload["model"] = version.model if version else ""
    payload["temperature"] = version.temperature if version else None
    payload["max_steps"] = version.max_steps if version else None
    payload["memory_enabled"] = bool(version.memory_enabled) if version else False
    reviews = (
        db.query(Review, User)
        .join(User, Review.user_id == User.id)
        .filter(Review.listing_id == listing.id)
        .order_by(Review.created_at.desc())
        .all()
    )
    payload["reviews"] = [
        {
            "id": review.id,
            "rating": review.rating,
            "comment": review.comment,
            "author": user.display_name,
            "created_at": iso(review.created_at),
        }
        for review, user in reviews
    ]
    return payload


def install_listing(db: Session, user: User, slug: str) -> dict:
    row = _published_query(db).filter(Listing.slug == slug).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Listing not found")
    listing, source = row
    version = db.get(AgentVersion, listing.version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="Listing version not found")
    agent, copy = add_agent_with_version(
        db,
        user,
        name=source.name,
        description=source.description,
        system_prompt=version.system_prompt,
        model=version.model,
        temperature=version.temperature,
        max_steps=version.max_steps,
        tool_names=list(version.tool_names or []),
        memory_enabled=bool(version.memory_enabled),
    )
    db.add(Install(user_id=user.id, listing_id=listing.id, agent_id=agent.id))
    listing.install_count = int(listing.install_count or 0) + 1
    db.commit()
    db.refresh(copy)
    return {
        "agent_id": agent.id,
        "version_id": copy.id,
        "slug": agent.slug,
        "name": agent.name,
        "system_prompt": copy.system_prompt,
        "tool_names": list(copy.tool_names or []),
        "model": copy.model,
        "temperature": copy.temperature,
        "max_steps": copy.max_steps,
        "memory_enabled": bool(copy.memory_enabled),
    }


def add_review(db: Session, user: User, slug: str, body: ReviewCreate) -> dict:
    row = _published_query(db).filter(Listing.slug == slug).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Listing not found")
    listing, _agent = row
    existing = (
        db.query(Review)
        .filter(Review.user_id == user.id, Review.listing_id == listing.id)
        .one_or_none()
    )
    if existing is not None:
        raise HTTPException(status_code=409, detail="You already reviewed this listing")
    review = Review(
        user_id=user.id,
        listing_id=listing.id,
        rating=body.rating,
        comment=body.comment.strip(),
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return {
        "id": review.id,
        "rating": review.rating,
        "comment": review.comment,
        "author": user.display_name,
        "created_at": iso(review.created_at),
    }
