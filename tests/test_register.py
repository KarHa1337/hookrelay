def test_register_returns_api_key(client):
    response = client.post("/register")
    assert response.status_code == 200
    body = response.json()
    assert "api_key" in body
    assert len(body["api_key"]) > 20


def test_each_registration_gives_a_different_key(client):
    key_a = client.post("/register").json()["api_key"]
    key_b = client.post("/register").json()["api_key"]
    assert key_a != key_b
