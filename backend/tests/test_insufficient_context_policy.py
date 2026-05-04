from datetime import UTC, datetime

from app.schemas.documents import DocumentChunkSourceAnchor
from app.schemas.search import SearchChunkResult
from app.services.chat.citation_mapper import Citation
from app.services.chat.context_builder import ContextBlock, ContextPackage
from app.services.chat.insufficient_context_policy import (
    INSUFFICIENT_CONTEXT_ANSWER,
    DEFAULT_MIN_RETRIEVAL_SCORE,
    DEFAULT_MIN_TOP_CHUNK_CHARS,
    InsufficientContextPolicy,
    InsufficientContextThresholds,
)


def make_search_result(*, chunk_id: str, rank: float, title: str = "Dokument", text_preview: str = "Kontext") -> SearchChunkResult:
    return SearchChunkResult(
        document_id=f"doc-{chunk_id}",
        document_title=title,
        document_created_at=datetime(2026, 5, 1, 10, 0, tzinfo=UTC),
        document_version_id=f"ver-{chunk_id}",
        version_number=1,
        chunk_id=chunk_id,
        position=0,
        text_preview=text_preview,
        source_anchor=DocumentChunkSourceAnchor(type="text", page=None, paragraph=None, char_start=0, char_end=len(text_preview)),
        rank=rank,
        filters={},
    )


def make_context(*, text_one: str, text_two: str | None = None, title_one: str = "Arbeitsvertrag", title_two: str = "Richtlinie") -> ContextPackage:
    blocks = [
        ContextBlock(
            chunk_id="chunk-1",
            document_id="doc-1",
            document_title=title_one,
            source_anchor=DocumentChunkSourceAnchor(type="text", page=None, paragraph=None, char_start=0, char_end=len(text_one)),
            text=text_one,
            rank=0.9,
            char_count=len(text_one),
            token_count=len(text_one.split()),
        )
    ]
    if text_two is not None:
        blocks.append(
            ContextBlock(
                chunk_id="chunk-2",
                document_id="doc-2",
                document_title=title_two,
                source_anchor=DocumentChunkSourceAnchor(type="text", page=None, paragraph=None, char_start=0, char_end=len(text_two)),
                text=text_two,
                rank=0.8,
                char_count=len(text_two),
                token_count=len(text_two.split()),
            )
        )
    return ContextPackage(
        blocks=blocks,
        total_chars=sum(block.char_count for block in blocks),
        total_tokens=sum(block.token_count for block in blocks),
        excluded_chunks=[],
    )


def make_citation(chunk_id: str) -> Citation:
    return Citation(
        chunk_id=chunk_id,
        document_id=f"doc-{chunk_id}",
        document_title=f"Titel {chunk_id}",
        source_anchor=DocumentChunkSourceAnchor(type="text", page=None, paragraph=None, char_start=0, char_end=42),
        quote_preview="Vorschaumaterial",
    )


def test_policy_denies_when_no_retrieval_hits_exist() -> None:
    policy = InsufficientContextPolicy()
    context = ContextPackage(blocks=[], total_chars=0, total_tokens=0, excluded_chunks=[])

    decision = policy.evaluate(question="Welche Frist gilt?", retrieval_results=[], context=context)

    assert decision.sufficient_context is False
    assert decision.reason == "no_retrieval_hits"
    assert decision.answer == INSUFFICIENT_CONTEXT_ANSWER
    assert decision.low_confidence_citations == []


def test_policy_denies_when_max_score_is_below_threshold() -> None:
    policy = InsufficientContextPolicy()
    results = [make_search_result(chunk_id="chunk-1", rank=DEFAULT_MIN_RETRIEVAL_SCORE - 0.01)]
    context = make_context(text_one="Dies ist ein ausreichend langer Kontextblock fuer die Bewertung.")

    decision = policy.evaluate(
        question="Welche Frist gilt?",
        retrieval_results=results,
        context=context,
        low_confidence_citations=[make_citation("chunk-1")],
    )

    assert decision.sufficient_context is False
    assert decision.reason == "max_score_below_threshold"
    assert decision.answer == INSUFFICIENT_CONTEXT_ANSWER
    assert decision.retrieval_score_max == results[0].rank
    assert decision.low_confidence_citations[0].reason == "low_retrieval_score"


