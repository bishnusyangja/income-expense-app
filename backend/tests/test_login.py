from base64 import urlsafe_b64encode
from datetime import datetime, timedelta, timezone
import json

import jwt
import pytest

from app.auth import JWT_ALGORITHM, JWT_EXPIRE_DAYS, JWT_SECRET, decode_access_token
from tests.helpers import (
    CSRF_HEADER_NAME,
    CSRF_URL,
    LOGIN_URL,
    REGISTER_URL,
    assert_api_error,
    assert_envelope,
    assert_validation_error,
)


def _login_payload(email="jane@example.com", password="secret123") -> dict:
    return {"email": email, "password": password}


def _login(client, **overrides) -> dict:
    response = client.post(LOGIN_URL, json=_login_payload(**overrides))
    return assert_envelope(response, 200)["data"]


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


    def test_login_strips_whitespace_around_email(self, client, registered_user):
        data = _login(client, email="  jane@example.com  ")
        assert data["user"]["email"] == "jane@example.com"

    def test_login_user_matches_registered_profile(self, client, registered_user):
        data = _login(client)
        user = data["user"]
        assert user["first_name"] == registered_user["first_name"]
        assert user["last_name"] == registered_user["last_name"]
        assert user["address"] == registered_user["address"]
        assert user["phone"] == registered_user["phone"]
        assert user["id"] >= 1


class TestLoginJwt:
    def test_access_token_is_three_part_jwt(self, client, registered_user):
        token = _login(client)["access_token"]
        assert len(token.split(".")) == 3

    def test_token_uses_hs256(self, client, registered_user):
        token = _login(client)["access_token"]
        header = jwt.get_unverified_header(token)
        assert header["alg"] == JWT_ALGORITHM

    def test_token_claims_include_sub_email_iat_exp(self, client, registered_user):
        data = _login(client)
        payload = decode_access_token(data["access_token"])
        assert set(payload) >= {"sub", "email", "iat", "exp"}
        assert payload["sub"] == str(data["user"]["id"])
        assert payload["email"] == registered_user["email"]

    def test_token_expiry_claim_is_30_days(self, client, registered_user):
        payload = decode_access_token(_login(client)["access_token"])
        issued_at = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
        expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        assert JWT_EXPIRE_DAYS == 30
        assert expires_at - issued_at == timedelta(days=30)

    def test_response_expires_at_matches_jwt_exp(self, client, registered_user):
        data = _login(client)
        payload = decode_access_token(data["access_token"])
        response_expiry = datetime.fromisoformat(data["expires_at"])
        jwt_expiry = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        assert abs((response_expiry - jwt_expiry).total_seconds()) < 1

    def test_decode_access_token_accepts_login_token(self, client, registered_user):
        token = _login(client)["access_token"]
        payload = decode_access_token(token)
        assert payload["email"] == registered_user["email"]

    def test_token_rejected_with_wrong_secret(self, client, registered_user):
        token = _login(client)["access_token"]
        with pytest.raises(jwt.InvalidSignatureError):
            jwt.decode(token, "wrong-secret", algorithms=[JWT_ALGORITHM])

    def test_tampered_token_is_rejected(self, client, registered_user):
        token = _login(client)["access_token"]
        header, payload, signature = token.split(".")
        tampered_payload = payload[:-1] + ("A" if payload[-1] != "A" else "B")
        tampered = ".".join([header, tampered_payload, signature])
        with pytest.raises(jwt.InvalidSignatureError):
            decode_access_token(tampered)

    def test_expired_token_is_rejected(self):
        expired = jwt.encode(
            {
                "sub": "1",
                "email": "jane@example.com",
                "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
            },
            JWT_SECRET,
            algorithm=JWT_ALGORITHM,
        )
        with pytest.raises(jwt.ExpiredSignatureError):
            decode_access_token(expired)

    def test_unsigned_alg_none_token_is_rejected(self, client, registered_user):
        payload = decode_access_token(_login(client)["access_token"])
        header = urlsafe_b64encode(b'{"alg":"none","typ":"JWT"}').rstrip(b"=").decode()
        body = (
            urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode())
            .rstrip(b"=")
            .decode()
        )
        none_token = f"{header}.{body}."
        with pytest.raises((jwt.InvalidAlgorithmError, jwt.DecodeError, jwt.InvalidTokenError)):
            decode_access_token(none_token)

    def test_failed_login_does_not_return_a_token(self, client, registered_user):
        response = client.post(LOGIN_URL, json=_login_payload(password="wrongpass"))
        body = assert_api_error(
            response,
            401,
            errors={"email": "Invalid email or password"},
        )
        assert body["data"] is None

    def test_different_users_receive_different_token_subjects(
        self, client, valid_payload, registered_user
    ):
        first = _login(client)
        valid_payload["email"] = "john@example.com"
        assert_envelope(client.post(REGISTER_URL, json=valid_payload), 201)
        second = _login(client, email="john@example.com")

        first_claims = decode_access_token(first["access_token"])
        second_claims = decode_access_token(second["access_token"])
        assert first_claims["sub"] != second_claims["sub"]
        assert second_claims["email"] == "john@example.com"
        assert first["user"]["id"] != second["user"]["id"]


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

    @pytest.mark.parametrize("field", ["email", "password"])
    def test_null_field_returns_422(self, client, field):
        payload = _login_payload()
        payload[field] = None
        response = client.post(LOGIN_URL, json=payload)

        assert_validation_error(response, field, "This field must be a string")

    def test_empty_body_returns_422(self, client):
        response = client.post(LOGIN_URL, json={})
        body = assert_envelope(response, 422)
        assert body["errors"]["email"] == "This field is required"
        assert body["errors"]["password"] == "This field is required"

    def test_password_longer_than_max_returns_422(self, client):
        response = client.post(LOGIN_URL, json=_login_payload(password="p" * 73))
        assert_validation_error(response, "password", "Must be at most 72 characters")

    def test_login_ignores_unknown_fields(self, client, registered_user):
        payload = _login_payload()
        payload["role"] = "admin"
        data = assert_envelope(client.post(LOGIN_URL, json=payload), 200)["data"]
        assert "role" not in data
        assert data["access_token"]


class TestLoginCsrf:
    def test_login_without_csrf_returns_403(self, bare_client, valid_payload):
        response = bare_client.post(LOGIN_URL, json=_login_payload())

        assert_api_error(
            response,
            403,
            errors={"csrf": "CSRF token missing"},
        )

    def test_login_with_mismatched_csrf_returns_403(self, bare_client):
        bare_client.get(CSRF_URL)
        response = bare_client.post(
            LOGIN_URL,
            json=_login_payload(),
            headers={CSRF_HEADER_NAME: "not-the-real-token"},
        )
        assert_api_error(response, 403, errors={"csrf": "CSRF token invalid"})

    @pytest.mark.parametrize("method", ["get", "put", "patch", "delete"])
    def test_unsupported_method_returns_405(self, client, method):
        response = getattr(client, method)(LOGIN_URL)

        assert_api_error(
            response,
            405,
            errors={"method": "Method not allowed"},
            message="Method not allowed",
        )
