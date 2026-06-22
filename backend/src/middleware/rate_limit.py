"""
Rate Limiting middleware — backed by Redis (shared.core.redis).

Usage in endpoints:
    from backend.src.middleware.rate_limit import limiter
    @limiter.limit("15/minute")
    async def my_endpoint(request: Request, ...):
"""

import os
from slowapi import Limiter
from slowapi.util import get_remote_address

_REDIS_URL_ENV = os.getenv("REDIS_URL")
if _REDIS_URL_ENV:
    _REDIS_URL = _REDIS_URL_ENV
else:
    _REDIS_HOST = os.getenv("REDIS_HOST", "redis")
    _REDIS_PORT = os.getenv("REDIS_PORT", "6379")
    if str(_REDIS_PORT).startswith("tcp://"):
        _REDIS_PORT = _REDIS_PORT.split(":")[-1]
    _REDIS_URL = f"redis://{_REDIS_HOST}:{_REDIS_PORT}/1"

# ─── Limiter singleton ───────────────────────────────────────────────────────
# get_remote_address extracts the real client IP from X-Forwarded-For header
# (set by Nginx: proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for)
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=_REDIS_URL,
    default_limits=[],           # No global default — limits are per-endpoint
    headers_enabled=False,       # Tắt để tránh lỗi cần inject Response param
)
