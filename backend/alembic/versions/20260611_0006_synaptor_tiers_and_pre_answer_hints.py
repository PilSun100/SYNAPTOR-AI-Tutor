"""synaptor tiers and pre-answer hints

Revision ID: 20260611_0006
Revises: 20260610_0005
Create Date: 2026-06-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260611_0006"
down_revision: str | None = "20260610_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("hint_logs") as batch_op:
        batch_op.alter_column("user_answer_id", existing_type=sa.Integer(), nullable=True)
        batch_op.add_column(sa.Column("session_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("question_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("concept_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("stuck_reason", sa.String(length=100), nullable=True))
        batch_op.create_foreign_key("fk_hint_logs_session_id", "learning_sessions", ["session_id"], ["id"])
        batch_op.create_foreign_key("fk_hint_logs_question_id", "questions", ["question_id"], ["id"])
        batch_op.create_foreign_key("fk_hint_logs_concept_id", "concepts", ["concept_id"], ["id"])
        batch_op.create_foreign_key("fk_hint_logs_user_id", "users", ["user_id"], ["id"])

    with op.batch_alter_table("concept_mastery") as batch_op:
        batch_op.add_column(sa.Column("concept_score", sa.Float(), nullable=False, server_default="0.0"))
        batch_op.add_column(sa.Column("tier_name", sa.String(length=50), nullable=False, server_default="초심자"))

    op.create_table(
        "material_mastery",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("material_id", sa.Integer(), sa.ForeignKey("learning_materials.id"), nullable=False),
        sa.Column("material_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("tier_name", sa.String(length=50), nullable=False, server_default="초심자"),
        sa.Column("completed_concepts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_concepts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("user_id", "material_id", name="uq_material_mastery_user_material"),
    )


def downgrade() -> None:
    op.drop_table("material_mastery")

    with op.batch_alter_table("concept_mastery") as batch_op:
        batch_op.drop_column("tier_name")
        batch_op.drop_column("concept_score")

    with op.batch_alter_table("hint_logs") as batch_op:
        batch_op.drop_constraint("fk_hint_logs_user_id", type_="foreignkey")
        batch_op.drop_constraint("fk_hint_logs_concept_id", type_="foreignkey")
        batch_op.drop_constraint("fk_hint_logs_question_id", type_="foreignkey")
        batch_op.drop_constraint("fk_hint_logs_session_id", type_="foreignkey")
        batch_op.drop_column("stuck_reason")
        batch_op.drop_column("user_id")
        batch_op.drop_column("concept_id")
        batch_op.drop_column("question_id")
        batch_op.drop_column("session_id")
        batch_op.alter_column("user_answer_id", existing_type=sa.Integer(), nullable=False)
