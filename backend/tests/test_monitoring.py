def test_monitoring_counts_a_completed_run(client, auth_headers):
    before = client.get("/monitoring/summary", headers=auth_headers)
    assert before.status_code == 200, before.text
    agents = client.get("/agents", headers=auth_headers).json()
    agent_id = next(item["id"] for item in agents if item["slug"] == "calculator-tutor")
    thread = client.post(
        f"/agents/{agent_id}/threads",
        headers=auth_headers,
        json={"title": "monitor"},
    )
    assert thread.status_code == 201, thread.text
    thread_id = thread.json()["id"]
    run = client.post(
        f"/threads/{thread_id}/runs",
        headers=auth_headers,
        json={"message": "What is 100 / 4?"},
    )
    assert run.status_code == 200, run.text

    summary = client.get("/monitoring/summary", headers=auth_headers)
    assert summary.status_code == 200
    body = summary.json()
    assert body["run_count"] == before.json()["run_count"] + 1
    assert body["success_count"] >= before.json()["success_count"] + 1
    assert 0 <= body["success_rate"] <= 1
    assert "p50_latency_ms" in body
    assert "p95_latency_ms" in body

    runs = client.get("/monitoring/runs", headers=auth_headers)
    assert runs.status_code == 200
    mine = [item for item in runs.json() if item["thread_id"] == thread_id]
    assert mine
    assert mine[0]["status"] == "completed"
    assert mine[0]["error"] is None
