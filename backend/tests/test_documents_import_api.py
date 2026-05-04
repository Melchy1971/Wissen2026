from io import BytesIO

from fastapi.testclient import TestClient
from pypdf import PdfWriter

from app.main import app


def test_import_rejects_unsupported_file_type() -> None:
    client = TestClient(app)

    response = client.post(
        "/documents/import",
        files={"file": ("scan.rtf", b"{\\rtf1 unsupported}", "application/rtf")},
    )

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "UNSUPPORTED_FILE_TYPE"
    assert response.json()["error"]["message"] == "Only .txt, .md, .docx, .doc and .pdf uploads are supported"


def test_import_returns_parser_failed_for_broken_pdf() -> None:
    client = TestClient(app)

    response = client.post(
        "/documents/import",
        files={"file": ("broken.pdf", b"%PDF-1.7", "application/pdf")},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "PARSER_FAILED"


def test_import_returns_ocr_required_for_scanned_pdf_without_ocr_engine() -> None:
    client = TestClient(app)
    buffer = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.write(buffer)

    response = client.post(
        "/documents/import",
        files={"file": ("scan.pdf", buffer.getvalue(), "application/pdf")},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "OCR_REQUIRED"
