"""initial learning schema

Revision ID: 20260609_0001
Revises:
Create Date: 2026-06-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260609_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "learning_materials",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=True),
        sa.Column("extracted_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "material_chunks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("material_id", sa.Integer(), sa.ForeignKey("learning_materials.id"), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("char_start", sa.Integer(), nullable=False),
        sa.Column("char_end", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "concepts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("material_id", sa.Integer(), sa.ForeignKey("learning_materials.id"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("difficulty", sa.String(length=50), nullable=False, server_default="medium"),
        sa.Column("parent_concept_id", sa.Integer(), sa.ForeignKey("concepts.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "learning_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("material_id", sa.Integer(), sa.ForeignKey("learning_materials.id"), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "questions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("concept_id", sa.Integer(), sa.ForeignKey("concepts.id"), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("question_type", sa.String(length=100), nullable=False),
        sa.Column("expected_answer", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "concept_mastery",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("concept_id", sa.Integer(), sa.ForeignKey("concepts.id"), nullable=False, unique=True),
        sa.Column("mastery_level", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("cognitive_load_score", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("last_answer_quality", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("misconception_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("hint_dependency", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("response_speed_score", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("next_difficulty", sa.String(length=50), nullable=False, server_default="diagnostic"),
        sa.Column("next_question_type", sa.String(length=100), nullable=False, server_default="definition"),
        sa.Column("learner_level_label", sa.String(length=100), nullable=False, server_default="진단 전"),
        sa.Column("recommended_strategy", sa.Text(), nullable=False, server_default=""),
        sa.Column("personalized_explanation", sa.Text(), nullable=False, server_default=""),
        sa.Column("last_reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("next_review_at", sa.DateTime(), nullable=True),
        sa.Column("total_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("correct_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("hint_used_count", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "self_explanations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("concept_id", sa.Integer(), sa.ForeignKey("concepts.id"), nullable=False),
        sa.Column("explanation_text", sa.Text(), nullable=False),
        sa.Column("accuracy_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("completeness_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("logical_connection_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "user_answers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.Integer(), sa.ForeignKey("learning_sessions.id"), nullable=False),
        sa.Column("question_id", sa.Integer(), sa.ForeignKey("questions.id"), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=False),
        sa.Column("correctness_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("missing_points", sa.Text(), nullable=False, server_default=""),
        sa.Column("misconception_detected", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("response_time", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "hint_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_answer_id", sa.Integer(), sa.ForeignKey("user_answers.id"), nullable=False),
        sa.Column("hint_level", sa.Integer(), nullable=False),
        sa.Column("hint_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "evidence_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("chunk_id", sa.Integer(), sa.ForeignKey("material_chunks.id"), nullable=False),
        sa.Column("purpose", sa.String(length=100), nullable=False),
        sa.Column("related_question_id", sa.Integer(), sa.ForeignKey("questions.id"), nullable=True),
        sa.Column("related_answer_id", sa.Integer(), sa.ForeignKey("user_answers.id"), nullable=True),
        sa.Column("relevance_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("evidence_logs")
    op.drop_table("hint_logs")
    op.drop_table("user_answers")
    op.drop_table("self_explanations")
    op.drop_table("concept_mastery")
    op.drop_table("questions")
    op.drop_table("learning_sessions")
    op.drop_table("concepts")
    op.drop_table("material_chunks")
    op.drop_table("learning_materials")
