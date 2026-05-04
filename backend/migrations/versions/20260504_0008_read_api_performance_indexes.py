"""read api performance indexes

Revision ID: 20260504_0008
Revises: 20260504_0007
Create Date: 2026-05-04
"""

from collections.abc import Sequence

from alembic import op


revision: str = "20260504_0008"
down_revision: str | None = "20260504_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Composite index for workspace-scoped document list, sorted by recency.
    # Migration 0001 already has ix_documents_workspace_id (single) and
    # ix_documents_created_at (single). This composite eliminates the Sort step:
    # WHERE workspace_id = X ORDER BY created_at DESC LIMIT 20 becomes a pure index scan.
    op.execute(
        "CREATE INDEX ix_documents_workspace_created "
        "ON documents (workspace_id, created_at DESC)"
    )

    # Triple composite covering index for all chunk queries.
    # Migration 0002 already has ix_document_chunks_document_id and
    # ix_document_chunks_document_version_id as separate single-column indexes.
    # This triple adds chunk_index so ORDER BY needs no separate Sort node,
    # and the prefix (document_id, document_version_id) covers COUNT / SUM queries.
    op.execute(
        "CREATE INDEX ix_document_chunks_doc_ver_idx "
        "ON document_chunks (document_id, document_version_id, chunk_index)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_doc_ver_idx")
    op.execute("DROP INDEX IF EXISTS ix_documents_workspace_created")
