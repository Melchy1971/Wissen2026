"""document version recency index

Revision ID: 20260504_0009
Revises: 20260504_0008
Create Date: 2026-05-04
"""

from collections.abc import Sequence

from alembic import op


revision: str = "20260504_0009"
down_revision: str | None = "20260504_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Supports WHERE document_id = X ORDER BY created_at DESC.
    # We keep the single-column document_id index for now to avoid changing
    # an already-deployed access path without measuring production plans first.
    op.execute(
        "CREATE INDEX ix_document_versions_document_created "
        "ON document_versions (document_id, created_at DESC)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_document_versions_document_created")