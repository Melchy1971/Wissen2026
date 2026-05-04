from app.schemas.documents import DocumentChunkSourceAnchor
from app.services.chat.citation_mapper import CitationMapper, CitationMappingError, QUOTE_PREVIEW_MAX_CHARS
from app.services.chat.context_builder import ContextBlock, ContextPackage


def make_context() -> ContextPackage:
    return ContextPackage(
        blocks=[
            ContextBlock(
                chunk_id="chunk-1",
                document_id="doc-1",
                document_title="Arbeitsvertrag Hybridmodell",
                source_anchor=DocumentChunkSourceAnchor(
                    type="text",
                    page=None,
                    paragraph=None,
                    char_start=120,
                    char_end=240,
                ),
                text="Nach der Probezeit gilt eine Kuendigungsfrist von vier Wochen zum Monatsende.",
                rank=0.91,
                char_count=75,
                token_count=11,
            ),
            ContextBlock(
                chunk_id="chunk-2",
                document_id="doc-2",
                document_title="Reisekostenrichtlinie 2026",
                source_anchor=DocumentChunkSourceAnchor(
                    type="pdf_page",
                    page=3,
                    paragraph=None,
                    char_start=0,
                    char_end=80,
                ),
                text="Hotels werden bis zu einer definierten Obergrenze erstattet.",
                rank=0.73,
                char_count=63,
                token_count=9,
            ),
        ],
        total_chars=138,
        total_tokens=20,
        excluded_chunks=[],
    )


def test_citation_mapper_maps_citations_by_first_use_order() -> None:
    mapper = CitationMapper()
    context = make_context()

    answer = (
        "Zur Reisekostenfrage siehe chunk-2. "
        "Fuer die arbeitsvertragliche Frist ist chunk-1 relevant. "
        "Spaeter wird chunk-2 nochmals erwaehnt."
    )

    citations = mapper.map_citations(answer=answer, context=context)

    assert [citation.chunk_id for citation in citations] == ["chunk-2", "chunk-1"]
    assert citations[0].document_id == "doc-2"
    assert citations[0].document_title == "Reisekostenrichtlinie 2026"
    assert citations[0].source_anchor.type == "pdf_page"


def test_citation_mapper_ignores_unreferenced_context_blocks() -> None:
    mapper = CitationMapper()

    citations = mapper.map_citations(answer="Nur chunk-1 wird referenziert.", context=make_context())

    assert [citation.chunk_id for citation in citations] == ["chunk-1"]


def test_citation_mapper_returns_empty_list_for_answer_without_chunk_references() -> None:
    mapper = CitationMapper()

    citations = mapper.map_citations(answer="Keine explizite Quellenreferenz vorhanden.", context=make_context())

    assert citations == []


def test_citation_mapper_truncates_quote_preview_to_maximum_length() -> None:
    mapper = CitationMapper()
    long_text = "wort " * 100
    context = ContextPackage(
        blocks=[
            ContextBlock(
                chunk_id="chunk-1",
                document_id="doc-1",
                document_title="Langtext",
                source_anchor=DocumentChunkSourceAnchor(
                    type="text",
                    page=None,
                    paragraph=None,
                    char_start=0,
                    char_end=len(long_text),
                ),
                text=long_text,
                rank=0.9,
                char_count=len(long_text),
                token_count=100,
            )
        ],
        total_chars=len(long_text),
        total_tokens=100,
        excluded_chunks=[],
    )

    citations = mapper.map_citations(answer="Bezug auf chunk-1.", context=context)

    assert len(citations[0].quote_preview) == QUOTE_PREVIEW_MAX_CHARS
    assert citations[0].quote_preview.endswith("...")


def test_citation_mapper_rejects_context_block_without_chunk_id() -> None:
    mapper = CitationMapper()
    invalid_context = ContextPackage(
        blocks=[
            ContextBlock(
                chunk_id=" ",
                document_id="doc-1",
                document_title="Invalid",
                source_anchor=DocumentChunkSourceAnchor(
                    type="text",
                    page=None,
                    paragraph=None,
                    char_start=0,
                    char_end=10,
                ),
                text="Gueltiger Textinhalt",
                rank=0.9,
                char_count=20,
                token_count=3,
            )
        ],
        total_chars=20,
        total_tokens=3,
        excluded_chunks=[],
    )

    try:
        mapper.map_citations(answer="chunk-1", context=invalid_context)
    except CitationMappingError as exc:
        assert str(exc) == "context block chunk_id must not be blank"
    else:
        raise AssertionError("CitationMapper should reject context blocks without chunk_id")


def test_citation_mapper_rejects_duplicate_chunk_ids_in_context() -> None:
    mapper = CitationMapper()
    duplicate_context = ContextPackage(
        blocks=[
            ContextBlock(
                chunk_id="chunk-1",
                document_id="doc-1",
                document_title="A",
                source_anchor=DocumentChunkSourceAnchor(type="text", page=None, paragraph=None, char_start=0, char_end=5),
                text="Text A",
                rank=0.9,
                char_count=6,
                token_count=2,
            ),
            ContextBlock(
                chunk_id="chunk-1",
                document_id="doc-2",
                document_title="B",
                source_anchor=DocumentChunkSourceAnchor(type="text", page=None, paragraph=None, char_start=0, char_end=5),
                text="Text B",
                rank=0.8,
                char_count=6,
                token_count=2,
            ),
        ],
        total_chars=12,
        total_tokens=4,
        excluded_chunks=[],
    )

    try:
        mapper.map_citations(answer="chunk-1", context=duplicate_context)
    except CitationMappingError as exc:
        assert str(exc) == "duplicate context block chunk_id: chunk-1"
    else:
        raise AssertionError("CitationMapper should reject duplicate chunk ids in context")