from __future__ import annotations

from dataclasses import dataclass
import re

from app.schemas.search import SearchChunkResult
from app.services.chat.citation_mapper import Citation
from app.services.chat.context_builder import ContextPackage


INSUFFICIENT_CONTEXT_ANSWER = "Dazu liegen in den vorhandenen Dokumenten keine ausreichenden Informationen vor."
DEFAULT_MIN_RETRIEVAL_SCORE = 0.25
DEFAULT_MIN_TOP_CHUNK_CHARS = 80
DEFAULT_MIN_QUESTION_TOKEN_LENGTH = 4
DEFAULT_MIN_QUESTION_TOKEN_OVERLAP = 1
CONTRADICTION_NEGATION_TOKENS = {"kein", "keine", "keinen", "nicht", "nie", "ohne"}
QUESTION_SCOPE_STOPWORDS = {
    "aber",
    "alle",
    "auch",
    "dabei",
    "daher",
    "dann",
    "dass",
    "dem",
    "den",
    "der",
    "des",
    "die",
    "eine",
    "einen",
    "einer",
    "eines",
    "fuer",
    "gelt",
    "hoch",
    "info",
    "ist",
    "kein",
    "keine",
    "mehr",
    "nach",
    "oder",
    "sind",
    "ueber",
    "und",
    "von",
    "warum",
    "weder",
    "welche",
    "welcher",
    "welches",
    "wenn",
    "wird",
    "wie",
    "wieviel",
    "wo",
    "womit",
    "zur",
}


@dataclass(frozen=True)
class InsufficientContextThresholds:
    min_retrieval_score: float = DEFAULT_MIN_RETRIEVAL_SCORE
    min_top_chunk_chars: int = DEFAULT_MIN_TOP_CHUNK_CHARS
    min_question_token_length: int = DEFAULT_MIN_QUESTION_TOKEN_LENGTH
    min_question_token_overlap: int = DEFAULT_MIN_QUESTION_TOKEN_OVERLAP


@dataclass(frozen=True)
class LowConfidenceCitation:
    citation: Citation
    reason: str


@dataclass(frozen=True)
class InsufficientContextDecision:
    sufficient_context: bool
    reason: str | None
    answer: str | None
    retrieval_score_max: float | None
    retrieval_score_avg: float | None
    low_confidence_citations: list[LowConfidenceCitation]


class InsufficientContextPolicy:
    def __init__(self, thresholds: InsufficientContextThresholds | None = None) -> None:
        self._thresholds = thresholds or InsufficientContextThresholds()

    def evaluate(
        self,
        *,
        question: str,
        retrieval_results: list[SearchChunkResult],
        context: ContextPackage,
        low_confidence_citations: list[Citation] | None = None,
    ) -> InsufficientContextDecision:
        scores = [result.rank for result in retrieval_results]
        retrieval_score_max = max(scores) if scores else None
        retrieval_score_avg = (sum(scores) / len(scores)) if scores else None
        supporting_citations = list(low_confidence_citations or [])

        if not retrieval_results:
            return self._deny(
                reason="no_retrieval_hits",
                retrieval_score_max=retrieval_score_max,
                retrieval_score_avg=retrieval_score_avg,
                low_confidence_citations=[],
            )

        if retrieval_score_max is None or retrieval_score_max < self._thresholds.min_retrieval_score:
            return self._deny(
                reason="max_score_below_threshold",
                retrieval_score_max=retrieval_score_max,
                retrieval_score_avg=retrieval_score_avg,
                low_confidence_citations=self._mark_low_confidence(supporting_citations, "low_retrieval_score"),
            )

        top_context_block = context.blocks[0] if context.blocks else None
        if top_context_block is None or top_context_block.char_count < self._thresholds.min_top_chunk_chars:
            return self._deny(
                reason="top_hit_too_short",
                retrieval_score_max=retrieval_score_max,
                retrieval_score_avg=retrieval_score_avg,
                low_confidence_citations=self._mark_low_confidence(supporting_citations, "top_hit_too_short"),
            )

        if self._question_outside_document_scope(question=question, context=context):
            return self._deny(
                reason="question_outside_document_scope",
                retrieval_score_max=retrieval_score_max,
                retrieval_score_avg=retrieval_score_avg,
                low_confidence_citations=self._mark_low_confidence(supporting_citations, "outside_document_scope"),
            )

        if self._has_unresolved_contradiction(context):
            return self._deny(
                reason="conflicting_sources_without_resolution",
                retrieval_score_max=retrieval_score_max,
                retrieval_score_avg=retrieval_score_avg,
                low_confidence_citations=self._mark_low_confidence(supporting_citations, "conflicting_sources"),
            )

        return InsufficientContextDecision(
            sufficient_context=True,
            reason=None,
            answer=None,
            retrieval_score_max=retrieval_score_max,
            retrieval_score_avg=retrieval_score_avg,
            low_confidence_citations=[],
        )

    def _deny(
        self,
        *,
        reason: str,
        retrieval_score_max: float | None,
        retrieval_score_avg: float | None,
        low_confidence_citations: list[LowConfidenceCitation],
    ) -> InsufficientContextDecision:
        return InsufficientContextDecision(
            sufficient_context=False,
            reason=reason,
            answer=INSUFFICIENT_CONTEXT_ANSWER,
            retrieval_score_max=retrieval_score_max,
            retrieval_score_avg=retrieval_score_avg,
            low_confidence_citations=low_confidence_citations,
        )

    def _mark_low_confidence(
        self,
        citations: list[Citation],
        reason: str,
    ) -> list[LowConfidenceCitation]:
        return [LowConfidenceCitation(citation=citation, reason=reason) for citation in citations]

    def _question_outside_document_scope(self, *, question: str, context: ContextPackage) -> bool:
        question_tokens = self._significant_tokens(question)
        if not question_tokens:
            return False

        context_tokens: set[str] = set()
        for block in context.blocks:
            context_tokens.update(self._significant_tokens(block.text))
            context_tokens.update(self._significant_tokens(block.document_title))

        overlap = question_tokens.intersection(context_tokens)
        return len(overlap) < self._thresholds.min_question_token_overlap

    def _has_unresolved_contradiction(self, context: ContextPackage) -> bool:
        if len(context.blocks) < 2:
            return False

        first = context.blocks[0]
        second = context.blocks[1]
        first_tokens = self._significant_tokens(first.text)
        second_tokens = self._significant_tokens(second.text)
        shared_tokens = first_tokens.intersection(second_tokens)
        if not shared_tokens:
            return False

        first_has_negation = self._contains_negation(first.text)
        second_has_negation = self._contains_negation(second.text)
        return first_has_negation != second_has_negation

    def _contains_negation(self, text: str) -> bool:
        return any(token in CONTRADICTION_NEGATION_TOKENS for token in self._tokens(text))

    def _significant_tokens(self, text: str) -> set[str]:
        return {
            token
            for token in self._tokens(text)
            if len(token) >= self._thresholds.min_question_token_length and token not in QUESTION_SCOPE_STOPWORDS
        }

    def _tokens(self, text: str) -> list[str]:
        return re.findall(r"[a-zA-Z0-9_aeoeuessAEIOU]+", text.lower())