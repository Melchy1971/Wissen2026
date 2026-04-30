import hashlib

from app.models.import_models import ExtractedContent, ImportError, ImportRequest, ImportResult
from app.services.markdown_normalizer import MarkdownNormalizer, NormalizationError
from app.services.ocr_service import OcrEngine, OcrError
from app.services.parser_service import ParserError, ParserSelector, UnsupportedMimeTypeError


def content_hash(source_bytes: bytes) -> str:
    return hashlib.sha256(source_bytes).hexdigest()


class ImportService:
    def __init__(
        self,
        parser_selector: ParserSelector,
        normalizer: MarkdownNormalizer,
        ocr_engine: OcrEngine | None = None,
    ) -> None:
        self._parser_selector = parser_selector
        self._normalizer = normalizer
        self._ocr_engine = ocr_engine

    def import_document(self, request: ImportRequest) -> ImportResult:
        source_hash = content_hash(request.source_bytes)
        metadata = {
            "filename": request.filename,
            "mime_type": request.mime_type,
            **request.metadata,
        }

        try:
            parser = self._parser_selector.select_parser(request.mime_type, request.filename)
            extracted = parser.parse(request)
            extracted.source_content_hash = source_hash
            extracted.metadata = {**metadata, **extracted.metadata}
            extracted.parser_name = extracted.parser_name or parser.name
            extracted.parser_version = extracted.parser_version or parser.version
        except UnsupportedMimeTypeError as exc:
            return self._failed_result(request, source_hash, "unsupported_type", "parse", str(exc))
        except ParserError as exc:
            return self._failed_result(request, source_hash, "parser_failed", "parse", str(exc))

        if extracted.ocr_required:
            if self._ocr_engine is None:
                extracted.errors.append(
                    ImportError(
                        code="ocr_failed",
                        stage="ocr",
                        message="OCR required but no OCR engine is configured",
                        recoverable=False,
                    )
                )
                return self._result_from_errors(request, source_hash, extracted)

            try:
                extracted = self._ocr_engine.extract_text(request, extracted)
                extracted.source_content_hash = source_hash
                extracted.metadata = {**metadata, **extracted.metadata}
                extracted.ocr_used = True
            except OcrError as exc:
                extracted.errors.append(
                    ImportError(code="ocr_failed", stage="ocr", message=str(exc), recoverable=False)
                )
                return self._result_from_errors(request, source_hash, extracted)

        try:
            normalized = self._normalizer.normalize(extracted)
        except NormalizationError as exc:
            return self._failed_result(
                request,
                source_hash,
                "normalization_failed",
                "normalize",
                str(exc),
            )

        return ImportResult(
            success=True,
            filename=request.filename,
            mime_type=request.mime_type,
            source_content_hash=source_hash,
            document=normalized,
            errors=extracted.errors,
            metadata=metadata,
        )

    def _failed_result(
        self,
        request: ImportRequest,
        source_hash: str,
        code: str,
        stage: str,
        message: str,
    ) -> ImportResult:
        return ImportResult(
            success=False,
            filename=request.filename,
            mime_type=request.mime_type,
            source_content_hash=source_hash,
            errors=[ImportError(code=code, stage=stage, message=message, recoverable=False)],
        )

    def _result_from_errors(
        self,
        request: ImportRequest,
        source_hash: str,
        extracted: ExtractedContent,
    ) -> ImportResult:
        return ImportResult(
            success=False,
            filename=request.filename,
            mime_type=request.mime_type,
            source_content_hash=source_hash,
            errors=extracted.errors,
            metadata=extracted.metadata,
        )
