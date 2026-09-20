def _get_api_key(client):
    return client.post("/register").json()["api_key"]


def test_create_relay_requires_auth(client):
    response = client.post(
        "/relays", json={"discord_webhook_url": "https://discord.com/api/webhooks/x/y"}
    )
    assert response.status_code in (401, 422)


def test_create_relay_success(client):
    api_key = _get_api_key(client)
    response = client.post(
        "/relays",
        json={"discord_webhook_url": "https://discord.com/api/webhooks/x/y", "label": "test"},
        headers={"X-API-Key": api_key},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["label"] == "test"
    assert body["post_url"].endswith(f"/relay/{body['id']}")


def test_list_relays_only_shows_your_own(client):
    key_a = _get_api_key(client)
    key_b = _get_api_key(client)

    client.post(
        "/relays",
        json={"discord_webhook_url": "https://discord.com/api/webhooks/x/y"},
        headers={"X-API-Key": key_a},
    )

    response = client.get("/relays", headers={"X-API-Key": key_b})
    assert response.status_code == 200
    assert response.json() == []


def test_delete_relay(client):
    api_key = _get_api_key(client)
    created = client.post(
        "/relays",
        json={"discord_webhook_url": "https://discord.com/api/webhooks/x/y"},
        headers={"X-API-Key": api_key},
    ).json()

    response = client.delete(f"/relays/{created['id']}", headers={"X-API-Key": api_key})
    assert response.status_code == 200

    response = client.get("/relays", headers={"X-API-Key": api_key})
    assert response.json() == []
