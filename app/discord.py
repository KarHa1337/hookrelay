from datetime import datetime, timezone

import httpx


def build_embed(payload: dict) -> dict:
    """Turns an arbitrary JSON payload into a Discord embed - dumps top-level
    keys as fields, since we don't know the shape of whatever gets sent in."""
    title = str(payload.get("title") or payload.get("event") or "New event")

    fields = []
    for key, value in payload.items():
        if key in ("title", "event"):
            continue
        text = str(value)
        if len(text) > 1000:
            text = text[:1000] + "..."
        fields.append({"name": str(key)[:256], "value": text or "-", "inline": len(text) < 40})
        if len(fields) >= 24:  # Discord caps embeds at 25 fields
            break

    return {
        "title": title[:256],
        "fields": fields,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def send_to_discord(webhook_url: str, payload: dict) -> httpx.Response:
    embed = build_embed(payload)
    return httpx.post(webhook_url, json={"embeds": [embed]}, timeout=10)
