from decimal import Decimal

import pytest

from tests.helpers import (
    EXPENDITURES_URL,
    INCOMES_URL,
    LOGIN_URL,
    REGISTER_URL,
    assert_api_error,
    assert_envelope,
    assert_validation_error,
)


def _add_income(client, amount="100.00", title="Salary") -> dict:
    response = client.post(
        INCOMES_URL,
        json={"title": title, "amount": amount, "note": "Pay"},
    )
    return assert_envelope(response, 201)["data"]


def _spend(client, income_id: int, amount="40.00", title="Groceries"):
    return client.post(
        EXPENDITURES_URL,
        json={"income_id": income_id, "title": title, "amount": amount, "note": "Food"},
    )


class TestAddExpenditure:
    def test_add_expenditure_deducts_from_income(self, auth_client):
        income = _add_income(auth_client, amount="100.00")
        response = _spend(auth_client, income["id"], amount="40.00")

        body = assert_envelope(response, 201)
        assert body["message"] == "Expenditure added successfully"
        data = body["data"]
        assert data["title"] == "Groceries"
        assert Decimal(data["amount"]) == Decimal("40.00")
        assert Decimal(data["income_remaining"]) == Decimal("60.00")
        assert data["income_id"] == income["id"]

        incomes = assert_envelope(auth_client.get(INCOMES_URL), 200)["data"]
        assert Decimal(incomes[0]["remaining"]) == Decimal("60.00")
        assert Decimal(incomes[0]["amount"]) == Decimal("100.00")

    def test_full_amount_can_be_spent(self, auth_client):
        income = _add_income(auth_client, amount="50.00")
        data = assert_envelope(_spend(auth_client, income["id"], amount="50.00"), 201)["data"]
        assert Decimal(data["income_remaining"]) == Decimal("0.00")

    def test_second_spend_uses_updated_remaining(self, auth_client):
        income = _add_income(auth_client, amount="100.00")
        _spend(auth_client, income["id"], amount="30.00")
        data = assert_envelope(_spend(auth_client, income["id"], amount="20.00"), 201)["data"]
        assert Decimal(data["income_remaining"]) == Decimal("50.00")

    def test_insufficient_remaining_returns_400(self, auth_client):
        income = _add_income(auth_client, amount="25.00")
        response = _spend(auth_client, income["id"], amount="25.01")
        assert_api_error(
            response,
            400,
            errors={"amount": "Insufficient remaining income"},
            message="Expenditure failed",
        )
        remaining = assert_envelope(auth_client.get(INCOMES_URL), 200)["data"][0]["remaining"]
        assert Decimal(remaining) == Decimal("25.00")

    def test_missing_income_returns_404(self, auth_client):
        response = _spend(auth_client, income_id=999)
        assert_api_error(
            response,
            404,
            errors={"income_id": "Income not found"},
            message="Expenditure failed",
        )

    def test_cannot_spend_another_users_income(self, auth_client, valid_payload):
        income = _add_income(auth_client, amount="100.00")
        valid_payload["email"] = "john@example.com"
        assert_envelope(auth_client.post(REGISTER_URL, json=valid_payload), 201)
        login = auth_client.post(
            LOGIN_URL,
            json={"email": "john@example.com", "password": valid_payload["password"]},
        )
        auth_client.headers["Authorization"] = (
            f"Bearer {login.json()['data']['access_token']}"
        )
        response = _spend(auth_client, income["id"], amount="10.00")
        assert_api_error(response, 404, errors={"income_id": "Income not found"})

    def test_list_expenditures(self, auth_client):
        income = _add_income(auth_client, amount="100.00")
        _spend(auth_client, income["id"], amount="10.00", title="Bus")
        _spend(auth_client, income["id"], amount="5.00", title="Coffee")
        body = assert_envelope(auth_client.get(EXPENDITURES_URL), 200)
        titles = [item["title"] for item in body["data"]]
        assert titles == ["Coffee", "Bus"]

    def test_add_expenditure_requires_auth(self, client):
        response = client.post(
            EXPENDITURES_URL,
            json={"income_id": 1, "title": "Food", "amount": "10.00"},
        )
        assert_api_error(response, 401, errors={"token": "Authentication required"})

    def test_add_expenditure_without_csrf_returns_403(self, bare_client):
        response = bare_client.post(
            EXPENDITURES_URL,
            json={"income_id": 1, "title": "Food", "amount": "10.00"},
        )
        assert_api_error(response, 403, errors={"csrf": "CSRF token missing"})


class TestExpenditureValidation:
    @pytest.mark.parametrize("field", ["income_id", "title", "amount"])
    def test_missing_required_field_returns_422(self, auth_client, field):
        payload = {"income_id": 1, "title": "Food", "amount": "10.00"}
        del payload[field]
        response = auth_client.post(EXPENDITURES_URL, json=payload)
        assert_validation_error(response, field, "This field is required")

    def test_zero_amount_returns_422(self, auth_client):
        income = _add_income(auth_client)
        response = _spend(auth_client, income["id"], amount="0")
        assert_envelope(response, 422)
