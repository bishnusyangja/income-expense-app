import pytest
from sqlalchemy.orm import sessionmaker

from tests.helpers import (
    REGISTER_URL,
    assert_error_detail,
    assert_status,
    assert_validation_error,
    max_length_message,
    min_length_message,
)
from user.dbmodels import User

REQUIRED_FIELDS = ["first_name", "last_name", "email", "address", "phone", "password"]
RESPONSE_FIELDS = [
    "id",
    "username",
    "first_name",
    "last_name",
    "email",
    "address",
    "phone",
    "created_at",
]


class TestRegisterSuccess:
    def test_register_returns_201_and_user_body(self, client, valid_payload):
        response = client.post(REGISTER_URL, json=valid_payload)

        assert_status(response, 201)
        body = response.json()
        for field in RESPONSE_FIELDS:
            assert field in body, f"Missing field {field!r} in {body}"

        assert body["id"] >= 1
        assert body["first_name"] == valid_payload["first_name"]
        assert body["last_name"] == valid_payload["last_name"]
        assert body["email"] == valid_payload["email"]
        assert body["username"] == valid_payload["email"]
        assert body["address"] == valid_payload["address"]
        assert body["phone"] == valid_payload["phone"]
        assert body["created_at"]

    def test_register_does_not_return_password_fields(self, client, valid_payload):
        response = client.post(REGISTER_URL, json=valid_payload)

        assert_status(response, 201)
        body = response.json()
        assert "password" not in body
        assert "hashed_password" not in body

    def test_register_stores_hashed_password(self, client, db_engine, valid_payload):
        response = client.post(REGISTER_URL, json=valid_payload)
        assert_status(response, 201)

        session = sessionmaker(bind=db_engine, autocommit=False, autoflush=False)()
        try:
            user = session.query(User).one()
            assert user.hashed_password != valid_payload["password"]
            assert user.hashed_password.startswith("$2")
            assert user.username == valid_payload["email"]
            assert user.email == valid_payload["email"]
        finally:
            session.close()

    def test_register_lowercases_email_and_username(self, client, valid_payload):
        valid_payload["email"] = "Jane.Doe@Example.COM"
        response = client.post(REGISTER_URL, json=valid_payload)

        assert_status(response, 201)
        body = response.json()
        assert body["email"] == "jane.doe@example.com"
        assert body["username"] == "jane.doe@example.com"

    def test_register_accepts_plus_addressed_email(self, client, valid_payload):
        valid_payload["email"] = "jane+tag@example.com"
        response = client.post(REGISTER_URL, json=valid_payload)

        assert_status(response, 201)
        assert response.json()["email"] == "jane+tag@example.com"

    def test_register_strips_whitespace_around_email(self, client, valid_payload):
        valid_payload["email"] = "  jane@example.com  "
        response = client.post(REGISTER_URL, json=valid_payload)

        assert_status(response, 201)
        assert response.json()["email"] == "jane@example.com"

    def test_register_accepts_min_length_fields(self, client):
        payload = {
            "first_name": "J",
            "last_name": "D",
            "email": "min@example.com",
            "address": "x",
            "phone": "1234567",
            "password": "12345678",
        }
        response = client.post(REGISTER_URL, json=payload)

        assert_status(response, 201)
        body = response.json()
        assert body["first_name"] == "J"
        assert body["last_name"] == "D"
        assert body["address"] == "x"
        assert body["phone"] == "1234567"

    def test_register_accepts_max_length_fields(self, client):
        payload = {
            "first_name": "a" * 100,
            "last_name": "b" * 100,
            "email": "max@example.com",
            "address": "c" * 500,
            "phone": "1" * 32,
            # bcrypt rejects secrets longer than 72 bytes
            "password": "p" * 72,
        }
        response = client.post(REGISTER_URL, json=payload)

        assert_status(response, 201)
        body = response.json()
        assert body["first_name"] == payload["first_name"]
        assert body["last_name"] == payload["last_name"]
        assert body["address"] == payload["address"]
        assert body["phone"] == payload["phone"]

    def test_register_ignores_unknown_fields(self, client, valid_payload):
        valid_payload["role"] = "admin"
        response = client.post(REGISTER_URL, json=valid_payload)

        assert_status(response, 201)
        assert "role" not in response.json()

    def test_register_second_unique_email_succeeds(self, client, valid_payload):
        first = client.post(REGISTER_URL, json=valid_payload)
        assert_status(first, 201)

        valid_payload["email"] = "john@example.com"
        second = client.post(REGISTER_URL, json=valid_payload)

        assert_status(second, 201)
        assert second.json()["email"] == "john@example.com"
        assert second.json()["id"] != first.json()["id"]


class TestRegisterConflict:
    def test_duplicate_email_returns_409(self, client, valid_payload):
        first = client.post(REGISTER_URL, json=valid_payload)
        assert_status(first, 201)

        duplicate = client.post(REGISTER_URL, json=valid_payload)

        assert_error_detail(duplicate, 409, "Email is already registered")

    def test_duplicate_email_different_case_returns_409(self, client, valid_payload):
        first = client.post(REGISTER_URL, json=valid_payload)
        assert_status(first, 201)

        valid_payload["email"] = "Jane@Example.com"
        duplicate = client.post(REGISTER_URL, json=valid_payload)

        assert_error_detail(duplicate, 409, "Email is already registered")

    def test_duplicate_email_with_other_fields_changed_returns_409(
        self, client, valid_payload
    ):
        first = client.post(REGISTER_URL, json=valid_payload)
        assert_status(first, 201)

        valid_payload.update(
            {
                "first_name": "John",
                "last_name": "Smith",
                "address": "456 Other St",
                "phone": "9998887777",
                "password": "anotherpass",
            }
        )
        duplicate = client.post(REGISTER_URL, json=valid_payload)

        assert_error_detail(duplicate, 409, "Email is already registered")


