"""create incomes and expenditures tables

Revision ID: 4f8c2a91b3d7
Revises: 276eb4010ea3
Create Date: 2026-09-13 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "4f8c2a91b3d7"
down_revision: Union[str, Sequence[str], None] = "276eb4010ea3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "incomes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("remaining", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("incomes", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_incomes_id"), ["id"], unique=False)
        batch_op.create_index(batch_op.f("ix_incomes_user_id"), ["user_id"], unique=False)

    op.create_table(
        "expenditures",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("income_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["income_id"], ["incomes.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("expenditures", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_expenditures_id"), ["id"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_expenditures_income_id"), ["income_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_expenditures_user_id"), ["user_id"], unique=False
        )


def downgrade() -> None:
    with op.batch_alter_table("expenditures", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_expenditures_user_id"))
        batch_op.drop_index(batch_op.f("ix_expenditures_income_id"))
        batch_op.drop_index(batch_op.f("ix_expenditures_id"))

    op.drop_table("expenditures")

    with op.batch_alter_table("incomes", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_incomes_user_id"))
        batch_op.drop_index(batch_op.f("ix_incomes_id"))

    op.drop_table("incomes")
