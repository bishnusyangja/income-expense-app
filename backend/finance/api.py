from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.responses import json_response
from finance.pymodel import (
    ExpenditureCreate,
    ExpenditureResponse,
    IncomeCreate,
    IncomeResponse,
)
from finance.service import (
    IncomeNotFoundError,
    InsufficientIncomeError,
    create_expenditure,
    create_income,
    list_expenditures,
    list_incomes,
)
from user.dbmodels import User

router = APIRouter(tags=["finance"])


def _income_data(income) -> dict:
    return IncomeResponse.model_validate(income).model_dump(mode="json")


def _expenditure_data(expenditure, remaining) -> dict:
    data = ExpenditureResponse.model_validate(
        {
            "id": expenditure.id,
            "user_id": expenditure.user_id,
            "income_id": expenditure.income_id,
            "title": expenditure.title,
            "amount": expenditure.amount,
            "note": expenditure.note,
            "created_at": expenditure.created_at,
            "income_remaining": remaining,
        }
    )
    return data.model_dump(mode="json")


@router.post("/incomes")
def add_income(
    payload: IncomeCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> JSONResponse:
    income = create_income(db, user, payload)
    return json_response(
        status_code=201,
        message="Income added successfully",
        data=_income_data(income),
    )


@router.get("/incomes")
def get_incomes(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> JSONResponse:
    incomes = list_incomes(db, user)
    return json_response(
        status_code=200,
        message="Incomes fetched successfully",
        data=[_income_data(income) for income in incomes],
    )


@router.post("/expenditures")
def add_expenditure(
    payload: ExpenditureCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> JSONResponse:
    try:
        expenditure, income = create_expenditure(db, user, payload)
    except IncomeNotFoundError:
        return json_response(
            status_code=404,
            message="Expenditure failed",
            errors={"income_id": "Income not found"},
        )
    except InsufficientIncomeError:
        return json_response(
            status_code=400,
            message="Expenditure failed",
            errors={"amount": "Insufficient remaining income"},
        )

    return json_response(
        status_code=201,
        message="Expenditure added successfully",
        data=_expenditure_data(expenditure, income.remaining),
    )


@router.get("/expenditures")
def get_expenditures(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> JSONResponse:
    items = list_expenditures(db, user)
    incomes = {income.id: income for income in list_incomes(db, user)}
    return json_response(
        status_code=200,
        message="Expenditures fetched successfully",
        data=[
            _expenditure_data(item, incomes[item.income_id].remaining)
            for item in items
        ],
    )
