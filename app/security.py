import hashlib
import hmac
import secrets


def generate_api_key() -> str:
    return secrets.token_urlsafe(32)


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def verify_signature(secret: str, payload_bytes: bytes, signature_header: str) -> bool:
    """Checks a `sha256=<hex>` HMAC signature header against the raw request body."""
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()
    provided = signature_header.split("=", 1)[1]
    return hmac.compare_digest(expected, provided)
