from decimal import Decimal

import pytest

from tests.helpers import (
    INCOMES_URL,
    assert_api_error,
    assert_envelope,
    assert_validation_error,
)


def _income_payload(title="Salary", amount="100.00", note="Monthly pay") -> dict:
    return {"title": title, "amount": amount, "note": note}


class TestAddIncome:
    def test_add_income_returns_201(self, auth_client):
        response = auth_client.post(INCOMES_URL, json=_income_payload())

        body = assert_envelope(response, 201)
        assert body["message"] == "Income added successfully"
        data = body["data"]
        assert data["title"] == "Salary"
        assert Decimal(data["amount"]) == Decimal("100.00")
        assert Decimal(data["remaining"]) == Decimal("100.00")
        assert data["note"] == "Monthly pay"
        assert data["user_id"] == 1
        assert data["id"] >= 1

    def test_remaining_starts_equal_to_amount(self, auth_client):
        data = assert_envelope(
            auth_client.post(INCOMES_URL, json=_income_payload(amount="250.50")),
            201,
        )["data"]
        assert Decimal(data["amount"]) == Decimal(data["remaining"]) == Decimal("250.50")

    def test_list_incomes_returns_current_user_items(self, auth_client):
        auth_client.post(INCOMES_URL, json=_income_payload(title="Job"))
        auth_client.post(INCOMES_URL, json=_income_payload(title="Freelance"))
        response = auth_client.get(INCOMES_URL)

        body = assert_envelope(response, 200)
        titles = [item["title"] for item in body["data"]]
        assert titles == ["Freelance", "Job"]

    def test_add_income_requires_auth(self, client):
        response = client.post(INCOMES_URL, json=_income_payload())
        assert_api_error(
            response,
            401,
            errors={"token": "Authentication required"},
            message="Unauthorized",
        )

    def test_add_income_rejects_invalid_token(self, client):
        client.headers["Authorization"] = "Bearer not-a-real-token"
        response = client.post(INCOMES_URL, json=_income_payload())
        assert_api_error(response, 401, errors={"token": "Invalid token"})

    def test_add_income_without_csrf_returns_403(self, bare_client):
        response = bare_client.post(INCOMES_URL, json=_income_payload())
        assert_api_error(response, 403, errors={"csrf": "CSRF token missing"})


class TestIncomeValidation:
    @pytest.mark.parametrize("field", ["title", "amount"])
    def test_missing_required_field_returns_422(self, auth_client, field):
        payload = _income_payload()
        del payload[field]
        response = auth_client.post(INCOMES_URL, json=payload)
        assert_validation_error(response, field, "This field is required")

    def test_blank_title_returns_422(self, auth_client):
        response = auth_client.post(INCOMES_URL, json=_income_payload(title="   "))
        assert_validation_error(response, "title", "This field cannot be blank")

    def test_zero_amount_returns_422(self, auth_client):
        response = auth_client.post(INCOMES_URL, json=_income_payload(amount="0"))
        assert_envelope(response, 422)
        assert "amount" in response.json()["errors"] or "non_field" in response.json()["errors"]

    def test_negative_amount_returns_422(self, auth_client):
        response = auth_client.post(INCOMES_URL, json=_income_payload(amount="-10"))
        assert_envelope(response, 422)
