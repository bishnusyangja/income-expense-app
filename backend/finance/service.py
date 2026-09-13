from decimal import Decimal

from sqlalchemy.orm import Session

from finance.dbmodels import Expenditure, Income
from finance.pymodel import ExpenditureCreate, IncomeCreate
from user.dbmodels import User


class IncomeNotFoundError(Exception):
    pass


class InsufficientIncomeError(Exception):
    pass


def create_income(db: Session, user: User, payload: IncomeCreate) -> Income:
    income = Income(
        user_id=user.id,
        title=payload.title,
        amount=payload.amount,
        remaining=payload.amount,
        note=payload.note,
    )
    db.add(income)
    db.commit()
    db.refresh(income)
    return income


def list_incomes(db: Session, user: User) -> list[Income]:
    return (
        db.query(Income)
        .filter(Income.user_id == user.id)
        .order_by(Income.id.desc())
        .all()
    )


def get_user_income(db: Session, user: User, income_id: int) -> Income | None:
    return (
        db.query(Income)
        .filter(Income.id == income_id, Income.user_id == user.id)
        .first()
    )


def create_expenditure(
    db: Session, user: User, payload: ExpenditureCreate
) -> tuple[Expenditure, Income]:
    income = get_user_income(db, user, payload.income_id)
    if income is None:
        raise IncomeNotFoundError

    remaining = Decimal(str(income.remaining))
    if payload.amount > remaining:
        raise InsufficientIncomeError

    income.remaining = remaining - payload.amount
    expenditure = Expenditure(
        user_id=user.id,
        income_id=income.id,
        title=payload.title,
        amount=payload.amount,
        note=payload.note,
    )
    db.add(expenditure)
    db.commit()
    db.refresh(expenditure)
    db.refresh(income)
    return expenditure, income


def list_expenditures(db: Session, user: User) -> list[Expenditure]:
    return (
        db.query(Expenditure)
        .filter(Expenditure.user_id == user.id)
        .order_by(Expenditure.id.desc())
        .all()
    )
