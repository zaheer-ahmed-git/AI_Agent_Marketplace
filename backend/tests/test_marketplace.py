def test_install_copies_config(client, auth_headers):
    source = client.get("/marketplace/research-summarizer", headers=auth_headers)
    assert source.status_code == 200, source.text
    installed = client.post("/marketplace/research-summarizer/install", headers=auth_headers)
    assert installed.status_code == 201, installed.text
    body = installed.json()
    assert body["system_prompt"] == source.json()["system_prompt"]
    assert body["tool_names"] == source.json()["tool_names"]
    assert body["model"] == source.json()["model"]

    detail = client.get(f"/agents/{body['agent_id']}", headers=auth_headers)
    assert detail.status_code == 200
    assert detail.json()["status"] == "draft"
    assert detail.json()["versions"][0]["system_prompt"] == source.json()["system_prompt"]


def test_review_validation(client, auth_headers):
    invalid = client.post(
        "/marketplace/support-triage/reviews",
        headers=auth_headers,
        json={"rating": 9, "comment": "too high"},
    )
    assert invalid.status_code == 422

    empty = client.post(
        "/marketplace/support-triage/reviews",
        headers=auth_headers,
        json={"rating": 5, "comment": "x"},
    )
    assert empty.status_code == 422

    created = client.post(
        "/marketplace/support-triage/reviews",
        headers=auth_headers,
        json={"rating": 5, "comment": "Clear triage notes."},
    )
    assert created.status_code == 201, created.text
    assert created.json()["rating"] == 5

    duplicate = client.post(
        "/marketplace/support-triage/reviews",
        headers=auth_headers,
        json={"rating": 4, "comment": "Second try."},
    )
    assert duplicate.status_code == 409
