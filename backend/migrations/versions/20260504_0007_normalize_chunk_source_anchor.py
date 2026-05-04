"""normalize chunk source anchors

Revision ID: 20260504_0007
Revises: 20260504_0006
Create Date: 2026-05-04
"""

from collections.abc import Sequence

from alembic import op


revision: str = "20260504_0007"
down_revision: str | None = "20260504_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        update document_chunks
        set metadata = jsonb_set(
            metadata,
            '{legacy_source_anchor}',
            metadata->'source_anchor',
            true
        )
        where metadata ? 'source_anchor'
          and (
            jsonb_typeof(metadata->'source_anchor') <> 'object'
            or not (metadata->'source_anchor' ? 'type')
            or not (metadata->'source_anchor' ? 'char_start')
            or metadata->'source_anchor' ? 'offset'
          )
        """
    )
    op.execute(
        """
        update document_chunks
        set metadata = jsonb_set(
            metadata,
            '{source_anchor}',
            jsonb_build_object(
                'type', 'legacy_unknown',
                'page', null,
                'paragraph', null,
                'char_start', null,
                'char_end', null
            ),
            true
        )
        where not (metadata ? 'source_anchor')
          or jsonb_typeof(metadata->'source_anchor') <> 'object'
          or not (metadata->'source_anchor' ? 'type')
          or not (metadata->'source_anchor' ? 'char_start')
          or metadata->'source_anchor' ? 'offset'
        """
    )


def downgrade() -> None:
    op.execute(
        """
        update document_chunks
        set metadata = jsonb_set(
            metadata - 'legacy_source_anchor',
            '{source_anchor}',
            metadata->'legacy_source_anchor',
            true
        )
        where metadata->'source_anchor'->>'type' = 'legacy_unknown'
          and metadata ? 'legacy_source_anchor'
        """
    )
