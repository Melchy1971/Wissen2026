from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from psycopg.types.json import Jsonb
from pydantic import BaseModel

from app.core.config import settings
from app.core.database import DatabaseConfigurationError, get_connection
from app.models.import_models import ImportRequest
from app.services.chunking_service import MarkdownChunkingService
from app.services.import_service import ImportService
from app.services.markdown_normalizer import DeterministicMarkdownNormalizer
from app.services.parser_service import MarkdownParser, StaticParserSelector, TextParser


router = APIRouter(prefix="/documents", tags=["documents"])

DuplicateStatus = Literal["created", "duplicate_existing"]


class ImportDocumentResponse(BaseModel):
    document_id: str
    version_id: str | None
    title: str
    chunk_count: int
    duplicate_status: DuplicateStatus


def build_import_service() -> ImportService:
    return ImportService(
        parser_selector=StaticParserSelector([TextParser(), MarkdownParser()]),
        normalizer=DeterministicMarkdownNormalizer(),
    )


@router.post("/import", response_model=ImportDocumentResponse)
async def import_document(file: UploadFile = File(...)) -> ImportDocumentResponse:
    filename = file.filename or "untitled"
    mime_type = canonical_mime_type(filename, file.content_type)
    source_bytes = await file.read()

    request = ImportRequest(filename=filename, mime_type=mime_type, source_bytes=source_bytes)
    import_result = build_import_service().import_document(request)
    if not import_result.success or import_result.document is None:
        detail = import_result.errors[0].message if import_result.errors else "Import failed"
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)

    title = title_from_filename(filename)
    chunks = MarkdownChunkingService().chunk(
        import_result.document.normalized_markdown,
        document_version_id="pending",
    )

    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select d.id, d.current_version_id, d.title, count(c.id)
                    from documents d
                    left join document_chunks c on c.document_id = d.id
                    where d.workspace_id = %s and d.content_hash = %s
                    group by d.id, d.current_version_id, d.title
                    order by d.created_at asc
                    limit 1
                    """,
                    (settings.default_workspace_id, import_result.source_content_hash),
                )
                existing = cursor.fetchone()
                if existing is not None:
                    return ImportDocumentResponse(
                        document_id=str(existing[0]),
                        version_id=str(existing[1]) if existing[1] is not None else None,
                        title=existing[2],
                        chunk_count=existing[3],
                        duplicate_status="duplicate_existing",
                    )

                document_id = str(uuid4())
                version_id = str(uuid4())
                cursor.execute(
                    """
                    insert into documents (
                        id,
                        workspace_id,
                        owner_user_id,
                        title,
                        source_type,
                        mime_type,
                        content_hash
                    )
                    values (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        document_id,
                        settings.default_workspace_id,
                        settings.default_user_id,
                        title,
                        "upload",
                        mime_type,
                        import_result.source_content_hash,
                    ),
                )
                cursor.execute(
                    """
                    insert into document_versions (
                        id,
                        document_id,
                        version_number,
                        normalized_markdown,
                        markdown_hash,
                        parser_version,
                        ocr_used,
                        ki_provider,
                        ki_model,
                        metadata
                    )
                    values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        version_id,
                        document_id,
                        1,
                        import_result.document.normalized_markdown,
                        import_result.document.markdown_hash,
                        import_result.document.parser_version or "unknown",
                        import_result.document.ocr_used,
                        import_result.document.ki_provider,
                        import_result.document.ki_model,
                        Jsonb(import_result.document.metadata),
                    ),
                )
                cursor.execute(
                    "update documents set current_version_id = %s, updated_at = now() where id = %s",
                    (version_id, document_id),
                )

                version_chunks = MarkdownChunkingService().chunk(
                    import_result.document.normalized_markdown,
                    document_version_id=version_id,
                )
                for chunk in version_chunks:
                    cursor.execute(
                        """
                        insert into document_chunks (
                            id,
                            document_id,
                            document_version_id,
                            chunk_index,
                            heading_path,
                            anchor,
                            content,
                            content_hash,
                            token_estimate,
                            metadata
                        )
                        values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            str(uuid4()),
                            document_id,
                            version_id,
                            chunk.chunk_index,
                            Jsonb(chunk.heading_path),
                            chunk.anchor,
                            chunk.content,
                            chunk.content_hash,
                            chunk.token_estimate,
                            Jsonb(chunk.metadata),
                        ),
                    )
    except DatabaseConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    return ImportDocumentResponse(
        document_id=document_id,
        version_id=version_id,
        title=title,
        chunk_count=len(chunks),
        duplicate_status="created",
    )


def canonical_mime_type(filename: str, content_type: str | None) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".txt":
        return "text/plain"
    if suffix == ".md":
        return "text/markdown"

    raise HTTPException(
        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        detail="Only .txt and .md uploads are supported",
    )


def title_from_filename(filename: str) -> str:
    title = Path(filename).stem.strip()
    return title or "Untitled"
