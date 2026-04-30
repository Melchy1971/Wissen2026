import pytest

from app.models.import_models import ExtractedContent
from app.services.markdown_normalizer import (
    DeterministicMarkdownNormalizer,
    NormalizationError,
    markdown_hash,
)


def normalize(text: str):
    return DeterministicMarkdownNormalizer().normalize(ExtractedContent(text=text))


def test_normalizer_preserves_markdown_tables() -> None:
    source = "  | Name | Wert |  \n| --- | ---: |\n| Alpha | 42 |\n"

    result = normalize(source)

    assert result.normalized_markdown == "| Name | Wert |\n| --- | ---: |\n| Alpha | 42 |\n"


def test_normalizer_preserves_code_block_content() -> None:
    source = "```python\r\n  value = 1\r\n  print(value)  \r\n```\r\n"

    result = normalize(source)

    assert result.normalized_markdown == "```python\n  value = 1\n  print(value)\n```\n"


def test_normalizer_preserves_headings_and_lists() -> None:
    source = "  # Titel  \n\n  - Punkt A  \n  - Punkt B\n"

    result = normalize(source)

    assert result.normalized_markdown == "# Titel\n\n- Punkt A\n- Punkt B\n"


def test_normalizer_converts_windows_line_endings() -> None:
    result = normalize("# Titel\r\n\r\nText\r\n")

    assert result.normalized_markdown == "# Titel\n\nText\n"
    assert result.metadata["normalization_metadata"]["line_endings"] == "lf"


def test_normalizer_collapses_multiple_blank_lines_and_adds_final_newline() -> None:
    result = normalize("A\n\n\n\nB")

    assert result.normalized_markdown == "A\n\nB\n"
    assert result.metadata["normalization_metadata"]["removed_extra_blank_lines"] == 2
    assert result.metadata["normalization_metadata"]["ensured_final_newline"] is True


def test_normalizer_rejects_empty_content() -> None:
    with pytest.raises(NormalizationError, match="empty markdown content"):
        normalize(" \n\t\n")


def test_normalizer_hash_is_stable_for_equivalent_input() -> None:
    left = normalize("A\r\n\r\nB")
    right = normalize(" A\n\nB\n")

    assert left.normalized_markdown == right.normalized_markdown
    assert left.markdown_hash == right.markdown_hash
    assert left.markdown_hash == markdown_hash("A\n\nB\n")
