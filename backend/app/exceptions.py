from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.responses import json_response, parse_validation_errors


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        return json_response(
            status_code=422,
            message="Validation failed",
            errors=parse_validation_errors(exc),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        errors = _http_errors(exc)
        return json_response(
            status_code=exc.status_code,
            message=_http_message(exc.status_code),
            errors=errors,
        )


def _http_message(status_code: int) -> str:
    messages = {
        404: "Not found",
        405: "Method not allowed",
        403: "Forbidden",
        401: "Unauthorized",
    }
    return messages.get(status_code, "Request failed")


def _http_errors(exc: StarletteHTTPException) -> dict[str, str]:
    if exc.status_code == 405:
        return {"method": "Method not allowed"}
    if exc.status_code == 404:
        return {"non_field": "Not found"}
    if isinstance(exc.detail, dict):
        return {str(key): str(value) for key, value in exc.detail.items()}
    return {"non_field": str(exc.detail)}
