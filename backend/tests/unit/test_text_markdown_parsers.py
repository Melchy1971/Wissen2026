import hashlib

import pytest

from app.models.import_models import ImportRequest
from app.services.parser_service import EmptyContentError, MarkdownParser, TextParser


def make_request(filename: str, mime_type: str, source_bytes: bytes) -> ImportRequest:
    return ImportRequest(filename=filename, mime_type=mime_type, source_bytes=source_bytes)


def test_txt_parser_extracts_markdown_compatible_text() -> None:
    source = "Erste Zeile\n\n- Punkt A\n- Punkt B".encode("utf-8")
    parsed = TextParser().parse(make_request("notes.txt", "text/plain", source))

    assert parsed.text == "Erste Zeile\n\n- Punkt A\n- Punkt B"
    assert parsed.parser_name == "txt-parser"
    assert parsed.metadata["mime_type"] == "text/plain"
    assert parsed.metadata["source_filename"] == "notes.txt"
    assert parsed.metadata["byte_size"] == len(source)
    assert parsed.source_content_hash == hashlib.sha256(source).hexdigest()


def test_markdown_parser_preserves_tables_unchanged() -> None:
    markdown = (
        "# Report\n\n"
        "| Name | Wert |\n"
        "| --- | ---: |\n"
        "| Alpha | 42 |\n"
    )
    source = markdown.encode("utf-8")

    parsed = MarkdownParser().parse(make_request("report.md", "text/markdown", source))

    assert parsed.text == markdown
    assert "| Name | Wert |" in parsed.text
    assert "| Alpha | 42 |" in parsed.text
    assert parsed.parser_name == "markdown-parser"


def test_empty_txt_file_fails_controlled() -> None:
    with pytest.raises(EmptyContentError, match="does not contain importable content"):
        TextParser().parse(make_request("empty.txt", "text/plain", b" \r\n\t "))


def test_parser_preserves_special_characters() -> None:
    text = "Umlaute: äöü ÄÖÜ ß; Euro: €; Gedankenstrich: –"
    parsed = TextParser().parse(make_request("sonderzeichen.txt", "text/plain", text.encode("utf-8")))

    assert parsed.text == text
    assert parsed.metadata["detected_encoding"] in {"utf-8", "utf-8-sig"}


def test_parser_uses_controlled_encoding_fallback() -> None:
    source = "Preis: 10€".encode("cp1252")

    parsed = TextParser().parse(make_request("fallback.txt", "text/plain", source))

    assert parsed.text == "Preis: 10€"
    assert parsed.metadata["detected_encoding"] == "cp1252"
