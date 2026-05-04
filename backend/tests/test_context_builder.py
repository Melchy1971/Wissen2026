from datetime import UTC, datetime

import pytest

from app.schemas.documents import DocumentChunkSourceAnchor
from app.schemas.search import SearchChunkResult
from app.services.chat.context_builder import ContextBuildError, ContextBuilder


def make_result(
    *,
    chunk_id: str,
    rank: float,
    text_preview: str,
    document_title: str = "Document",
) -> SearchChunkResult:
    return SearchChunkResult(
        document_id=f"doc-{chunk_id}",
        document_title=document_title,
        document_created_at=datetime(2026, 5, 1, 10, 0, tzinfo=UTC),
        document_version_id=f"ver-{chunk_id}",
        version_number=1,
        chunk_id=chunk_id,
        position=0,
        text_preview=text_preview,
        source_anchor=DocumentChunkSourceAnchor(
            type="text",
            page=None,
            paragraph=None,
            char_start=0,
            char_end=len(text_preview),
        ),
        rank=rank,
        filters={},
    )


def test_context_builder_builds_package_in_ranking_order() -> None:
    builder = ContextBuilder(max_context_chars=500, max_context_tokens=100, min_chunk_chars=20)
    results = [
        make_result(chunk_id="chunk-1", rank=0.9, text_preview="Alpha content with enough words for context"),
        make_result(chunk_id="chunk-2", rank=0.7, text_preview="Beta content with enough words for context"),
    ]

    package = builder.build(results)

    assert [block.chunk_id for block in package.blocks] == ["chunk-1", "chunk-2"]
    assert package.blocks[0].document_id == "doc-chunk-1"
    assert package.blocks[0].document_title == "Document"
    assert package.blocks[0].source_anchor.type == "text"
    assert package.blocks[0].text == "Alpha content with enough words for context"
    assert package.total_chars == sum(block.char_count for block in package.blocks)
    assert package.total_tokens == sum(block.token_count for block in package.blocks)


def test_context_builder_deduplicates_chunk_ids_and_keeps_first_ranked_occurrence() -> None:
    builder = ContextBuilder(max_context_chars=500, max_context_tokens=100, min_chunk_chars=10)
    results = [
        make_result(chunk_id="chunk-1", rank=0.9, text_preview="First ranked content"),
        make_result(chunk_id="chunk-1", rank=0.2, text_preview="Lower ranked duplicate content"),
    ]

    package = builder.build(results)

    assert [block.chunk_id for block in package.blocks] == ["chunk-1"]
    assert package.blocks[0].text == "First ranked content"
    assert len(package.excluded_chunks) == 1
    assert package.excluded_chunks[0].chunk_id == "chunk-1"
    assert package.excluded_chunks[0].reason == "duplicate_chunk"


def test_context_builder_uses_full_chunk_text_when_available() -> None:
    builder = ContextBuilder(max_context_chars=500, max_context_tokens=100, min_chunk_chars=20)
    result = make_result(chunk_id="chunk-1", rank=0.9, text_preview="Short preview only")

    package = builder.build(
        [result],
        chunk_text_by_id={"chunk-1": "Full chunk text with enough words to exceed the minimum length."},
    )

    assert package.blocks[0].text == "Full chunk text with enough words to exceed the minimum length."


def test_context_builder_excludes_empty_and_very_short_chunks() -> None:
    builder = ContextBuilder(max_context_chars=500, max_context_tokens=100, min_chunk_chars=15)
    results = [
        make_result(chunk_id="chunk-1", rank=0.9, text_preview="   "),
        make_result(chunk_id="chunk-2", rank=0.8, text_preview="too short"),
        make_result(chunk_id="chunk-3", rank=0.7, text_preview="This chunk is long enough to survive."),
    ]

    package = builder.build(results)

    assert [block.chunk_id for block in package.blocks] == ["chunk-3"]
    assert [(item.chunk_id, item.reason) for item in package.excluded_chunks] == [
        ("chunk-1", "chunk_too_short"),
        ("chunk-2", "chunk_too_short"),
    ]


def test_context_builder_respects_char_limit_without_losing_kept_source_information() -> None:
    builder = ContextBuilder(max_context_chars=55, max_context_tokens=100, min_chunk_chars=10)
    results = [
        make_result(chunk_id="chunk-1", rank=0.9, text_preview="1234567890 1234567890 1234567890"),
        make_result(chunk_id="chunk-2", rank=0.8, text_preview="abcdefghij abcdefghij abcdefghij"),
        make_result(chunk_id="chunk-3", rank=0.7, text_preview="short but acceptable chunk text"),
    ]

    package = builder.build(results)

    assert [block.chunk_id for block in package.blocks] == ["chunk-1"]
    assert package.blocks[0].source_anchor.char_end == len(results[0].text_preview)
    assert [(item.chunk_id, item.reason) for item in package.excluded_chunks] == [
        ("chunk-2", "context_char_limit"),
        ("chunk-3", "context_char_limit"),
    ]


def test_context_builder_respects_token_limit_and_can_include_smaller_later_chunk() -> None:
    builder = ContextBuilder(max_context_chars=500, max_context_tokens=8, min_chunk_chars=5)
    results = [
        make_result(chunk_id="chunk-1", rank=0.9, text_preview="one two three four"),
        make_result(chunk_id="chunk-2", rank=0.8, text_preview="five six seven eight nine"),
        make_result(chunk_id="chunk-3", rank=0.7, text_preview="ten eleven"),
    ]

    package = builder.build(results)

    assert [block.chunk_id for block in package.blocks] == ["chunk-1", "chunk-3"]
    assert [(item.chunk_id, item.reason) for item in package.excluded_chunks] == [
        ("chunk-2", "context_token_limit"),
    ]
    assert package.total_tokens <= 8


def test_context_builder_excludes_single_chunk_that_exceeds_hard_limits() -> None:
    builder = ContextBuilder(max_context_chars=20, max_context_tokens=3, min_chunk_chars=5)
    results = [
        make_result(chunk_id="chunk-1", rank=0.9, text_preview="one two three four five"),
    ]

    package = builder.build(results)

    assert package.blocks == []
    assert [(item.chunk_id, item.reason) for item in package.excluded_chunks] == [
        ("chunk-1", "chunk_exceeds_context_limit"),
    ]


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"max_context_chars": 0, "max_context_tokens": 10}, "max_context_chars must be positive"),
        ({"max_context_chars": 10, "max_context_tokens": 0}, "max_context_tokens must be positive"),
        (
            {"max_context_chars": 10, "max_context_tokens": 10, "min_chunk_chars": 0},
            "min_chunk_chars must be positive",
        ),
    ],
)
def test_context_builder_rejects_invalid_configuration(kwargs: dict, message: str) -> None:
    with pytest.raises(ContextBuildError, match=message):
        ContextBuilder(**kwargs)