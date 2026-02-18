from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models import User
from app.schemas.common import ReviewCreate
from app.services import marketplace as market

router = APIRouter(tags=["marketplace"])


@router.get("/marketplace")
def list_listings(
    q: str | None = None,
    category: str | None = None,
    min_rating: float | None = None,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return market.list_marketplace(db, q=q, category=category, min_rating=min_rating)


@router.get("/marketplace/{slug}")
def get_listing(
    slug: str,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return market.get_listing_detail(db, slug)


@router.post("/marketplace/{slug}/install", status_code=201)
def install_listing(
    slug: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return market.install_listing(db, user, slug)


@router.post("/marketplace/{slug}/reviews", status_code=201)
def create_review(
    slug: str,
    body: ReviewCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return market.add_review(db, user, slug, body)
