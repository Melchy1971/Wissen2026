from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from pypdf import PdfWriter

from app.models.import_models import ImportRequest
from app.services.parser_service import EmptyContentError, OCR_MIN_CHARS_PER_PAGE, ParserError, PdfParser


PDF_MIME = "application/pdf"


def make_request(source_bytes: bytes = b"%PDF-1.4", filename: str = "document.pdf") -> ImportRequest:
    return ImportRequest(filename=filename, mime_type=PDF_MIME, source_bytes=source_bytes)


def blank_pdf_bytes() -> bytes:
    """Single blank page PDF via pypdf PdfWriter."""
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    buf = BytesIO()
    writer.write(buf)
    return buf.getvalue()


def _mock_reader(pages_text: list[str]) -> MagicMock:
    mock_pages = []
    for text in pages_text:
        page = MagicMock()
        page.extract_text.return_value = text
        mock_pages.append(page)
    reader = MagicMock()
    reader.pages = mock_pages
    return reader


def test_pdf_parser_extracts_text_from_single_page() -> None:
    page_text = "x" * 200
    with patch("app.services.parser_service.PdfReader", return_value=_mock_reader([page_text])):
        result = PdfParser().parse(make_request())

    assert page_text in result.text
    assert "<!-- page:1 -->" in result.text
    assert result.metadata["page_count"] == 1
    assert result.metadata["extraction_method"] == "text"
    assert result.metadata["total_chars_extracted"] == 200
    assert result.parser_name == "pdf-parser"
    assert result.ocr_required is False


def test_pdf_parser_includes_page_markers_for_each_page() -> None:
    pages = ["x" * 100, "y" * 100, "z" * 100]
    with patch("app.services.parser_service.PdfReader", return_value=_mock_reader(pages)):
        result = PdfParser().parse(make_request())

    assert "<!-- page:1 -->" in result.text
    assert "<!-- page:2 -->" in result.text
    assert "<!-- page:3 -->" in result.text
    assert result.metadata["page_count"] == 3


def test_pdf_parser_page_markers_appear_before_page_text() -> None:
    with patch("app.services.parser_service.PdfReader", return_value=_mock_reader(["First page", "Second page"])):
        result = PdfParser().parse(make_request())

    pos_marker1 = result.text.index("<!-- page:1 -->")
    pos_text1 = result.text.index("First page")
    pos_marker2 = result.text.index("<!-- page:2 -->")
    pos_text2 = result.text.index("Second page")

    assert pos_marker1 < pos_text1 < pos_marker2 < pos_text2


def test_pdf_parser_sets_ocr_required_when_text_is_sparse() -> None:
    sparse_text = "abc"  # 3 chars, well below OCR_MIN_CHARS_PER_PAGE
    assert len(sparse_text) < OCR_MIN_CHARS_PER_PAGE
    with patch("app.services.parser_service.PdfReader", return_value=_mock_reader([sparse_text])):
        result = PdfParser().parse(make_request())

    assert result.ocr_required is True
    assert result.metadata["ocr_required"] is True


def test_pdf_parser_does_not_set_ocr_required_for_sufficient_text() -> None:
    rich_text = "x" * OCR_MIN_CHARS_PER_PAGE
    with patch("app.services.parser_service.PdfReader", return_value=_mock_reader([rich_text])):
        result = PdfParser().parse(make_request())

    assert result.ocr_required is False


def test_pdf_parser_sets_ocr_required_when_all_pages_are_blank() -> None:
    with patch("app.services.parser_service.PdfReader", return_value=_mock_reader(["", ""])):
        result = PdfParser().parse(make_request())

    assert result.ocr_required is True
    assert result.metadata["total_chars_extracted"] == 0


def test_pdf_parser_includes_page_markers_even_for_empty_pages() -> None:
    with patch("app.services.parser_service.PdfReader", return_value=_mock_reader(["", ""])):
        result = PdfParser().parse(make_request())

    assert "<!-- page:1 -->" in result.text
    assert "<!-- page:2 -->" in result.text


def test_pdf_parser_rejects_corrupted_pdf() -> None:
    with pytest.raises(ParserError, match="could not be opened"):
        PdfParser().parse(make_request(source_bytes=b"not a pdf"))


def test_pdf_parser_rejects_pdf_with_no_pages() -> None:
    mock_reader = MagicMock()
    mock_reader.pages = []
    with patch("app.services.parser_service.PdfReader", return_value=mock_reader):
        with pytest.raises(ParserError, match="no pages"):
            PdfParser().parse(make_request())


def test_pdf_parser_records_required_metadata() -> None:
    with patch("app.services.parser_service.PdfReader", return_value=_mock_reader(["x" * 100])):
        result = PdfParser().parse(make_request(filename="report.pdf"))

    assert result.metadata["source_filename"] == "report.pdf"
    assert result.metadata["mime_type"] == PDF_MIME
    assert result.metadata["byte_size"] == len(b"%PDF-1.4")
    assert result.metadata["parser_name"] == "pdf-parser"
    assert result.metadata["parser_version"] == "1.0"


def test_pdf_parser_survives_page_extraction_failure() -> None:
    """A page that raises during extract_text is treated as blank, not a crash."""
    failing_page = MagicMock()
    failing_page.extract_text.side_effect = Exception("decode error")
    good_page = MagicMock()
    good_page.extract_text.return_value = "x" * 200

    mock_reader = MagicMock()
    mock_reader.pages = [failing_page, good_page]

    with patch("app.services.parser_service.PdfReader", return_value=mock_reader):
        result = PdfParser().parse(make_request())

    assert "<!-- page:1 -->" in result.text
    assert "<!-- page:2 -->" in result.text
    assert "x" * 200 in result.text


def test_pdf_parser_blank_page_pdf_sets_ocr_required() -> None:
    """End-to-end with a real PDF that has no text (pypdf PdfWriter produces blank pages)."""
    pdf_bytes = blank_pdf_bytes()
    result = PdfParser().parse(make_request(source_bytes=pdf_bytes))

    assert result.ocr_required is True
    assert result.metadata["page_count"] == 1
    assert result.metadata["total_chars_extracted"] == 0
