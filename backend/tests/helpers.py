REGISTER_URL = "/register"
CSRF_URL = "/csrf-token"
CSRF_HEADER_NAME = "X-CSRF-Token"
CSRF_COOKIE_NAME = "csrf_token"


def assert_status(response, expected_status: int) -> None:
    assert response.status_code == expected_status, (
        f"Expected status {expected_status}, got {response.status_code}: {response.text}"
    )


def assert_error_detail(response, expected_status: int, expected_detail: str) -> None:
    assert_status(response, expected_status)
    body = response.json()
    assert "detail" in body
    assert body["detail"] == expected_detail, (
        f"Expected detail {expected_detail!r}, got {body['detail']!r}"
    )


def assert_validation_error(response, field: str, message: str) -> None:
    assert_status(response, 422)
    body = response.json()
    assert "detail" in body
    detail = body["detail"]
    assert isinstance(detail, list), f"Expected list of errors, got {detail!r}"

    field_errors = [error for error in detail if field in error.get("loc", [])]
    assert field_errors, f"No validation error for {field!r} in {detail!r}"

    messages = [error.get("msg", "") for error in field_errors]
    assert any(message in msg for msg in messages), (
        f"Expected message containing {message!r} for {field}, got {messages}"
    )


def min_length_message(min_length: int) -> str:
    noun = "character" if min_length == 1 else "characters"
    return f"String should have at least {min_length} {noun}"


def max_length_message(max_length: int) -> str:
    noun = "character" if max_length == 1 else "characters"
    return f"String should have at most {max_length} {noun}"
