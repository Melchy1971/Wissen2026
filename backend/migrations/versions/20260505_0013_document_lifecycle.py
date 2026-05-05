"""document lifecycle

Revision ID: 20260505_0013
Revises: 20260504_0012
Create Date: 2026-05-05
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260505_0013"
down_revision: str | None = "20260504_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("lifecycle_status", sa.String(length=32), nullable=False, server_default="active"),
    )
    op.add_column("documents", sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("documents", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.create_check_constraint(
        "ck_documents_lifecycle_status_allowed",
        "documents",
        "lifecycle_status in ('active', 'archived', 'deleted')",
    )
    op.create_index(
        "ix_documents_workspace_lifecycle_created_at",
        "documents",
        ["workspace_id", "lifecycle_status", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_documents_workspace_lifecycle_created_at", table_name="documents")
    op.drop_constraint("ck_documents_lifecycle_status_allowed", "documents", type_="check")
    op.drop_column("documents", "deleted_at")
    op.drop_column("documents", "archived_at")
    op.drop_column("documents", "lifecycle_status")