from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.auth import JWT_ALGORITHM, JWT_SECRET
from tests.helpers import (
    LOGIN_URL,
    assert_api_error,
    assert_envelope,
    assert_validation_error,
)


def _login_payload(email="jane@example.com", password="secret123") -> dict:
    return {"email": email, "password": password}


class TestLoginSuccess:
    def test_login_returns_200_and_jwt(self, client, registered_user):
        response = client.post(LOGIN_URL, json=_login_payload())

        body = assert_envelope(response, 200)
        assert body["message"] == "Login successful"
        assert body["errors"] is None
        data = body["data"]
        assert data["token_type"] == "bearer"
        assert data["access_token"]
        assert data["expires_at"]
        assert data["user"]["email"] == registered_user["email"]
        assert data["user"]["username"] == registered_user["email"]
        assert "password" not in data["user"]
        assert "hashed_password" not in data

    def test_login_token_expires_in_30_days(self, client, registered_user):
        response = client.post(LOGIN_URL, json=_login_payload())
        token = assert_envelope(response, 200)["data"]["access_token"]

        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        assert payload["sub"] == "1"
        assert payload["email"] == registered_user["email"]

        expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        remaining = expires_at - datetime.now(timezone.utc)
        assert timedelta(days=29, hours=23) < remaining <= timedelta(days=30, minutes=1)

    def test_login_accepts_email_with_different_case(self, client, registered_user):
        response = client.post(
            LOGIN_URL,
            json=_login_payload(email="Jane@Example.com"),
        )

        data = assert_envelope(response, 200)["data"]
        assert data["user"]["email"] == "jane@example.com"


class TestLoginUnauthorized:
    def test_wrong_password_returns_401(self, client, registered_user):
        response = client.post(
            LOGIN_URL,
            json=_login_payload(password="wrongpass"),
        )

        assert_api_error(
            response,
            401,
            errors={"email": "Invalid email or password"},
            message="Login failed",
        )

    def test_unknown_email_returns_401(self, client, registered_user):
        response = client.post(
            LOGIN_URL,
            json=_login_payload(email="missing@example.com"),
        )

        assert_api_error(
            response,
            401,
            errors={"email": "Invalid email or password"},
            message="Login failed",
        )

    def test_login_without_existing_user_returns_401(self, client):
        response = client.post(LOGIN_URL, json=_login_payload())

        assert_api_error(
            response,
            401,
            errors={"email": "Invalid email or password"},
        )


class TestLoginValidation:
    @pytest.mark.parametrize("field", ["email", "password"])
    def test_missing_field_returns_422(self, client, field):
        payload = _login_payload()
        del payload[field]
        response = client.post(LOGIN_URL, json=payload)

        assert_validation_error(response, field, "This field is required")

    def test_invalid_email_returns_422(self, client):
        response = client.post(LOGIN_URL, json=_login_payload(email="not-an-email"))

        assert_validation_error(response, "email", "Enter a valid email address")

    def test_empty_password_returns_422(self, client):
        response = client.post(LOGIN_URL, json=_login_payload(password=""))

        assert_validation_error(response, "password", "Must be at least 1 characters")


class TestLoginCsrf:
    def test_login_without_csrf_returns_403(self, bare_client, valid_payload):
        response = bare_client.post(LOGIN_URL, json=_login_payload())

        assert_api_error(
            response,
            403,
            errors={"csrf": "CSRF token missing"},
        )

    def test_get_login_returns_405(self, client):
        response = client.get(LOGIN_URL)

        assert_api_error(
            response,
            405,
            errors={"method": "Method not allowed"},
            message="Method not allowed",
        )