class TestRegisterMissingFields:
    @pytest.mark.parametrize("field", REQUIRED_FIELDS)
    def test_missing_required_field_returns_422(self, client, valid_payload, field):
        del valid_payload[field]
        response = client.post(REGISTER_URL, json=valid_payload)

        assert_validation_error(response, field, "Field required")

    def test_empty_object_reports_all_required_fields(self, client):
        response = client.post(REGISTER_URL, json={})

        assert_status(response, 422)
        detail = response.json()["detail"]
        missing_fields = {error["loc"][-1] for error in detail}
        assert missing_fields == set(REQUIRED_FIELDS)
        assert all(error["msg"] == "Field required" for error in detail)

    def test_missing_body_returns_422(self, client):
        response = client.post(REGISTER_URL)

        assert_status(response, 422)
        detail = response.json()["detail"]
        assert isinstance(detail, list)
        assert any("Field required" in error.get("msg", "") for error in detail)


class TestRegisterInvalidValues:
    @pytest.mark.parametrize(
        ("field", "min_length"),
        [
            ("first_name", 1),
            ("last_name", 1),
            ("address", 1),
            ("phone", 7),
            ("password", 8),
        ],
    )
    def test_empty_string_returns_422(self, client, valid_payload, field, min_length):
        valid_payload[field] = ""
        response = client.post(REGISTER_URL, json=valid_payload)

        assert_validation_error(response, field, min_length_message(min_length))

    @pytest.mark.parametrize(
        ("field", "value", "min_length"),
        [
            ("phone", "123456", 7),
            ("password", "1234567", 8),
        ],
    )
    def test_value_shorter_than_min_returns_422(
        self, client, valid_payload, field, value, min_length
    ):
        valid_payload[field] = value
        response = client.post(REGISTER_URL, json=valid_payload)

        assert_validation_error(response, field, min_length_message(min_length))

    @pytest.mark.parametrize(
        ("field", "value", "max_length"),
        [
            ("first_name", "a" * 101, 100),
            ("last_name", "b" * 101, 100),
            ("address", "c" * 501, 500),
            ("phone", "1" * 33, 32),
            ("password", "p" * 129, 128),
        ],
    )
    def test_value_longer_than_max_returns_422(
        self, client, valid_payload, field, value, max_length
    ):
        valid_payload[field] = value
        response = client.post(REGISTER_URL, json=valid_payload)

        assert_validation_error(response, field, max_length_message(max_length))

    @pytest.mark.parametrize(
        "email",
        [
            "not-an-email",
            "missing-at.example.com",
            "user@",
            "@example.com",
            "user@example",
            "jane example@example.com",
        ],
    )
    def test_invalid_email_returns_422(self, client, valid_payload, email):
        valid_payload["email"] = email
        response = client.post(REGISTER_URL, json=valid_payload)

        assert_validation_error(response, "email", "value is not a valid email address")

    @pytest.mark.parametrize("field", REQUIRED_FIELDS)
    def test_null_field_returns_422(self, client, valid_payload, field):
        valid_payload[field] = None
        response = client.post(REGISTER_URL, json=valid_payload)

        assert_status(response, 422)
        assert_validation_error(response, field, "Input should be a valid string")

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("first_name", 123),
            ("last_name", ["Doe"]),
            ("email", 123),
            ("address", {"street": "Main"}),
            ("phone", 5551234567),
            ("password", True),
        ],
    )
    def test_wrong_type_returns_422(self, client, valid_payload, field, value):
        valid_payload[field] = value
        response = client.post(REGISTER_URL, json=valid_payload)

        assert_status(response, 422)
        detail = response.json()["detail"]
        assert any(field in error.get("loc", []) for error in detail)


class TestRegisterMalformedRequest:
    def test_invalid_json_returns_422(self, client):
        response = client.post(
            REGISTER_URL,
            content="{not json",
            headers={"Content-Type": "application/json"},
        )

        assert_status(response, 422)
        body = response.json()
        detail = body["detail"]
        if isinstance(detail, str):
            assert "json" in detail.lower()
        else:
            messages = [error.get("msg", "") for error in detail]
            assert any("JSON decode error" in msg for msg in messages)

    def test_json_array_body_returns_422(self, client):
        response = client.post(REGISTER_URL, json=[])

        assert_status(response, 422)
        detail = response.json()["detail"]
        assert isinstance(detail, list)
        assert any("Input should be a valid dictionary" in error.get("msg", "") for error in detail)

    def test_form_encoded_body_returns_422(self, client, valid_payload):
        response = client.post(REGISTER_URL, data=valid_payload)

        assert_status(response, 422)

    @pytest.mark.parametrize("method", ["get", "put", "patch", "delete"])
    def test_unsupported_method_returns_405(self, client, method):
        response = getattr(client, method)(REGISTER_URL)

        assert_error_detail(response, 405, "Method Not Allowed")
