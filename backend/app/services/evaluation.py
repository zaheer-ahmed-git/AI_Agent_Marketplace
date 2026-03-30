import time

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import TestCase, TestRun, TestSuite, Thread, User
from app.services.agents import get_owned_agent, latest_version
from app.services.runs import run_agent


def list_tests(db: Session, user: User, agent_id: int) -> dict:
    agent = get_owned_agent(db, user, agent_id)
    suites = db.query(TestSuite).filter(TestSuite.agent_id == agent.id).order_by(TestSuite.id.asc()).all()
    payload = []
    for suite in suites:
        cases = db.query(TestCase).filter(TestCase.suite_id == suite.id).order_by(TestCase.id.asc()).all()
        case_rows = []
        for case in cases:
            last = (
                db.query(TestRun)
                .filter(TestRun.case_id == case.id)
                .order_by(TestRun.id.desc())
                .first()
            )
            case_rows.append(
                {
                    "id": case.id,
                    "name": case.name,
                    "input_text": case.input_text,
                    "expected_tool": case.expected_tool,
                    "expected_phrase": case.expected_phrase,
                    "last_passed": None if last is None else bool(last.passed),
                    "last_detail": None if last is None else last.detail,
                }
            )
        payload.append({"id": suite.id, "name": suite.name, "cases": case_rows})
    return {"suites": payload}


def _tool_names(events: list[dict]) -> set[str]:
    found: set[str] = set()
    for event in events:
        if event.get("event") != "node":
            continue
        data = event.get("data") or {}
        for call in data.get("tool_calls") or []:
            if call.get("name"):
                found.add(call["name"])
        for tool in data.get("tools") or []:
            if tool.get("name"):
                found.add(tool["name"])
    return found


def run_suite(db: Session, user: User, agent_id: int) -> dict:
    agent = get_owned_agent(db, user, agent_id)
    suite = db.query(TestSuite).filter(TestSuite.agent_id == agent.id).order_by(TestSuite.id.asc()).first()
    if suite is None:
        raise HTTPException(status_code=404, detail="No test suite")
    version = latest_version(db, agent)
    cases = db.query(TestCase).filter(TestCase.suite_id == suite.id).order_by(TestCase.id.asc()).all()
    results = []
    for case in cases:
        thread = Thread(
            agent_id=agent.id,
            user_id=user.id,
            version_id=version.id,
            title=f"test:{case.id}",
        )
        db.add(thread)
        db.commit()
        db.refresh(thread)
        started = time.perf_counter()
        events = list(run_agent(db, user, thread, case.input_text))
        latency_ms = int((time.perf_counter() - started) * 1000)
        text = "".join(
            event["data"].get("text", "")
            for event in events
            if event.get("event") == "token"
        )
        reasons = []
        if case.expected_tool and case.expected_tool not in _tool_names(events):
            reasons.append(f"missing tool {case.expected_tool}")
        if case.expected_phrase and case.expected_phrase.lower() not in text.lower():
            reasons.append(f"missing phrase {case.expected_phrase}")
        passed = not reasons
        detail = "passed" if passed else "; ".join(reasons)
        db.add(
            TestRun(
                suite_id=suite.id,
                case_id=case.id,
                passed=passed,
                latency_ms=latency_ms,
                detail=detail,
            )
        )
        db.commit()
        results.append(
            {
                "case_id": case.id,
                "name": case.name,
                "passed": passed,
                "latency_ms": latency_ms,
                "detail": detail,
            }
        )
    return {
        "suite_id": suite.id,
        "total": len(results),
        "passed": sum(1 for result in results if result["passed"]),
        "results": results,
    }
