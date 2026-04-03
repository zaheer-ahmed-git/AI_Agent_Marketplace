def test_login_and_me(client):
    anonymous = client.get("/auth/me")
    assert anonymous.status_code == 401

    rejected = client.post(
        "/auth/login",
        json={"email": "demo@example.com", "password": "wrong-password"},
    )
    assert rejected.status_code == 401

    accepted = client.post(
        "/auth/login",
        json={"email": "demo@example.com", "password": "demo-password"},
    )
    assert accepted.status_code == 200
    token = accepted.json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "demo@example.com"
    assert me.json()["display_name"] == "Demo User"
