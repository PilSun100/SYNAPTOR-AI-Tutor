"""user learning profiles

Revision ID: 20260610_0004
Revises: 20260609_0003
Create Date: 2026-06-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260610_0004"
down_revision: str | None = "20260609_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_learning_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("average_recall_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("explanation_quality", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("hint_dependency", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("misconception_frequency", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("preferred_difficulty_level", sa.String(length=50), nullable=False, server_default="easy"),
        sa.Column("frustration_risk", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("best_intervention_type", sa.String(length=100), nullable=False, server_default="active_recall"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index(
        "ix_user_learning_profiles_user_id",
        "user_learning_profiles",
        ["user_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_user_learning_profiles_user_id", table_name="user_learning_profiles")
    op.drop_table("user_learning_profiles")
