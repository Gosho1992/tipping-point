"""Request size limit and security headers (strict Content-Security-Policy)."""
from fastapi import Request
from fastapi.responses import JSONResponse

from . import config

CSP = "; ".join([
    "default-src 'self'",
    "script-src 'self'",
    "style-src 'self' https://fonts.googleapis.com",
    "font-src https://fonts.gstatic.com",
    "img-src 'self' data:",
    "connect-src 'self'",
    "base-uri 'none'",
    "form-action 'self'",
    "frame-ancestors 'none'",
])
HEADERS = {
    "Content-Security-Policy": CSP,
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
}


async def guard(request: Request, call_next):
    if request.method == "POST":
        try:
            size = int(request.headers.get("content-length", "0"))
        except ValueError:
            size = config.MAX_BODY_BYTES + 1
        if size > config.MAX_BODY_BYTES:
            return JSONResponse(status_code=413, content={"code": "too_large"})
    response = await call_next(request)
    for k, v in HEADERS.items():
        response.headers.setdefault(k, v)
    return response
