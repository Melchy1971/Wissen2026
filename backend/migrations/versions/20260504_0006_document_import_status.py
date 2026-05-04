"""document import status

Revision ID: 20260504_0006
Revises: 20260504_0005
Create Date: 2026-05-04
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260504_0006"
down_revision: str | None = "20260504_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("import_status", sa.String(length=32), nullable=True, server_default="pending"),
    )
    op.execute(
        """
        update documents d
        set import_status = case
            when exists (
                select 1
                from document_chunks c
                where c.document_id = d.id
                  and c.document_version_id = d.current_version_id
            )
            then 'chunked'
            else 'parsed'
        end
        """
    )
    op.alter_column("documents", "import_status", nullable=False)
    op.create_check_constraint(
        "ck_documents_import_status_allowed",
        "documents",
        "import_status in ('pending', 'parsing', 'parsed', 'chunked', 'failed', 'duplicate')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_documents_import_status_allowed", "documents", type_="check")
    op.drop_column("documents", "import_status")
