from typing import Protocol


class KiProviderError(Exception):
    pass


class KiProvider(Protocol):
    name: str
    model: str

    def normalize_markdown(self, text: str, metadata: dict) -> str:
        ...
