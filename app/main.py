from fastapi import FastAPI, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session

from app.db import engine, get_db, Base
from app import models, schemas, security, discord, ratelimit
from app.config import MAX_PAYLOAD_BYTES

Base.metadata.create_all(bind=engine)

app = FastAPI(title="HookRelay API", version="0.1.0")


def get_current_api_key(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> models.ApiKey:
    key_hash = security.hash_api_key(x_api_key)
    api_key = db.query(models.ApiKey).filter(models.ApiKey.key_hash == key_hash).first()
    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key


@app.get("/")
def root():
    return {"status": "ok"}


@app.post("/register", response_model=schemas.ApiKeyOut)
def register(db: Session = Depends(get_db)):
    """Hands out a fresh API key. No signup form, no email - just gives you a
    random key. Shown once, same as e.g. a GitHub personal access token."""
    raw_key = security.generate_api_key()
    api_key = models.ApiKey(key_hash=security.hash_api_key(raw_key))
    db.add(api_key)
    db.commit()
    return {"api_key": raw_key}


@app.post("/relays", response_model=schemas.RelayOut)
def create_relay(
    body: schemas.RelayCreate,
    request: Request,
    api_key: models.ApiKey = Depends(get_current_api_key),
    db: Session = Depends(get_db),
):
    relay = models.Relay(
        api_key_id=api_key.id,
        label=body.label,
        discord_webhook_url=str(body.discord_webhook_url),
        secret=body.secret,
    )
    db.add(relay)
    db.commit()
    db.refresh(relay)

    return {
        "id": relay.id,
        "label": relay.label,
        "post_url": str(request.base_url) + f"relay/{relay.id}",
        "event_count": relay.event_count,
    }


@app.get("/relays", response_model=list[schemas.RelayOut])
def list_relays(
    request: Request,
    api_key: models.ApiKey = Depends(get_current_api_key),
    db: Session = Depends(get_db),
):
    relays = db.query(models.Relay).filter(models.Relay.api_key_id == api_key.id).all()
    return [
        {
            "id": r.id,
            "label": r.label,
            "post_url": str(request.base_url) + f"relay/{r.id}",
            "event_count": r.event_count,
        }
        for r in relays
    ]


@app.delete("/relays/{relay_id}")
def delete_relay(
    relay_id: str,
    api_key: models.ApiKey = Depends(get_current_api_key),
    db: Session = Depends(get_db),
):
    relay = (
        db.query(models.Relay)
        .filter(models.Relay.id == relay_id, models.Relay.api_key_id == api_key.id)
        .first()
    )
    if not relay:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(relay)
    db.commit()
    return {"deleted": relay_id}


@app.post("/relay/{relay_id}")
async def receive_event(relay_id: str, request: Request, db: Session = Depends(get_db)):
    """Public endpoint - whatever external system you point at this URL lands here.
    No API key needed (the caller isn't you), but an optional per-relay secret
    can require a signed request instead."""
    relay = db.query(models.Relay).filter(models.Relay.id == relay_id).first()
    if not relay:
        raise HTTPException(status_code=404, detail="Not found")

    if ratelimit.is_rate_limited(relay_id):
        raise HTTPException(status_code=429, detail="Too many events, slow down")

    raw_body = await request.body()
    if len(raw_body) > MAX_PAYLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Payload too large")

    if relay.secret:
        signature = request.headers.get("X-Signature-256", "")
        if not security.verify_signature(relay.secret, raw_body, signature):
            raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        payload = await request.json()
        if not isinstance(payload, dict):
            payload = {"payload": payload}
    except Exception:
        payload = {"raw": raw_body.decode(errors="replace")}

    response = discord.send_to_discord(relay.discord_webhook_url, payload)
    if response.status_code >= 300:
        raise HTTPException(status_code=502, detail="Discord rejected the forwarded message")

    relay.event_count += 1
    db.commit()

    return {"forwarded": True}
