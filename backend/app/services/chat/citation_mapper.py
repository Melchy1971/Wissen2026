from __future__ import annotations

from dataclasses import dataclass
import re

from app.schemas.documents import DocumentChunkSourceAnchor
from app.services.chat.context_builder import ContextBlock, ContextPackage


QUOTE_PREVIEW_MAX_CHARS = 300


class CitationMappingError(ValueError):
    pass


@dataclass(frozen=True)
class Citation:
    chunk_id: str
    document_id: str
    document_title: str
    source_anchor: DocumentChunkSourceAnchor
    quote_preview: str


class CitationMapper:
    def map_citations(self, *, answer: str, context: ContextPackage) -> list[Citation]:
        normalized_answer = answer.strip()
        if not normalized_answer:
            return []

        blocks_by_chunk_id = self._index_blocks(context)
        usages = self._find_chunk_usages(normalized_answer, blocks_by_chunk_id)

        citations: list[Citation] = []
        seen_chunk_ids: set[str] = set()
        for chunk_id, _position in usages:
            if chunk_id in seen_chunk_ids:
                continue
            seen_chunk_ids.add(chunk_id)
            block = blocks_by_chunk_id[chunk_id]
            citations.append(
                Citation(
                    chunk_id=block.chunk_id,
                    document_id=block.document_id,
                    document_title=block.document_title,
                    source_anchor=block.source_anchor,
                    quote_preview=self._build_quote_preview(block.text),
                )
            )
        return citations

    def _index_blocks(self, context: ContextPackage) -> dict[str, ContextBlock]:
        blocks_by_chunk_id: dict[str, ContextBlock] = {}
        for block in context.blocks:
            chunk_id = block.chunk_id.strip()
            if not chunk_id:
                raise CitationMappingError("context block chunk_id must not be blank")
            if chunk_id in blocks_by_chunk_id:
                raise CitationMappingError(f"duplicate context block chunk_id: {chunk_id}")
            blocks_by_chunk_id[chunk_id] = block
        return blocks_by_chunk_id

    def _find_chunk_usages(
        self,
        answer: str,
        blocks_by_chunk_id: dict[str, ContextBlock],
    ) -> list[tuple[str, int]]:
        usages: list[tuple[str, int]] = []
        for chunk_id in blocks_by_chunk_id:
            position = self._first_chunk_reference_position(answer, chunk_id)
            if position is not None:
                usages.append((chunk_id, position))
        usages.sort(key=lambda item: item[1])
        return usages

    def _first_chunk_reference_position(self, answer: str, chunk_id: str) -> int | None:
        pattern = re.compile(rf"(?<![A-Za-z0-9_-]){re.escape(chunk_id)}(?![A-Za-z0-9_-])")
        match = pattern.search(answer)
        if match is None:
            return None
        return match.start()

    def _build_quote_preview(self, text: str) -> str:
        normalized = " ".join(text.split())
        if len(normalized) <= QUOTE_PREVIEW_MAX_CHARS:
            return normalized
        return normalized[: QUOTE_PREVIEW_MAX_CHARS - 3].rstrip() + "..."