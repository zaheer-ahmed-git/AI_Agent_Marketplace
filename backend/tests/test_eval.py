def test_seed_suites_pass_offline(client, auth_headers):
    agents = client.get("/agents", headers=auth_headers)
    assert agents.status_code == 200
    by_slug = {item["slug"]: item["id"] for item in agents.json()}
    for slug in ("research-summarizer", "support-triage", "meeting-notes", "calculator-tutor"):
        result = client.post(f"/agents/{by_slug[slug]}/tests/run", headers=auth_headers)
        assert result.status_code == 200, result.text
        body = result.json()
        assert body["total"] == 3
        assert body["passed"] == 3, body
