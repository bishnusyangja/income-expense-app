REGISTER_URL = "/register"
CSRF_URL = "/csrf-token"
CSRF_HEADER_NAME = "X-CSRF-Token"
CSRF_COOKIE_NAME = "csrf_token"


def assert_status(response, expected_status: int) -> None:
    assert response.status_code == expected_status, (
        f"Expected status {expected_status}, got {response.status_code}: {response.text}"
    )


def assert_envelope(response, expected_status: int) -> dict:
    assert_status(response, expected_status)
    body = response.json()
    assert body.get("status-code") == expected_status, (
        f"Expected status-code {expected_status}, got {body.get('status-code')!r}: {body}"
    )
    assert "message" in body
    assert "data" in body
    assert "errors" in body
    return body


def assert_api_error(
    response,
    expected_status: int,
    *,
    errors: dict[str, str],
    message: str | None = None,
) -> dict:
    body = assert_envelope(response, expected_status)
    assert body["data"] is None
    assert isinstance(body["errors"], dict)
    for field, expected_message in errors.items():
        assert field in body["errors"], f"Missing error for {field!r} in {body['errors']}"
        assert expected_message in body["errors"][field], (
            f"Expected {field} message {expected_message!r}, got {body['errors'][field]!r}"
        )
    if message is not None:
        assert body["message"] == message
    return body


def assert_validation_error(response, field: str, message: str) -> None:
    assert_api_error(response, 422, errors={field: message}, message="Validation failed")


def min_length_message(min_length: int) -> str:
    return f"Must be at least {min_length} characters"


def max_length_message(max_length: int) -> str:
    return f"Must be at most {max_length} characters"
