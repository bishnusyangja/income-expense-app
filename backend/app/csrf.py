import secrets

from fastapi import APIRouter, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.responses import json_response

CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"
UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

router = APIRouter(tags=["csrf"])


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def set_csrf_cookie(response: Response, token: str, *, secure: bool) -> None:
    response.set_cookie(
        CSRF_COOKIE_NAME,
        token,
        httponly=False,
        samesite="lax",
        secure=secure,
        path="/",
    )


def csrf_tokens_match(cookie_token: str, header_token: str) -> bool:
    return secrets.compare_digest(cookie_token, header_token)


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
        header_token = request.headers.get(CSRF_HEADER_NAME)

        if request.method in UNSAFE_METHODS:
            if not cookie_token or not header_token:
                return json_response(
                    status_code=403,
                    message="CSRF check failed",
                    errors={"csrf": "CSRF token missing"},
                )
            if not csrf_tokens_match(cookie_token, header_token):
                return json_response(
                    status_code=403,
                    message="CSRF check failed",
                    errors={"csrf": "CSRF token invalid"},
                )
            request.state.csrf_token = cookie_token
        else:
            request.state.csrf_token = cookie_token or generate_csrf_token()

        response = await call_next(request)
        if cookie_token is None:
            set_csrf_cookie(
                response,
                request.state.csrf_token,
                secure=request.url.scheme == "https",
            )
        return response


@router.get("/csrf-token")
def get_csrf_token(request: Request):
    return json_response(
        status_code=200,
        message="CSRF token generated",
        data={"csrf_token": request.state.csrf_token},
    )
