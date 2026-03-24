import math

from sqlalchemy.orm import Session

from app.models import Agent, Run, Thread, User
from app.timeutil import iso


def _user_runs(db: Session, user: User) -> list[tuple[Run, str]]:
    rows = (
        db.query(Run, Agent.name)
        .join(Thread, Run.thread_id == Thread.id)
        .join(Agent, Thread.agent_id == Agent.id)
        .filter(Thread.user_id == user.id)
        .order_by(Run.id.desc())
        .all()
    )
    return [(run, name) for run, name in rows]


def percentile(values: list[int], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    rank = (len(ordered) - 1) * fraction
    low = math.floor(rank)
    high = math.ceil(rank)
    if low == high:
        return float(ordered[low])
    weight = rank - low
    return ordered[low] * (1 - weight) + ordered[high] * weight


def summary(db: Session, user: User) -> dict:
    rows = _user_runs(db, user)
    runs = [run for run, _name in rows]
    completed = [run for run in runs if run.status == "completed"]
    failed = [run for run in runs if run.status == "failed"]
    latencies = [int(run.latency_ms or 0) for run in completed]
    total = len(runs)
    success_count = len(completed)
    return {
        "run_count": total,
        "success_count": success_count,
        "error_count": len(failed),
        "success_rate": round(success_count / total, 4) if total else 0,
        "p50_latency_ms": round(percentile(latencies, 0.50), 2),
        "p95_latency_ms": round(percentile(latencies, 0.95), 2),
    }


def recent_runs(db: Session, user: User) -> list[dict]:
    rows = _user_runs(db, user)[:50]
    return [
        {
            "id": run.id,
            "thread_id": run.thread_id,
            "agent_name": name,
            "status": run.status,
            "latency_ms": run.latency_ms,
            "step_count": run.step_count,
            "estimated_tokens": run.estimated_tokens,
            "error": run.error,
            "created_at": iso(run.created_at),
        }
        for run, name in rows
    ]
