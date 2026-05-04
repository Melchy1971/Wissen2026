"""add chunk full text search support

Revision ID: 20260504_0011
Revises: 20260504_0010
Create Date: 2026-05-04
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260504_0011"
down_revision: str | None = "20260504_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


LEGACY_FTS_INDEX = "ix_document_chunks_content_fts"
SEARCH_VECTOR_COLUMN = "search_vector"
SEARCH_VECTOR_INDEX = "ix_document_chunks_search_vector"


def upgrade() -> None:
    bind = op.get_bind()
    dialect_name = bind.dialect.name

    if dialect_name == "postgresql":
        _upgrade_postgresql()
        return

    if dialect_name == "sqlite":
        _upgrade_sqlite()
        return

    raise RuntimeError(f"Unsupported database dialect for chunk FTS migration: {dialect_name}")


def downgrade() -> None:
    bind = op.get_bind()
    dialect_name = bind.dialect.name

    if dialect_name == "postgresql":
        _downgrade_postgresql()
        return

    if dialect_name == "sqlite":
        _downgrade_sqlite()
        return

    raise RuntimeError(f"Unsupported database dialect for chunk FTS migration: {dialect_name}")


def _upgrade_postgresql() -> None:
    op.execute(f"DROP INDEX IF EXISTS {LEGACY_FTS_INDEX}")
    op.execute(
        "ALTER TABLE document_chunks "
        "ADD COLUMN search_vector tsvector "
        "GENERATED ALWAYS AS (to_tsvector('simple', coalesce(content, ''))) STORED"
    )
    op.execute(
        f"CREATE INDEX {SEARCH_VECTOR_INDEX} "
        "ON document_chunks USING gin (search_vector)"
    )


def _downgrade_postgresql() -> None:
    op.execute(f"DROP INDEX IF EXISTS {SEARCH_VECTOR_INDEX}")
    op.execute(
        "ALTER TABLE document_chunks "
        "DROP COLUMN IF EXISTS search_vector"
    )
    op.execute(
        f"CREATE INDEX {LEGACY_FTS_INDEX} "
        "ON document_chunks USING gin (to_tsvector('simple', content))"
    )


def _upgrade_sqlite() -> None:
    # SQLite is only used for lightweight development/tests in this repository.
    # We keep schema parity for ORM usage but do not introduce a second FTS stack here.
    op.add_column(
        "document_chunks",
        sa.Column(SEARCH_VECTOR_COLUMN, sa.Text(), nullable=True),
    )
    op.execute("UPDATE document_chunks SET search_vector = content WHERE search_vector IS NULL")


def _downgrade_sqlite() -> None:
    op.drop_column("document_chunks", SEARCH_VECTOR_COLUMN)