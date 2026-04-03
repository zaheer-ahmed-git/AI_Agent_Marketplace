def test_create_version_and_publish(client, auth_headers):
    created = client.post(
        "/agents",
        headers=auth_headers,
        json={
            "name": "Field notes agent",
            "description": "Draft used by the publish test",
            "system_prompt": "First prompt",
            "model": "gpt-4o-mini",
            "temperature": 0.2,
            "max_steps": 4,
            "tool_names": ["notes"],
            "memory_enabled": True,
        },
    )
    assert created.status_code == 201, created.text
    agent_id = created.json()["id"]
    assert created.json()["versions"][0]["system_prompt"] == "First prompt"

    rejected = client.post(
        "/agents",
        headers=auth_headers,
        json={
            "name": "Bad tools",
            "description": "nope",
            "system_prompt": "nope",
            "model": "gpt-4o-mini",
            "temperature": 0.1,
            "max_steps": 2,
            "tool_names": ["python"],
            "memory_enabled": False,
        },
    )
    assert rejected.status_code == 422

    version = client.post(
        f"/agents/{agent_id}/versions",
        headers=auth_headers,
        json={
            "system_prompt": "Second prompt",
            "model": "gpt-4o-mini",
            "temperature": 0.4,
            "max_steps": 5,
            "tool_names": ["notes", "clock"],
            "memory_enabled": False,
        },
    )
    assert version.status_code == 201, version.text
    assert version.json()["version_number"] == 2

    detail = client.get(f"/agents/{agent_id}", headers=auth_headers)
    prompts = [item["system_prompt"] for item in detail.json()["versions"]]
    assert prompts == ["First prompt", "Second prompt"]

    published = client.post(
        f"/agents/{agent_id}/publish",
        headers=auth_headers,
        json={"category": "productivity", "tags": ["notes"], "slug": "field-notes-agent"},
    )
    assert published.status_code == 200, published.text
    assert published.json()["status"] == "published"
    assert published.json()["listing"]["slug"] == "field-notes-agent"

    catalog = client.get("/marketplace", headers=auth_headers)
    slugs = [item["slug"] for item in catalog.json()]
    assert "field-notes-agent" in slugs
