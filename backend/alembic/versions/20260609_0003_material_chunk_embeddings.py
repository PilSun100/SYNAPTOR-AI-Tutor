"""material chunk embeddings

Revision ID: 20260609_0003
Revises: 20260609_0002
Create Date: 2026-06-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260609_0003"
down_revision: str | None = "20260609_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect_name = bind.dialect.name

    if dialect_name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
        op.execute("ALTER TABLE material_chunks ADD COLUMN embedding vector(768)")
    else:
        with op.batch_alter_table("material_chunks") as batch_op:
            batch_op.add_column(sa.Column("embedding", sa.Text(), nullable=True))

    with op.batch_alter_table("material_chunks") as batch_op:
        batch_op.add_column(sa.Column("embedding_model", sa.String(length=100), nullable=True))

    if dialect_name == "postgresql":
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_material_chunks_embedding_cosine "
            "ON material_chunks USING hnsw (embedding vector_cosine_ops)"
        )


def downgrade() -> None:
    bind = op.get_bind()
    dialect_name = bind.dialect.name

    if dialect_name == "postgresql":
        op.execute("DROP INDEX IF EXISTS ix_material_chunks_embedding_cosine")

    with op.batch_alter_table("material_chunks") as batch_op:
        batch_op.drop_column("embedding_model")
        batch_op.drop_column("embedding")
