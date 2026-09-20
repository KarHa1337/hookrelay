# HookRelay

A small API that turns any webhook into a Discord message. You register, create a
"relay" pointing at a Discord webhook URL, and get back a POST endpoint - point
whatever system you have (CI, monitoring, Stripe, your own app) at that endpoint
and it forwards the event to Discord as a formatted embed.

Built as a second portfolio project, focused on things [PriceWatch](https://github.com/KarHa1337/pricewatch)
didn't cover: authentication, tests, CI, containerization, and an actual deployment.

## How it works

1. `POST /register` - no auth needed, gives you back an API key (store it, it's
   only shown once)
2. `POST /relays` (with an `X-API-Key` header) - give it a Discord webhook URL,
   get back a `post_url`
3. Point any system that can send a webhook at that `post_url`
4. Whatever JSON it sends shows up in Discord as an embed

Optionally set a `secret` when creating a relay - incoming requests then need a
valid `X-Signature-256: sha256=<hmac>` header (HMAC-SHA256 of the raw body using
your secret) or they get rejected. Useful since the relay endpoint itself is
public - anyone with the URL could otherwise post to your Discord.

## Setup

```bash
python -m venv venv
source venv/bin/activate  # windows: venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Interactive docs show up on `/docs` once it's running.

## Running tests

```bash
pytest
```

CI runs the same test suite on every push via GitHub Actions
(`.github/workflows/tests.yml`).

## Docker

```bash
docker build -t hookrelay .
docker run -p 8000:8000 hookrelay
```

## Live demo

<!-- TODO: link once deployed -->

## What's still missing / to do

- rate limiting is in-memory, per process - fine for a single instance, but it
  resets on restart and wouldn't be shared across multiple instances (would need
  something like Redis for that)
- no retry on failed Discord delivery - if Discord is down or rate-limits us, the
  event just gets dropped and the caller gets a 502
- message formatting is a generic "dump the fields" embed - per-relay templating
  (so you control exactly how it looks) would be a good follow-up
- API keys are single-tier - no per-key relay limits or usage stats yet
