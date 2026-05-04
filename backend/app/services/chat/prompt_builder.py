from __future__ import annotations

from dataclasses import dataclass

from app.services.chat.context_builder import ContextPackage


DEFAULT_PROMPT_TEMPLATE_VERSION = "rag-doc-answer-v1"

SYSTEM_PROMPT_TEMPLATE = """Du bist ein Assistent fuer dokumentgestuetzte Antworten.

Systemregeln:
- Antworte nur auf Basis des bereitgestellten Kontexts.
- Wenn der Kontext fuer eine belastbare Antwort nicht ausreicht, sage explizit: \"Auf Basis des bereitgestellten Kontexts ist keine belastbare Antwort moeglich.\"
- Jede fachliche Aussage muss auf Quellen aus dem Kontext zurueckfuehrbar sein.
- Erfinde keine Details.
- Verwende keine Informationen ausserhalb des bereitgestellten Kontexts.
- Wenn du antwortest, stuetze dich ausschliesslich auf die bereitgestellten Quellenbloeke.
"""


class PromptBuildError(ValueError):
    pass


@dataclass(frozen=True)
class PromptPackage:
    template_version: str
    system_prompt: str
    user_prompt: str
    rendered_context: str
    question: str
    source_chunk_ids: list[str]


class PromptBuilder:
    def __init__(self, *, template_version: str = DEFAULT_PROMPT_TEMPLATE_VERSION) -> None:
        if not template_version.strip():
            raise PromptBuildError("template_version must not be blank")
        self._template_version = template_version.strip()

    def build(self, *, question: str, context: ContextPackage) -> PromptPackage:
        normalized_question = question.strip()
        if not normalized_question:
            raise PromptBuildError("question must not be blank")

        rendered_context = self._render_context(context)
        user_prompt = self._render_user_prompt(question=normalized_question, rendered_context=rendered_context)

        return PromptPackage(
            template_version=self._template_version,
            system_prompt=SYSTEM_PROMPT_TEMPLATE,
            user_prompt=user_prompt,
            rendered_context=rendered_context,
            question=normalized_question,
            source_chunk_ids=[block.chunk_id for block in context.blocks],
        )

    def _render_user_prompt(self, *, question: str, rendered_context: str) -> str:
        return (
            "AUFGABE\n"
            "Beantworte die Frage nur anhand des bereitgestellten Kontexts. "
            "Wenn der Kontext nicht ausreicht, antworte exakt mit dem vorgesehenen Hinweis auf fehlende belastbare Grundlage.\n\n"
            f"FRAGE\n{question}\n\n"
            "KONTEXT\n"
            f"{rendered_context}\n"
        )

    def _render_context(self, context: ContextPackage) -> str:
        if not context.blocks:
            return "<kein verwertbarer Kontext verfuegbar>"

        rendered_blocks: list[str] = []
        for index, block in enumerate(context.blocks, start=1):
            rendered_blocks.append(
                "\n".join(
                    [
                        f"[QUELLE {index}]",
                        f"chunk_id: {block.chunk_id}",
                        f"document_id: {block.document_id}",
                        f"document_title: {block.document_title}",
                        f"source_anchor: {self._format_source_anchor(block.source_anchor)}",
                        "text:",
                        block.text,
                    ]
                )
            )
        return "\n\n".join(rendered_blocks)

    def _format_source_anchor(self, source_anchor) -> str:
        parts = [f"type={source_anchor.type}"]
        parts.append(f"page={self._format_optional_int(source_anchor.page)}")
        parts.append(f"paragraph={self._format_optional_int(source_anchor.paragraph)}")
        parts.append(f"char_start={self._format_optional_int(source_anchor.char_start)}")
        parts.append(f"char_end={self._format_optional_int(source_anchor.char_end)}")
        return "; ".join(parts)

    def _format_optional_int(self, value: int | None) -> str:
        return "null" if value is None else str(value)