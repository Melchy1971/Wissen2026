import hashlib
import re
from dataclasses import dataclass, field
from typing import Any


DEFAULT_MAX_CHARS = 2400
ANCHOR_PREFIX = "dv"


@dataclass(frozen=True)
class MarkdownChunk:
    chunk_index: int
    heading_path: list[str]
    anchor: str
    content: str
    content_hash: str
    token_estimate: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MarkdownBlock:
    content: str
    block_type: str
    heading_level: int | None = None
    heading_text: str | None = None


class ChunkingError(Exception):
    pass


class MarkdownChunkingService:
    def __init__(self, max_chars: int = DEFAULT_MAX_CHARS) -> None:
        if max_chars < 200:
            raise ValueError("max_chars must be at least 200")
        self._max_chars = max_chars

    def chunk(
        self,
        normalized_markdown: str,
        document_version_id: str,
        source_anchor_type: str = "text",
    ) -> list[MarkdownChunk]:
        if not normalized_markdown.strip():
            raise ChunkingError("Cannot chunk empty markdown content")
        if not document_version_id.strip():
            raise ChunkingError("document_version_id is required for stable anchors")

        blocks = parse_markdown_blocks(normalized_markdown)
        chunks: list[MarkdownChunk] = []
        current_blocks: list[MarkdownBlock] = []
        current_heading_path: list[str] = []
        active_heading_path: list[str] = []

        for block in blocks:
            if block.block_type == "heading":
                active_heading_path = update_heading_path(
                    active_heading_path,
                    block.heading_level or 1,
                    block.heading_text or "",
                )
                if current_blocks:
                    chunks.append(
                        self._build_chunk(
                            current_blocks,
                            current_heading_path,
                            document_version_id,
                            len(chunks),
                        )
                    )
                    current_blocks = []
                current_heading_path = list(active_heading_path)
                current_blocks.append(block)
                continue

            block_heading_path = list(active_heading_path)
            if not current_blocks:
                current_heading_path = block_heading_path

            if (
                current_blocks
                and block.block_type == "paragraph"
                and _content_length(current_blocks) + len(block.content) + 2 > self._max_chars
            ):
                chunks.append(
                    self._build_chunk(
                        current_blocks,
                        current_heading_path,
                        document_version_id,
                        len(chunks),
                    )
                )
                current_blocks = []
                current_heading_path = block_heading_path

            current_blocks.append(block)

        if current_blocks:
            chunks.append(
                self._build_chunk(
                    current_blocks,
                    current_heading_path,
                    document_version_id,
                    len(chunks),
                )
            )

        return add_source_anchors(chunks, normalized_markdown, source_anchor_type)

    def _build_chunk(
        self,
        blocks: list[MarkdownBlock],
        heading_path: list[str],
        document_version_id: str,
        chunk_index: int,
    ) -> MarkdownChunk:
        content = "\n\n".join(block.content.strip("\n") for block in blocks).strip() + "\n"
        block_types = [block.block_type for block in blocks]
        return MarkdownChunk(
            chunk_index=chunk_index,
            heading_path=heading_path,
            anchor=make_anchor(document_version_id, chunk_index),
            content=content,
            content_hash=hash_text(content),
            token_estimate=estimate_tokens(content),
            metadata={
                "block_types": block_types,
                "char_count": len(content),
                "max_chars": self._max_chars,
                "contains_table": "table" in block_types,
                "contains_code": "code" in block_types,
            },
        )


def make_anchor(document_version_id: str, chunk_index: int) -> str:
    normalized_version = re.sub(r"[^a-zA-Z0-9_-]+", "-", document_version_id.strip()).strip("-")
    return f"{ANCHOR_PREFIX}:{normalized_version}:c{chunk_index:04d}"


def add_source_anchors(
    chunks: list[MarkdownChunk],
    normalized_markdown: str,
    source_anchor_type: str,
) -> list[MarkdownChunk]:
    anchored_chunks: list[MarkdownChunk] = []
    cursor = 0
    for chunk in chunks:
        needle = chunk.content.rstrip("\n")
        char_start = normalized_markdown.find(needle, cursor)
        if char_start < 0:
            char_start = None
            char_end = None
        else:
            char_end = char_start + len(needle)
            cursor = char_end

        source_anchor = {
            "type": normalize_source_anchor_type(source_anchor_type),
            "page": extract_pdf_page(chunk.content) if source_anchor_type == "pdf_page" else None,
            "paragraph": None,
            "char_start": char_start,
            "char_end": char_end,
        }
        metadata = {**chunk.metadata, "source_anchor": source_anchor}
        anchored_chunks.append(
            MarkdownChunk(
                chunk_index=chunk.chunk_index,
                heading_path=chunk.heading_path,
                anchor=chunk.anchor,
                content=chunk.content,
                content_hash=chunk.content_hash,
                token_estimate=chunk.token_estimate,
                metadata=metadata,
            )
        )
    return anchored_chunks


def normalize_source_anchor_type(source_anchor_type: str) -> str:
    if source_anchor_type in {"text", "pdf_page", "docx_paragraph", "legacy_unknown"}:
        return source_anchor_type
    return "legacy_unknown"


def extract_pdf_page(content: str) -> int | None:
    match = re.search(r"<!--\s*page:(\d+)\s*-->", content)
    if not match:
        return None
    return int(match.group(1))


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def estimate_tokens(text: str) -> int:
    return max(1, (len(text) + 3) // 4)


def parse_markdown_blocks(markdown: str) -> list[MarkdownBlock]:
    lines = markdown.splitlines()
    blocks: list[MarkdownBlock] = []
    index = 0

    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue

        if is_heading(line):
            level, text = parse_heading(line)
            blocks.append(MarkdownBlock(content=line, block_type="heading", heading_level=level, heading_text=text))
            index += 1
            continue

        if is_fence_line(line):
            start = index
            fence = line.lstrip()[:3]
            index += 1
            while index < len(lines):
                if lines[index].lstrip().startswith(fence):
                    index += 1
                    break
                index += 1
            blocks.append(MarkdownBlock(content="\n".join(lines[start:index]), block_type="code"))
            continue

        if is_table_start(lines, index):
            start = index
            index += 2
            while index < len(lines) and lines[index].strip().startswith("|"):
                index += 1
            blocks.append(MarkdownBlock(content="\n".join(lines[start:index]), block_type="table"))
            continue

        start = index
        index += 1
        while index < len(lines):
            next_line = lines[index]
            if not next_line.strip() or is_heading(next_line) or is_fence_line(next_line) or is_table_start(lines, index):
                break
            index += 1
        blocks.append(MarkdownBlock(content="\n".join(lines[start:index]), block_type="paragraph"))

    return blocks


def is_heading(line: str) -> bool:
    return bool(re.match(r"^#{1,6}\s+\S", line))


def parse_heading(line: str) -> tuple[int, str]:
    match = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
    if not match:
        return 1, line.strip()
    return len(match.group(1)), match.group(2).strip()


def update_heading_path(current: list[str], level: int, text: str) -> list[str]:
    path = current[: max(level - 1, 0)]
    path.append(text)
    return path


def is_fence_line(line: str) -> bool:
    stripped = line.lstrip()
    return stripped.startswith("```") or stripped.startswith("~~~")


def is_table_start(lines: list[str], index: int) -> bool:
    if index + 1 >= len(lines):
        return False
    header = lines[index].strip()
    separator = lines[index + 1].strip()
    return header.startswith("|") and "|" in header[1:] and bool(re.match(r"^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?$", separator))


def _content_length(blocks: list[MarkdownBlock]) -> int:
    return sum(len(block.content) + 2 for block in blocks)
