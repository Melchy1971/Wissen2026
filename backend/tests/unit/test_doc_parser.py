import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.models.import_models import ImportRequest
from app.services.parser_service import ConverterNotAvailableError, DocParser, ParserError


DOC_MIME = "application/msword"


def make_request(
    source_bytes: bytes = b"fake doc content",
    filename: str = "document.doc",
) -> ImportRequest:
    return ImportRequest(filename=filename, mime_type=DOC_MIME, source_bytes=source_bytes)


def test_doc_parser_raises_when_converter_not_available() -> None:
    with patch("app.services.parser_service.subprocess.run", side_effect=FileNotFoundError):
        with pytest.raises(ConverterNotAvailableError, match="LibreOffice"):
            DocParser().parse(make_request())


def test_doc_parser_raises_on_conversion_failure() -> None:
    with patch("app.services.parser_service.subprocess.run") as mock_run:
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout=b"LibreOffice 7.0"),
            MagicMock(returncode=1, stderr=b"corrupt input file"),
        ]
        with pytest.raises(ParserError, match="corrupt input file"):
            DocParser().parse(make_request())


def test_doc_parser_raises_when_output_file_missing() -> None:
    with patch("app.services.parser_service.subprocess.run") as mock_run:
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout=b"LibreOffice 7.0"),
            MagicMock(returncode=0, stderr=b""),
        ]
        with pytest.raises(ParserError, match="no output file"):
            DocParser().parse(make_request())


def test_doc_parser_temp_dir_is_deleted_after_conversion_error() -> None:
    recorded: list[Path] = []
    real_td = tempfile.TemporaryDirectory

    class _TrackingTD:
        def __init__(self) -> None:
            self._td = real_td()
            recorded.append(Path(self._td.name))

        def __enter__(self) -> str:
            return self._td.__enter__()

        def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
            self._td.__exit__(exc_type, exc_val, exc_tb)

    with (
        patch("app.services.parser_service.tempfile.TemporaryDirectory", _TrackingTD),
        patch("app.services.parser_service.subprocess.run") as mock_run,
        pytest.raises(ParserError),
    ):
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout=b"LibreOffice 7.0"),
            MagicMock(returncode=1, stderr=b"error"),
        ]
        DocParser().parse(make_request())

    assert recorded, "TemporaryDirectory was never entered"
    assert not recorded[0].exists(), f"Temp dir {recorded[0]} was not cleaned up"
