import pytest

from app.services.chunking_service import ChunkingError, MarkdownChunkingService, hash_text


DOCUMENT_VERSION_ID = "00000000-0000-0000-0000-000000000301"


def test_chunking_uses_headings_and_heading_paths() -> None:
    markdown = "# Root\n\nIntro\n\n## Child\n\nDetails\n"

    chunks = MarkdownChunkingService().chunk(markdown, DOCUMENT_VERSION_ID)

    assert [chunk.heading_path for chunk in chunks] == [["Root"], ["Root", "Child"]]
    assert chunks[0].content == "# Root\n\nIntro\n"
    assert chunks[1].content == "## Child\n\nDetails\n"


def test_chunking_splits_long_paragraphs_on_paragraph_boundaries() -> None:
    markdown = "# A\n\n" + ("x" * 180) + "\n\n" + ("y" * 180) + "\n"

    chunks = MarkdownChunkingService(max_chars=200).chunk(markdown, DOCUMENT_VERSION_ID)

    assert len(chunks) == 2
    assert chunks[0].content.startswith("# A")
    assert "x" * 180 in chunks[0].content
    assert chunks[1].content == ("y" * 180) + "\n"


def test_chunking_keeps_markdown_table_together() -> None:
    markdown = "# Table\n\n| Name | Wert |\n| --- | ---: |\n| Alpha | 42 |\n\nAfter\n"

    chunks = MarkdownChunkingService(max_chars=200).chunk(markdown, DOCUMENT_VERSION_ID)

    table_chunks = [chunk for chunk in chunks if chunk.metadata["contains_table"]]
    assert len(table_chunks) == 1
    assert "| Name | Wert |\n| --- | ---: |\n| Alpha | 42 |" in table_chunks[0].content


def test_chunking_keeps_code_block_together() -> None:
    markdown = "# Code\n\n```python\nvalue = 1\nprint(value)\n```\n\nAfter\n"

    chunks = MarkdownChunkingService(max_chars=200).chunk(markdown, DOCUMENT_VERSION_ID)

    code_chunks = [chunk for chunk in chunks if chunk.metadata["contains_code"]]
    assert len(code_chunks) == 1
    assert "```python\nvalue = 1\nprint(value)\n```" in code_chunks[0].content


def test_chunking_rejects_empty_content() -> None:
    with pytest.raises(ChunkingError, match="empty markdown content"):
        MarkdownChunkingService().chunk(" \n\n", DOCUMENT_VERSION_ID)


def test_chunking_produces_unique_anchors_for_duplicate_headings() -> None:
    markdown = "# Same\n\nA\n\n# Same\n\nB\n"

    chunks = MarkdownChunkingService().chunk(markdown, DOCUMENT_VERSION_ID)
    anchors = [chunk.anchor for chunk in chunks]

    assert len(anchors) == len(set(anchors))
    assert anchors == [
        f"dv:{DOCUMENT_VERSION_ID}:c0000",
        f"dv:{DOCUMENT_VERSION_ID}:c0001",
    ]
    assert [chunk.heading_path for chunk in chunks] == [["Same"], ["Same"]]


def test_chunking_is_deterministic_and_hashes_content() -> None:
    markdown = "# A\n\nText\n"
    service = MarkdownChunkingService()

    left = service.chunk(markdown, DOCUMENT_VERSION_ID)
    right = service.chunk(markdown, DOCUMENT_VERSION_ID)

    assert left == right
    assert left[0].content_hash == hash_text(left[0].content)
    assert left[0].token_estimate == 3


def test_chunking_adds_normalized_text_source_anchor() -> None:
    markdown = "# A\n\nText\n"

    chunk = MarkdownChunkingService().chunk(markdown, DOCUMENT_VERSION_ID)[0]

    assert chunk.metadata["source_anchor"] == {
        "type": "text",
        "page": None,
        "paragraph": None,
        "char_start": 0,
        "char_end": len("# A\n\nText"),
    }


def test_chunking_maps_pdf_page_source_anchor() -> None:
    markdown = "<!-- page:3 -->\n\nPDF text\n"

    chunk = MarkdownChunkingService().chunk(
        markdown,
        DOCUMENT_VERSION_ID,
        source_anchor_type="pdf_page",
    )[0]

    assert chunk.metadata["source_anchor"] == {
        "type": "pdf_page",
        "page": 3,
        "paragraph": None,
        "char_start": 0,
        "char_end": len("<!-- page:3 -->\n\nPDF text"),
    }
