from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from app.schemas.documents import DocumentChunkSourceAnchor
from app.schemas.search import SearchChunkResult


class ContextBuildError(ValueError):
    pass


@dataclass(frozen=True)
class ExcludedContextChunk:
    chunk_id: str
    reason: str


@dataclass(frozen=True)
class ContextBlock:
    chunk_id: str
    document_id: str
    document_title: str
    source_anchor: DocumentChunkSourceAnchor
    text: str
    rank: float
    char_count: int
    token_count: int


@dataclass(frozen=True)
class ContextPackage:
    blocks: list[ContextBlock]
    total_chars: int
    total_tokens: int
    excluded_chunks: list[ExcludedContextChunk]


class ContextBuilder:
    def __init__(
        self,
        *,
        max_context_chars: int,
        max_context_tokens: int,
        min_chunk_chars: int = 40,
    ) -> None:
        if max_context_chars < 1:
            raise ContextBuildError("max_context_chars must be positive")
        if max_context_tokens < 1:
            raise ContextBuildError("max_context_tokens must be positive")
        if min_chunk_chars < 1:
            raise ContextBuildError("min_chunk_chars must be positive")

        self._max_context_chars = max_context_chars
        self._max_context_tokens = max_context_tokens
        self._min_chunk_chars = min_chunk_chars

    def build(
        self,
        results: list[SearchChunkResult],
        *,
        chunk_text_by_id: Mapping[str, str] | None = None,
    ) -> ContextPackage:
        blocks: list[ContextBlock] = []
        excluded_chunks: list[ExcludedContextChunk] = []
        seen_chunk_ids: set[str] = set()
        total_chars = 0
        total_tokens = 0

        for result in results:
            if result.chunk_id in seen_chunk_ids:
                excluded_chunks.append(ExcludedContextChunk(chunk_id=result.chunk_id, reason="duplicate_chunk"))
                continue

            seen_chunk_ids.add(result.chunk_id)

            text = self._resolve_text(result, chunk_text_by_id)
            if len(text) < self._min_chunk_chars:
                excluded_chunks.append(ExcludedContextChunk(chunk_id=result.chunk_id, reason="chunk_too_short"))
                continue

            token_count = self._estimate_tokens(text)
            if token_count < 1:
                excluded_chunks.append(ExcludedContextChunk(chunk_id=result.chunk_id, reason="chunk_empty"))
                continue

            char_count = len(text)
            if char_count > self._max_context_chars or token_count > self._max_context_tokens:
                excluded_chunks.append(
                    ExcludedContextChunk(chunk_id=result.chunk_id, reason="chunk_exceeds_context_limit")
                )
                continue

            if total_chars + char_count > self._max_context_chars:
                excluded_chunks.append(ExcludedContextChunk(chunk_id=result.chunk_id, reason="context_char_limit"))
                continue

            if total_tokens + token_count > self._max_context_tokens:
                excluded_chunks.append(
                    ExcludedContextChunk(chunk_id=result.chunk_id, reason="context_token_limit")
                )
                continue

            blocks.append(
                ContextBlock(
                    chunk_id=result.chunk_id,
                    document_id=result.document_id,
                    document_title=result.document_title,
                    source_anchor=result.source_anchor,
                    text=text,
                    rank=result.rank,
                    char_count=char_count,
                    token_count=token_count,
                )
            )
            total_chars += char_count
            total_tokens += token_count

        return ContextPackage(
            blocks=blocks,
            total_chars=total_chars,
            total_tokens=total_tokens,
            excluded_chunks=excluded_chunks,
        )

    def _resolve_text(
        self,
        result: SearchChunkResult,
        chunk_text_by_id: Mapping[str, str] | None,
    ) -> str:
        if chunk_text_by_id is not None and result.chunk_id in chunk_text_by_id:
            return self._normalize_text(chunk_text_by_id[result.chunk_id])
        return self._normalize_text(result.text_preview)

    def _normalize_text(self, text: str) -> str:
        return text.strip()

    def _estimate_tokens(self, text: str) -> int:
        return len(text.split())