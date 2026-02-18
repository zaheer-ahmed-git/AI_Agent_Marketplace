from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models import User
from app.services import monitoring as monitor

router = APIRouter(tags=["monitoring"])


@router.get("/monitoring/summary")
def monitoring_summary(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return monitor.summary(db, user)


@router.get("/monitoring/runs")
def monitoring_runs(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return monitor.recent_runs(db, user)
