from app.schemas.documents import DocumentChunkSourceAnchor
from app.services.chat.context_builder import ContextBlock, ContextPackage
from app.services.chat.prompt_builder import (
    DEFAULT_PROMPT_TEMPLATE_VERSION,
    PromptBuildError,
    PromptBuilder,
    SYSTEM_PROMPT_TEMPLATE,
)


def make_context_package() -> ContextPackage:
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


def test_prompt_builder_builds_deterministic_prompt_with_question_and_context() -> None:
    builder = PromptBuilder()

    prompt = builder.build(
        question="Welche Kuendigungsfrist gilt nach der Probezeit?",
        context=make_context_package(),
    )

    assert prompt.template_version == DEFAULT_PROMPT_TEMPLATE_VERSION
    assert prompt.system_prompt == SYSTEM_PROMPT_TEMPLATE
    assert prompt.question == "Welche Kuendigungsfrist gilt nach der Probezeit?"
    assert prompt.source_chunk_ids == ["chunk-1", "chunk-2"]
    assert "FRAGE\nWelche Kuendigungsfrist gilt nach der Probezeit?" in prompt.user_prompt
    assert "[QUELLE 1]" in prompt.rendered_context
    assert "chunk_id: chunk-1" in prompt.rendered_context
    assert "document_id: doc-1" in prompt.rendered_context
    assert "document_title: Arbeitsvertrag Hybridmodell" in prompt.rendered_context
    assert "source_anchor: type=text; page=null; paragraph=null; char_start=120; char_end=240" in prompt.rendered_context
    assert "Nach der Probezeit gilt eine Kuendigungsfrist" in prompt.rendered_context
    assert "[QUELLE 2]" in prompt.rendered_context


def test_prompt_builder_is_byte_stable_for_same_inputs() -> None:
    builder = PromptBuilder()
    context = make_context_package()

    left = builder.build(question="Frage?", context=context)
    right = builder.build(question="Frage?", context=context)

    assert left == right


def test_prompt_builder_renders_empty_context_marker() -> None:
    builder = PromptBuilder()
    empty_context = ContextPackage(blocks=[], total_chars=0, total_tokens=0, excluded_chunks=[])

    prompt = builder.build(question="Was ist die Kuendigungsfrist?", context=empty_context)

    assert prompt.rendered_context == "<kein verwertbarer Kontext verfuegbar>"
    assert "KONTEXT\n<kein verwertbarer Kontext verfuegbar>" in prompt.user_prompt
    assert prompt.source_chunk_ids == []


def test_prompt_builder_keeps_context_order() -> None:
    builder = PromptBuilder()
    context = make_context_package()

    prompt = builder.build(question="Frage?", context=context)

    first_index = prompt.rendered_context.index("chunk_id: chunk-1")
    second_index = prompt.rendered_context.index("chunk_id: chunk-2")
    assert first_index < second_index


def test_prompt_builder_rejects_blank_question() -> None:
    builder = PromptBuilder()

    try:
        builder.build(question="   ", context=make_context_package())
    except PromptBuildError as exc:
        assert str(exc) == "question must not be blank"
    else:
        raise AssertionError("PromptBuilder should reject blank questions")


def test_prompt_builder_rejects_blank_template_version() -> None:
    try:
        PromptBuilder(template_version="   ")
    except PromptBuildError as exc:
        assert str(exc) == "template_version must not be blank"
    else:
        raise AssertionError("PromptBuilder should reject blank template versions")