"""repair legacy document states

Revision ID: 20260504_0010
Revises: 20260504_0009
Create Date: 2026-05-04
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260504_0010"
down_revision: str | None = "20260504_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


REPAIR_LOG_TABLE = "migration_document_repairs"


repair_log = sa.table(
    REPAIR_LOG_TABLE,
    sa.column("entity_type", sa.String(length=32)),
    sa.column("entity_id", sa.String(length=36)),
    sa.column("issue_codes", postgresql.JSONB(astext_type=sa.Text())),
    sa.column("before_payload", postgresql.JSONB(astext_type=sa.Text())),
    sa.column("after_payload", postgresql.JSONB(astext_type=sa.Text())),
)

documents_table = sa.table(
    "documents",
    sa.column("id", sa.String(length=36)),
    sa.column("workspace_id", sa.String(length=36)),
    sa.column("current_version_id", sa.String(length=36)),
    sa.column("content_hash", sa.String(length=128)),
    sa.column("import_status", sa.String(length=32)),
)

document_versions_table = sa.table(
    "document_versions",
    sa.column("id", sa.String(length=36)),
    sa.column("markdown_hash", sa.String(length=128)),
)

document_chunks_table = sa.table(
    "document_chunks",
    sa.column("id", sa.String(length=36)),
    sa.column("content_hash", sa.String(length=128)),
    sa.column("metadata", postgresql.JSONB(astext_type=sa.Text())),
)


def upgrade() -> None:
    op.create_table(
        REPAIR_LOG_TABLE,
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("entity_type", sa.String(length=32), nullable=False),
        sa.Column("entity_id", sa.String(length=36), nullable=False),
        sa.Column("issue_codes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("before_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("after_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("repaired_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index(
        "ix_migration_document_repairs_entity",
        REPAIR_LOG_TABLE,
        ["entity_type", "entity_id"],
    )

    bind = op.get_bind()

    _repair_document_versions(bind)
    _repair_document_chunks(bind)
    _repair_documents(bind)

    op.create_check_constraint(
        "ck_documents_readable_status_requires_current_version",
        "documents",
        "import_status in ('pending', 'parsing', 'failed') OR current_version_id IS NOT NULL",
    )
    op.create_check_constraint(
        "ck_document_chunks_source_anchor_normalized",
        "document_chunks",
        "metadata ? 'source_anchor'"
        " AND jsonb_typeof(metadata->'source_anchor') = 'object'"
        " AND metadata->'source_anchor' ? 'type'"
        " AND metadata->'source_anchor' ? 'page'"
        " AND metadata->'source_anchor' ? 'paragraph'"
        " AND metadata->'source_anchor' ? 'char_start'"
        " AND metadata->'source_anchor' ? 'char_end'"
        " AND jsonb_typeof(metadata->'source_anchor'->'type') = 'string'"
        " AND jsonb_typeof(metadata->'source_anchor'->'page') in ('number', 'null')"
        " AND jsonb_typeof(metadata->'source_anchor'->'paragraph') in ('number', 'null')"
        " AND jsonb_typeof(metadata->'source_anchor'->'char_start') in ('number', 'null')"
        " AND jsonb_typeof(metadata->'source_anchor'->'char_end') in ('number', 'null')",
    )


def downgrade() -> None:
    bind = op.get_bind()

    op.drop_constraint(
        "ck_document_chunks_source_anchor_normalized",
        "document_chunks",
        type_="check",
    )
    op.drop_constraint(
        "ck_documents_readable_status_requires_current_version",
        "documents",
        type_="check",
    )

    rows = bind.execute(
        sa.text(
            f"""
            select entity_type, entity_id, before_payload
            from {REPAIR_LOG_TABLE}
            order by id desc
            """
        )
    ).mappings()

    for row in rows:
        before_payload = dict(row["before_payload"] or {})
        if not before_payload:
            continue

        if row["entity_type"] == "document":
            bind.execute(
                sa.update(documents_table)
                .where(documents_table.c.id == row["entity_id"])
                .values(**before_payload)
            )
        elif row["entity_type"] == "document_version":
            bind.execute(
                sa.update(document_versions_table)
                .where(document_versions_table.c.id == row["entity_id"])
                .values(**before_payload)
            )
        elif row["entity_type"] == "document_chunk":
            bind.execute(
                sa.update(document_chunks_table)
                .where(document_chunks_table.c.id == row["entity_id"])
                .values(**before_payload)
            )

    op.drop_index("ix_migration_document_repairs_entity", table_name=REPAIR_LOG_TABLE)
    op.drop_table(REPAIR_LOG_TABLE)


def _repair_document_versions(bind: sa.Connection) -> None:
    version_rows = bind.execute(
        sa.text(
            """
            select id, normalized_markdown, markdown_hash
            from document_versions
            """
        )
    ).mappings()

    for row in version_rows:
        issue_codes: list[str] = []
        before_payload: dict[str, Any] = {}
        after_payload: dict[str, Any] = {}

        if _is_blank(row["markdown_hash"]):
            normalized_markdown = row["normalized_markdown"] or ""
            if normalized_markdown.strip():
                markdown_hash = _sha256(normalized_markdown)
                issue_codes.append("markdown_hash_recomputed")
            else:
                markdown_hash = _sha256(f"legacy-empty-version:{row['id']}")
                issue_codes.append("markdown_hash_placeholder")

            before_payload["markdown_hash"] = row["markdown_hash"]
            after_payload["markdown_hash"] = markdown_hash

            bind.execute(
                sa.update(document_versions_table)
                .where(document_versions_table.c.id == row["id"])
                .values(markdown_hash=markdown_hash)
            )

        if issue_codes:
            _log_repair(
                bind,
                entity_type="document_version",
                entity_id=row["id"],
                issue_codes=issue_codes,
                before_payload=before_payload,
                after_payload=after_payload,
            )


def _repair_document_chunks(bind: sa.Connection) -> None:
    chunk_rows = bind.execute(
        sa.text(
            """
            select id, content, content_hash, metadata
            from document_chunks
            """
        )
    ).mappings()

    for row in chunk_rows:
        issue_codes: list[str] = []
        before_payload: dict[str, Any] = {}
        after_payload: dict[str, Any] = {}
        update_values: dict[str, Any] = {}

        metadata = dict(row["metadata"] or {})
        normalized_metadata, metadata_changed, metadata_issue_codes = _normalize_chunk_metadata(metadata)
        if metadata_changed:
            issue_codes.extend(metadata_issue_codes)
            before_payload["metadata"] = _json_safe(metadata)
            after_payload["metadata"] = _json_safe(normalized_metadata)
            update_values["metadata"] = normalized_metadata

        if _is_blank(row["content_hash"]):
            chunk_hash = _sha256((row["content"] or "").strip() or f"legacy-empty-chunk:{row['id']}")
            issue_codes.append("content_hash_recomputed")
            before_payload["content_hash"] = row["content_hash"]
            after_payload["content_hash"] = chunk_hash
            update_values["content_hash"] = chunk_hash

        if update_values:
            bind.execute(
                sa.update(document_chunks_table)
                .where(document_chunks_table.c.id == row["id"])
                .values(**update_values)
            )
            _log_repair(
                bind,
                entity_type="document_chunk",
                entity_id=row["id"],
                issue_codes=issue_codes,
                before_payload=before_payload,
                after_payload=after_payload,
            )


def _repair_documents(bind: sa.Connection) -> None:
    version_rows = bind.execute(
        sa.text(
            """
            select id, document_id, markdown_hash, created_at, version_number
            from document_versions
            order by document_id asc, created_at desc, version_number desc, id desc
            """
        )
    ).mappings().all()
    chunk_counts = {
        row["document_version_id"]: row["chunk_count"]
        for row in bind.execute(
            sa.text(
                """
                select document_version_id, count(*) as chunk_count
                from document_chunks
                group by document_version_id
                """
            )
        ).mappings()
    }
    versions_by_id = {row["id"]: row for row in version_rows}
    versions_by_document: dict[str, list[dict[str, Any]]] = {}
    for row in version_rows:
        versions_by_document.setdefault(row["document_id"], []).append(dict(row))

    document_rows = bind.execute(
        sa.text(
            """
            select id, workspace_id, current_version_id, content_hash, import_status
            from documents
            """
        )
    ).mappings()

    for row in document_rows:
        issue_codes: list[str] = []
        before_payload: dict[str, Any] = {}
        after_payload: dict[str, Any] = {}
        update_values: dict[str, Any] = {}

        document_versions = versions_by_document.get(row["id"], [])
        current_version_id = row["current_version_id"]

        if current_version_id is not None:
            current_version = versions_by_id.get(current_version_id)
            if current_version is None or current_version["document_id"] != row["id"]:
                before_payload["current_version_id"] = current_version_id
                issue_codes.append("current_version_relinked")
                current_version_id = None

        if current_version_id is None and document_versions:
            current_version_id = document_versions[0]["id"]
            before_payload.setdefault("current_version_id", row["current_version_id"])
            after_payload["current_version_id"] = current_version_id
            update_values["current_version_id"] = current_version_id
            issue_codes.append("current_version_backfilled")

        if not document_versions:
            derived_status = "failed"
            issue_codes.append("document_without_versions")
            if row["current_version_id"] is not None:
                before_payload.setdefault("current_version_id", row["current_version_id"])
                after_payload["current_version_id"] = None
                update_values["current_version_id"] = None
        else:
            chunk_count = chunk_counts.get(current_version_id, 0) if current_version_id is not None else 0
            derived_status = "chunked" if chunk_count > 0 else "parsed"
            if chunk_count == 0:
                issue_codes.append("version_without_chunks")

        if row["import_status"] != derived_status:
            before_payload["import_status"] = row["import_status"]
            after_payload["import_status"] = derived_status
            update_values["import_status"] = derived_status
            issue_codes.append("import_status_rederived")

        if _is_blank(row["content_hash"]):
            basis_version = versions_by_id.get(current_version_id) if current_version_id is not None else None
            basis = basis_version["markdown_hash"] if basis_version is not None else row["id"]
            content_hash = _sha256(f"legacy-document:{row['workspace_id']}:{row['id']}:{basis}")
            before_payload["content_hash"] = row["content_hash"]
            after_payload["content_hash"] = content_hash
            update_values["content_hash"] = content_hash
            issue_codes.append("content_hash_placeholder")

        if update_values:
            bind.execute(
                sa.update(documents_table)
                .where(documents_table.c.id == row["id"])
                .values(**update_values)
            )
            _log_repair(
                bind,
                entity_type="document",
                entity_id=row["id"],
                issue_codes=issue_codes,
                before_payload=before_payload,
                after_payload=after_payload,
            )


def _normalize_chunk_metadata(metadata: dict[str, Any]) -> tuple[dict[str, Any], bool, list[str]]:
    normalized = dict(metadata)
    issue_codes: list[str] = []

    current_anchor = normalized.get("source_anchor")
    if not _is_normalized_source_anchor(current_anchor):
        if current_anchor is not None and "legacy_source_anchor" not in normalized:
            normalized["legacy_source_anchor"] = current_anchor
            issue_codes.append("source_anchor_legacy_preserved")
        normalized["source_anchor"] = _normalize_source_anchor(current_anchor)
        issue_codes.append("source_anchor_normalized")
        return normalized, True, issue_codes

    canonical_anchor = _normalize_source_anchor(current_anchor)
    if canonical_anchor != current_anchor:
        normalized["source_anchor"] = canonical_anchor
        issue_codes.append("source_anchor_canonicalized")
        return normalized, True, issue_codes

    return normalized, False, issue_codes


def _normalize_source_anchor(anchor: Any) -> dict[str, Any]:
    if not isinstance(anchor, dict):
        return {
            "type": "legacy_unknown",
            "page": None,
            "paragraph": None,
            "char_start": None,
            "char_end": None,
        }

    char_start = _coerce_int(anchor.get("char_start"))
    char_end = _coerce_int(anchor.get("char_end"))
    if char_start is not None and char_end is not None and char_end < char_start:
        char_end = None

    anchor_type = anchor.get("type") if isinstance(anchor.get("type"), str) else "legacy_unknown"
    if anchor_type not in {"text", "pdf_page", "docx_paragraph", "legacy_unknown"}:
        anchor_type = "legacy_unknown"

    return {
        "type": anchor_type,
        "page": _coerce_int(anchor.get("page")),
        "paragraph": _coerce_int(anchor.get("paragraph")),
        "char_start": char_start,
        "char_end": char_end,
    }


def _is_normalized_source_anchor(anchor: Any) -> bool:
    if not isinstance(anchor, dict):
        return False

    required_keys = {"type", "page", "paragraph", "char_start", "char_end"}
    if set(anchor.keys()) < required_keys:
        return False

    if not isinstance(anchor.get("type"), str):
        return False

    for key in ("page", "paragraph", "char_start", "char_end"):
        value = anchor.get(key)
        if value is not None and not isinstance(value, int):
            return False

    return "offset" not in anchor


def _coerce_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, Decimal) and value == int(value):
        return int(value)
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def _log_repair(
    bind: sa.Connection,
    *,
    entity_type: str,
    entity_id: str,
    issue_codes: list[str],
    before_payload: dict[str, Any],
    after_payload: dict[str, Any],
) -> None:
    bind.execute(
        sa.insert(repair_log).values(
            entity_type=entity_type,
            entity_id=entity_id,
            issue_codes=_json_safe(issue_codes),
            before_payload=_json_safe(before_payload),
            after_payload=_json_safe(after_payload),
        )
    )


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(inner) for key, inner in value.items()}
    if isinstance(value, list):
        return [_json_safe(inner) for inner in value]
    if isinstance(value, tuple):
        return [_json_safe(inner) for inner in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value