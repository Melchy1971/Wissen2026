"""m4 performance indexes

Revision ID: 20260505_0014
Revises: 20260505_0013
Create Date: 2026-05-05
"""

from collections.abc import Sequence

from alembic import op


revision: str = "20260505_0014"
down_revision: str | None = "20260505_0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_chat_sessions_workspace_updated_at "
        "ON chat_sessions (workspace_id, updated_at DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_chat_messages_session_message_index_desc "
        "ON chat_messages (session_id, message_index DESC)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_chat_messages_session_message_index_desc")
    op.execute("DROP INDEX IF EXISTS ix_chat_sessions_workspace_updated_at")