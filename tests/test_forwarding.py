from app import discord as discord_module


class FakeResponse:
    def __init__(self, status_code=204):
        self.status_code = status_code


def _get_api_key(client):
    return client.post("/register").json()["api_key"]


def test_relay_forwards_event(client, monkeypatch):
    sent = {}

    def fake_send(webhook_url, payload):
        sent["url"] = webhook_url
        sent["payload"] = payload
        return FakeResponse(204)

    monkeypatch.setattr(discord_module, "send_to_discord", fake_send)

    api_key = _get_api_key(client)
    relay = client.post(
        "/relays",
        json={"discord_webhook_url": "https://discord.com/api/webhooks/x/y"},
        headers={"X-API-Key": api_key},
    ).json()

    response = client.post(f"/relay/{relay['id']}", json={"event": "deploy", "status": "success"})

    assert response.status_code == 200
    assert sent["url"] == "https://discord.com/api/webhooks/x/y"
    assert sent["payload"]["status"] == "success"


def test_relay_missing_returns_404(client):
    response = client.post("/relay/does-not-exist", json={"foo": "bar"})
    assert response.status_code == 404


def test_relay_rejects_bad_signature(client, monkeypatch):
    monkeypatch.setattr(discord_module, "send_to_discord", lambda *a, **k: FakeResponse(204))

    api_key = _get_api_key(client)
    relay = client.post(
        "/relays",
        json={"discord_webhook_url": "https://discord.com/api/webhooks/x/y", "secret": "topsecret"},
        headers={"X-API-Key": api_key},
    ).json()

    response = client.post(
        f"/relay/{relay['id']}",
        json={"event": "test"},
        headers={"X-Signature-256": "sha256=deadbeef"},
    )
    assert response.status_code == 401


def test_relay_accepts_valid_signature(client, monkeypatch):
    import hashlib
    import hmac
    import json

    monkeypatch.setattr(discord_module, "send_to_discord", lambda *a, **k: FakeResponse(204))

    api_key = _get_api_key(client)
    relay = client.post(
        "/relays",
        json={"discord_webhook_url": "https://discord.com/api/webhooks/x/y", "secret": "topsecret"},
        headers={"X-API-Key": api_key},
    ).json()

    body = json.dumps({"event": "test"}).encode()
    signature = "sha256=" + hmac.new(b"topsecret", body, hashlib.sha256).hexdigest()

    response = client.post(
        f"/relay/{relay['id']}",
        content=body,
        headers={"X-Signature-256": signature, "Content-Type": "application/json"},
    )
    assert response.status_code == 200


def test_relay_rate_limit(client, monkeypatch):
    from app import config

    monkeypatch.setattr(config, "RATE_LIMIT_PER_MINUTE", 2)
    monkeypatch.setattr(discord_module, "send_to_discord", lambda *a, **k: FakeResponse(204))

    api_key = _get_api_key(client)
    relay = client.post(
        "/relays",
        json={"discord_webhook_url": "https://discord.com/api/webhooks/x/y"},
        headers={"X-API-Key": api_key},
    ).json()

    for _ in range(2):
        response = client.post(f"/relay/{relay['id']}", json={"n": 1})
        assert response.status_code == 200

    response = client.post(f"/relay/{relay['id']}", json={"n": 1})
    assert response.status_code == 429
