from app.database import SessionLocal
from app.models import Run, RunEvent


def _agent_id(client, auth_headers, slug: str) -> int:
    agents = client.get("/agents", headers=auth_headers)
    assert agents.status_code == 200
    match = next(item for item in agents.json() if item["slug"] == slug)
    return match["id"]


def test_calculator_run_records_tool_and_completion(client, auth_headers):
    agent_id = _agent_id(client, auth_headers, "calculator-tutor")
    thread = client.post(f"/agents/{agent_id}/threads", headers=auth_headers, json={"title": "math"})
    assert thread.status_code == 201, thread.text
    thread_id = thread.json()["id"]

    response = client.post(
        f"/threads/{thread_id}/runs",
        headers=auth_headers,
        json={"message": "What is 12 * 7?"},
    )
    assert response.status_code == 200, response.text
    assert "calculator" in response.text
    assert "completed" in response.text

    db = SessionLocal()
    try:
        run = db.query(Run).filter(Run.thread_id == thread_id).one()
        assert run.status == "completed"
        assert "84" in (run.assistant_message or "")
        events = db.query(RunEvent).filter(RunEvent.run_id == run.id).all()
        assert any(event.node_name == "tools" and "calculator" in event.payload for event in events)
    finally:
        db.close()
