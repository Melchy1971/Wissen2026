from __future__ import annotations

import re
from dataclasses import dataclass


class FakeLlmProviderUnavailableError(RuntimeError):
    pass


class FakeLlmProviderTimeoutError(TimeoutError):
    pass


@dataclass(frozen=True)
class FakeLlmCall:
    system_prompt: str
    user_prompt: str


class FakeLlmProvider:
    def __init__(
        self,
        *,
        answer: str | None = None,
        unavailable: bool = False,
        timeout: bool = False,
    ) -> None:
        self.answer = answer
        self.unavailable = unavailable
        self.timeout = timeout
        self.calls: list[FakeLlmCall] = []

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        self.calls.append(FakeLlmCall(system_prompt=system_prompt, user_prompt=user_prompt))
        if self.timeout:
            raise FakeLlmProviderTimeoutError("fake llm timeout")
        if self.unavailable:
            raise FakeLlmProviderUnavailableError("fake llm unavailable")
        if self.answer is not None:
            return self.answer
        return self._deterministic_answer(user_prompt)

    def _deterministic_answer(self, user_prompt: str) -> str:
        chunk_ids = self._extract_chunk_ids(user_prompt)
        if not chunk_ids:
            return "Auf Basis des bereitgestellten Kontexts ist keine belastbare Antwort moeglich."
        sources = ", ".join(chunk_ids)
        return f"Deterministische Testantwort auf Basis der Quellen {sources}."

    def _extract_chunk_ids(self, user_prompt: str) -> list[str]:
        seen: set[str] = set()
        chunk_ids: list[str] = []
        for match in re.finditer(r"^chunk_id:\s*(\S+)\s*$", user_prompt, flags=re.MULTILINE):
            chunk_id = match.group(1).strip()
            if chunk_id and chunk_id not in seen:
                seen.add(chunk_id)
                chunk_ids.append(chunk_id)
        return chunk_ids
