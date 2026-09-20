import time
from collections import defaultdict, deque

from app import config

# per relay_id sliding window - fine for a single process, resets on restart and
# doesn't share state across multiple instances (would need redis for that)
_hits: dict = defaultdict(deque)


def is_rate_limited(relay_id: str) -> bool:
    now = time.monotonic()
    window = _hits[relay_id]

    while window and now - window[0] > 60:
        window.popleft()

    if len(window) >= config.RATE_LIMIT_PER_MINUTE:
        return True

    window.append(now)
    return False
