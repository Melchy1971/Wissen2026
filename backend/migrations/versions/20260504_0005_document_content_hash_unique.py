"""document content hash uniqueness

Revision ID: 20260504_0005
Revises: 20260430_0004
Create Date: 2026-05-04
"""

from collections.abc import Sequence

from alembic import op


revision: str = "20260504_0005"
down_revision: str | None = "20260430_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_documents_workspace_content_hash",
        "documents",
        ["workspace_id", "content_hash"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_documents_workspace_content_hash",
        "documents",
        type_="unique",
    )
