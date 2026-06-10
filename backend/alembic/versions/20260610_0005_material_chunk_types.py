"""material chunk types

Revision ID: 20260610_0005
Revises: 20260610_0004
Create Date: 2026-06-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260610_0005"
down_revision: str | None = "20260610_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("material_chunks") as batch_op:
        batch_op.add_column(
            sa.Column("chunk_type", sa.String(length=50), nullable=False, server_default="text")
        )


def downgrade() -> None:
    with op.batch_alter_table("material_chunks") as batch_op:
        batch_op.drop_column("chunk_type")
