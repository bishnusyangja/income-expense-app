from typing import Any

from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field


class APIEnvelope(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    status_code: int = Field(alias="status-code")
    message: str
    data: Any = None
    errors: dict[str, str] | None = None


def json_response(
    *,
    status_code: int,
    message: str,
    data: Any = None,
    errors: dict[str, str] | None = None,
) -> JSONResponse:
    payload = APIEnvelope(
        status_code=status_code,
        message=message,
        data=data,
        errors=errors,
    )
    return JSONResponse(
        status_code=status_code,
        content=payload.model_dump(by_alias=True, mode="json"),
    )


def parse_validation_errors(exc) -> dict[str, str]:
    errors: dict[str, str] = {}
    for err in exc.errors():
        field = _error_field(err)
        if field in errors:
            continue
        errors[field] = _friendly_message(err)
    return errors


def _error_field(err: dict) -> str:
    loc = err.get("loc") or ()
    err_type = err.get("type", "")
    if err_type == "json_invalid":
        return "non_field"

    parts = [
        str(part)
        for part in loc
        if part not in {"body", "query", "path", "header", "cookie"}
        and not isinstance(part, int)
    ]
    if not parts:
        return "non_field"
    return parts[-1] if len(parts) == 1 else ".".join(parts)


def _friendly_message(err: dict) -> str:
    err_type = err.get("type", "")
    ctx = err.get("ctx") or {}
    loc = err.get("loc") or ()
    msg = err.get("msg") or "Invalid value"

    if loc == ("body",):
        if err_type == "missing":
            return "Request body is required"
        if err_type in {"dict_type", "list_type", "model_attributes_type", "mapping_type"}:
            return "Request body must be a JSON object"

    if err_type == "missing":
        return "This field is required"
    if err_type == "string_too_short":
        min_length = ctx.get("min_length")
        return f"Must be at least {min_length} characters"
    if err_type == "string_too_long":
        max_length = ctx.get("max_length")
        return f"Must be at most {max_length} characters"
    if err_type == "string_type":
        return "This field must be a string"
    if err_type in {"dict_type", "model_attributes_type", "mapping_type"}:
        return "Request body must be a JSON object"
    if err_type == "json_invalid":
        return "Invalid JSON in request body"
    if err_type == "string_pattern_mismatch":
        if _error_field(err) == "phone":
            return "Enter a valid phone number"
        return "Invalid format"
    if err_type == "bool_type":
        return "This field must be a boolean"
    if err_type in {"int_type", "float_type"}:
        return "This field must be a number"
    if err_type == "list_type":
        return "This field must be a list"
    if _error_field(err) == "email" and (
        "email" in err_type or "not a valid email" in msg.lower()
    ):
        return "Enter a valid email address"
    if msg.startswith("Value error, "):
        return msg.removeprefix("Value error, ")
    return msg
