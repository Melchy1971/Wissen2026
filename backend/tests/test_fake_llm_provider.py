import pytest

from app.core.errors import InsufficientContextApiError, LlmUnavailableApiError
from app.services.chat.fake_llm_provider import (
    FakeLlmProvider,
    FakeLlmProviderTimeoutError,
    FakeLlmProviderUnavailableError,
)

from tests.test_rag_chat_service import make_service


USER_PROMPT_WITH_CHUNKS = """
KONTEXT
[QUELLE 1]
chunk_id: chunk-1
text:
Kontext A

[QUELLE 2]
chunk_id: chunk-2
text:
Kontext B
"""


def test_fake_llm_provider_returns_deterministic_answer_with_sources() -> None:
    provider = FakeLlmProvider()

    answer = provider.generate("system", USER_PROMPT_WITH_CHUNKS)

    assert answer == "Deterministische Testantwort auf Basis der Quellen chunk-1, chunk-2."
    assert provider.calls[0].system_prompt == "system"
    assert provider.calls[0].user_prompt == USER_PROMPT_WITH_CHUNKS


def test_fake_llm_provider_can_simulate_unavailable() -> None:
    provider = FakeLlmProvider(unavailable=True)

    with pytest.raises(FakeLlmProviderUnavailableError, match="fake llm unavailable"):
        provider.generate("system", USER_PROMPT_WITH_CHUNKS)


def test_fake_llm_provider_can_simulate_timeout() -> None:
    provider = FakeLlmProvider(timeout=True)

    with pytest.raises(FakeLlmProviderTimeoutError, match="fake llm timeout"):
        provider.generate("system", USER_PROMPT_WITH_CHUNKS)


def test_fake_llm_provider_can_return_empty_answer() -> None:
    provider = FakeLlmProvider(answer="")

    assert provider.generate("system", USER_PROMPT_WITH_CHUNKS) == ""


def test_fake_llm_provider_can_return_answer_without_sources() -> None:
    provider = FakeLlmProvider(answer="Antwort ohne Quellenreferenz.")

    assert provider.generate("system", USER_PROMPT_WITH_CHUNKS) == "Antwort ohne Quellenreferenz."


def test_rag_pipeline_maps_fake_unavailable_to_llm_unavailable() -> None:
    service, _persistence, _retrieval, _llm = make_service(llm_provider=FakeLlmProvider(unavailable=True))

    with pytest.raises(LlmUnavailableApiError) as exc:
        service.answer_question(
            session_id="session-1",
            workspace_id="workspace-1",
            question="Welche Kuendigungsfrist gilt nach der Probezeit?",
        )

    assert exc.value.code == "LLM_UNAVAILABLE"


def test_rag_pipeline_maps_fake_timeout_to_llm_unavailable() -> None:
    service, _persistence, _retrieval, _llm = make_service(llm_provider=FakeLlmProvider(timeout=True))

    with pytest.raises(LlmUnavailableApiError) as exc:
        service.answer_question(
            session_id="session-1",
            workspace_id="workspace-1",
            question="Welche Kuendigungsfrist gilt nach der Probezeit?",
        )

    assert exc.value.code == "LLM_UNAVAILABLE"


def test_rag_pipeline_rejects_fake_empty_answer() -> None:
    service, _persistence, _retrieval, _llm = make_service(llm_provider=FakeLlmProvider(answer=""))

    with pytest.raises(LlmUnavailableApiError) as exc:
        service.answer_question(
            session_id="session-1",
            workspace_id="workspace-1",
            question="Welche Kuendigungsfrist gilt nach der Probezeit?",
        )

    assert exc.value.code == "LLM_UNAVAILABLE"
    assert exc.value.message == "LLM returned an empty response"


def test_rag_pipeline_rejects_fake_answer_without_sources() -> None:
    service, _persistence, _retrieval, _llm = make_service(
        llm_provider=FakeLlmProvider(answer="Antwort ohne Quellenreferenz.")
    )

    with pytest.raises(InsufficientContextApiError) as exc:
        service.answer_question(
            session_id="session-1",
            workspace_id="workspace-1",
            question="Welche Kuendigungsfrist gilt nach der Probezeit?",
        )

    assert exc.value.code == "INSUFFICIENT_CONTEXT"
    assert exc.value.message == "answer contains no supported citations"
