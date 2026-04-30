import hashlib
from typing import Protocol

from app.models.import_models import ExtractedContent, ImportError, NormalizedDocument
from app.services.ki_provider import KiProvider, KiProviderError

DETERMINISTIC_NORMALIZER_VERSION = "1.0"


class NormalizationError(Exception):
    pass


class MarkdownNormalizer(Protocol):
    def normalize(self, extracted: ExtractedContent) -> NormalizedDocument:
        ...


def markdown_hash(markdown: str) -> str:
    return hashlib.sha256(markdown.encode("utf-8")).hexdigest()


def normalize_markdown_text(markdown: str) -> tuple[str, dict[str, object]]:
    text = markdown.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    normalized_lines: list[str] = []
    in_fenced_code = False
    blank_pending = False
    changed = text != markdown
    removed_blank_lines = 0

    for line in lines:
        if _is_fence_line(line):
            normalized_line = line.rstrip()
            in_fenced_code = not in_fenced_code
        elif in_fenced_code:
            normalized_line = line.rstrip()
        else:
            normalized_line = line.strip()

        if normalized_line != line:
            changed = True

        if not in_fenced_code and normalized_line == "":
            if blank_pending:
                removed_blank_lines += 1
                changed = True
                continue
            blank_pending = True
        else:
            blank_pending = False

        normalized_lines.append(normalized_line)

    while normalized_lines and normalized_lines[0] == "":
        normalized_lines.pop(0)
        changed = True
    while normalized_lines and normalized_lines[-1] == "":
        normalized_lines.pop()
        changed = True

    normalized = "\n".join(normalized_lines)
    if normalized:
        normalized += "\n"
        if not text.endswith("\n"):
            changed = True

    metadata = {
        "normalizer_name": "deterministic-markdown-normalizer",
        "normalizer_version": DETERMINISTIC_NORMALIZER_VERSION,
        "line_endings": "lf",
        "trimmed_line_edges": True,
        "collapsed_blank_lines": True,
        "removed_extra_blank_lines": removed_blank_lines,
        "ensured_final_newline": bool(normalized),
        "changed": changed,
    }
    return normalized, metadata


def _is_fence_line(line: str) -> bool:
    stripped = line.lstrip()
    return stripped.startswith("```") or stripped.startswith("~~~")


class DeterministicMarkdownNormalizer:
    name = "deterministic-markdown-normalizer"
    version = DETERMINISTIC_NORMALIZER_VERSION

    def normalize(self, extracted: ExtractedContent) -> NormalizedDocument:
        normalized_markdown, normalization_metadata = normalize_markdown_text(extracted.text)
        if not normalized_markdown.strip():
            raise NormalizationError("Cannot normalize empty markdown content")

        metadata = {
            **extracted.metadata,
            "normalization_metadata": normalization_metadata,
        }

        return NormalizedDocument(
            normalized_markdown=normalized_markdown,
            markdown_hash=markdown_hash(normalized_markdown),
            metadata=metadata,
            parser_version=extracted.parser_version,
            ocr_used=extracted.ocr_used,
            fallback_used=False,
        )


class KiMarkdownNormalizer:
    def __init__(
        self,
        provider: KiProvider | None = None,
        fallback_normalizer: MarkdownNormalizer | None = None,
    ) -> None:
        self._provider = provider
        self._fallback_normalizer = fallback_normalizer or DeterministicMarkdownNormalizer()

    def normalize(self, extracted: ExtractedContent) -> NormalizedDocument:
        metadata = dict(extracted.metadata)

        if not extracted.text.strip():
            raise NormalizationError("Cannot normalize empty extracted content")

        if self._provider is None:
            document = self._fallback_normalizer.normalize(extracted)
            document.fallback_used = True
            return document

        try:
            markdown = self._provider.normalize_markdown(extracted.text, metadata)
            fallback_used = False
        except KiProviderError as exc:
            metadata.setdefault("normalization_errors", []).append(
                ImportError(
                    code="normalization_failed",
                    stage="normalize",
                    message=str(exc),
                    recoverable=True,
                ).model_dump()
            )
            fallback_extracted = extracted.model_copy(update={"metadata": metadata})
            document = self._fallback_normalizer.normalize(fallback_extracted)
            document.fallback_used = True
            return document

        if not markdown.strip():
            raise NormalizationError("Normalizer returned empty markdown")

        normalized_markdown, normalization_metadata = normalize_markdown_text(markdown)
        metadata["normalization_metadata"] = normalization_metadata

        return NormalizedDocument(
            normalized_markdown=normalized_markdown,
            markdown_hash=markdown_hash(normalized_markdown),
            metadata=metadata,
            parser_version=extracted.parser_version,
            ocr_used=extracted.ocr_used,
            ki_provider=self._provider.name,
            ki_model=self._provider.model,
            fallback_used=fallback_used,
        )