def test_policy_denies_when_top_hit_is_too_short() -> None:
    policy = InsufficientContextPolicy()
    results = [make_search_result(chunk_id="chunk-1", rank=0.9, text_preview="Lang genug fuer Retrieval")]
    context = make_context(text_one="zu kurz")

    decision = policy.evaluate(question="Welche Frist gilt?", retrieval_results=results, context=context)

    assert decision.sufficient_context is False
    assert decision.reason == "top_hit_too_short"
    assert decision.answer == INSUFFICIENT_CONTEXT_ANSWER


def test_policy_denies_when_question_is_outside_document_scope() -> None:
    policy = InsufficientContextPolicy()
    results = [make_search_result(chunk_id="chunk-1", rank=0.9)]
    context = make_context(
        text_one=(
            "Der Vertrag regelt Probezeit und Kuendigungsfrist ausfuehrlich, verbindlich und mit "
            "konkreten Fristregeln fuer das Arbeitsverhaeltnis im Unternehmen."
        )
    )

    decision = policy.evaluate(question="Wie hoch ist die Hotelobergrenze fuer Dienstreisen?", retrieval_results=results, context=context)

    assert decision.sufficient_context is False
    assert decision.reason == "question_outside_document_scope"
    assert decision.answer == INSUFFICIENT_CONTEXT_ANSWER


def test_policy_denies_when_sources_conflict_without_resolution() -> None:
    policy = InsufficientContextPolicy()
    results = [
        make_search_result(chunk_id="chunk-1", rank=0.9),
        make_search_result(chunk_id="chunk-2", rank=0.85),
    ]
    context = make_context(
        text_one=(
            "Homeoffice ist erlaubt, wenn Datenschutz, Erreichbarkeit, Dokumentation und Freigabe durch "
            "die Fuehrungskraft gewaehleistet sind."
        ),
        text_two=(
            "Homeoffice ist nicht erlaubt, wenn Datenschutz, Erreichbarkeit, Dokumentation und Freigabe "
            "durch die Fuehrungskraft gewaehleistet sind."
        ),
    )

    decision = policy.evaluate(
        question="Ist Homeoffice erlaubt?",
        retrieval_results=results,
        context=context,
        low_confidence_citations=[make_citation("chunk-1"), make_citation("chunk-2")],
    )

    assert decision.sufficient_context is False
    assert decision.reason == "conflicting_sources_without_resolution"
    assert [item.reason for item in decision.low_confidence_citations] == ["conflicting_sources", "conflicting_sources"]


def test_policy_allows_sufficient_context() -> None:
    policy = InsufficientContextPolicy()
    results = [make_search_result(chunk_id="chunk-1", rank=0.9)]
    context = make_context(
        text_one="Nach der Probezeit gilt eine Kuendigungsfrist von vier Wochen zum Monatsende fuer das Arbeitsverhaeltnis.",
    )

    decision = policy.evaluate(
        question="Welche Kuendigungsfrist gilt nach der Probezeit?",
        retrieval_results=results,
        context=context,
    )

    assert decision.sufficient_context is True
    assert decision.reason is None
    assert decision.answer is None
    assert decision.retrieval_score_max == 0.9
    assert decision.low_confidence_citations == []


def test_policy_uses_custom_thresholds() -> None:
    policy = InsufficientContextPolicy(
        InsufficientContextThresholds(
            min_retrieval_score=0.5,
            min_top_chunk_chars=20,
            min_question_token_length=5,
            min_question_token_overlap=2,
        )
    )
    results = [make_search_result(chunk_id="chunk-1", rank=0.49)]
    context = make_context(text_one="Ein ausreichend langer Kontextblock fuer die Pruefung.")

    decision = policy.evaluate(question="Welche Frist gilt?", retrieval_results=results, context=context)

    assert decision.sufficient_context is False
    assert decision.reason == "max_score_below_threshold"


def test_policy_exposes_default_thresholds_as_stable_contract() -> None:
    thresholds = InsufficientContextThresholds()

    assert thresholds.min_retrieval_score == DEFAULT_MIN_RETRIEVAL_SCORE
    assert thresholds.min_top_chunk_chars == DEFAULT_MIN_TOP_CHUNK_CHARS
    assert thresholds.min_question_token_length == 4
    assert thresholds.min_question_token_overlap == 1