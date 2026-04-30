from typing import Protocol

from app.models.import_models import ExtractedContent, ImportRequest


class OcrError(Exception):
    pass


class OcrEngine(Protocol):
    name: str
    version: str

    def extract_text(self, request: ImportRequest, parsed: ExtractedContent | None = None) -> ExtractedContent:
        """Run local OCR for scanned content. Implementations must not persist original bytes."""
        ...
