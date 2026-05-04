import hashlib
import subprocess
import tempfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Protocol

from docx import Document
from docx.document import Document as DocxDocument
from docx.table import Table
from docx.text.paragraph import Paragraph
from pypdf import PdfReader

from app.models.import_models import ExtractedContent, ImportRequest


PARSER_VERSION = "1.0"
OCR_MIN_CHARS_PER_PAGE = 50


class ParserError(Exception):
    pass


class UnsupportedMimeTypeError(ParserError):
    pass


class EmptyContentError(ParserError):
    pass


class ConverterNotAvailableError(ParserError):
    pass


class Parser(Protocol):
    name: str
    version: str
    supported_mime_types: set[str]

    def parse(self, request: ImportRequest) -> ExtractedContent:
        """Extract text from a transient file payload without storing the original bytes."""
        ...


class ParserSelector(Protocol):
    def select_parser(self, mime_type: str, filename: str) -> Parser:
        ...


class StaticParserSelector:
    def __init__(self, parsers: list[Parser]) -> None:
        self._parsers = parsers

    def select_parser(self, mime_type: str, filename: str) -> Parser:
        for parser in self._parsers:
            if mime_type in parser.supported_mime_types:
                return parser
        raise UnsupportedMimeTypeError(f"No parser registered for MIME type: {mime_type}")


def source_hash(source_bytes: bytes) -> str:
    return hashlib.sha256(source_bytes).hexdigest()


def decode_text(source_bytes: bytes) -> tuple[str, str]:
    for encoding in ("utf-8-sig", "utf-8"):
        try:
            return source_bytes.decode(encoding), encoding
        except UnicodeDecodeError:
            continue

    try:
        return source_bytes.decode("cp1252"), "cp1252"
    except UnicodeDecodeError:
        return source_bytes.decode("latin-1"), "latin-1"


@dataclass(frozen=True)
class TextParser:
    name: str = "txt-parser"
    version: str = PARSER_VERSION
    supported_mime_types: set[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.supported_mime_types is None:
            object.__setattr__(self, "supported_mime_types", {"text/plain"})

    def parse(self, request: ImportRequest) -> ExtractedContent:
        text, encoding = decode_text(request.source_bytes)
        if not text.strip():
            raise EmptyContentError("Text file does not contain importable content")

        return ExtractedContent(
            text=text,
            metadata=_parser_metadata(self.name, self.version, request, encoding),
            parser_name=self.name,
            parser_version=self.version,
            source_content_hash=source_hash(request.source_bytes),
        )


@dataclass(frozen=True)
class MarkdownParser:
    name: str = "markdown-parser"
    version: str = PARSER_VERSION
    supported_mime_types: set[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.supported_mime_types is None:
            object.__setattr__(
                self,
                "supported_mime_types",
                {"text/markdown", "text/x-markdown", "text/md"},
            )

    def parse(self, request: ImportRequest) -> ExtractedContent:
        markdown, encoding = decode_text(request.source_bytes)
        if not markdown.strip():
            raise EmptyContentError("Markdown file does not contain importable content")

        return ExtractedContent(
            text=markdown,
            metadata=_parser_metadata(self.name, self.version, request, encoding),
            parser_name=self.name,
            parser_version=self.version,
            source_content_hash=source_hash(request.source_bytes),
        )


@dataclass(frozen=True)
class DocxParser:
    name: str = "docx-parser"
    version: str = PARSER_VERSION
    supported_mime_types: set[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.supported_mime_types is None:
            object.__setattr__(
                self,
                "supported_mime_types",
                {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
            )

    def parse(self, request: ImportRequest) -> ExtractedContent:
        try:
            document = Document(BytesIO(request.source_bytes))
        except Exception as exc:
            raise ParserError("DOCX file could not be opened") from exc

        markdown_blocks: list[str] = []
        paragraph_count = 0
        table_count = 0

        for block in iter_docx_blocks(document):
            if isinstance(block, Paragraph):
                markdown = paragraph_to_markdown(block)
                if markdown:
                    markdown_blocks.append(markdown)
                    paragraph_count += 1
            elif isinstance(block, Table):
                markdown = table_to_markdown(block)
                if markdown:
                    markdown_blocks.append(markdown)
                    table_count += 1

        markdown = "\n\n".join(markdown_blocks).strip()
        if not markdown:
            raise EmptyContentError("DOCX file does not contain importable content")

        metadata = _parser_metadata(self.name, self.version, request, detected_encoding=None)
        metadata["table_count"] = table_count
        metadata["paragraph_count"] = paragraph_count

        return ExtractedContent(
            text=markdown + "\n",
            metadata=metadata,
            parser_name=self.name,
            parser_version=self.version,
            source_content_hash=source_hash(request.source_bytes),
        )


def _parser_metadata(
    parser_name: str,
    parser_version: str,
    request: ImportRequest,
    detected_encoding: str | None,
) -> dict[str, object]:
    metadata: dict[str, object] = {
        "parser_name": parser_name,
        "parser_version": parser_version,
        "mime_type": request.mime_type,
        "source_filename": request.filename,
        "byte_size": len(request.source_bytes),
    }
    if detected_encoding is not None:
        metadata["detected_encoding"] = detected_encoding
    return metadata


def iter_docx_blocks(document: DocxDocument):
    body = document.element.body
    for child in body.iterchildren():
        if child.tag.endswith("}p"):
            yield Paragraph(child, document._body)
        elif child.tag.endswith("}tbl"):
            yield Table(child, document._body)


def paragraph_to_markdown(paragraph: Paragraph) -> str:
    text = paragraph.text.strip()
    if not text:
        return ""

    style_name = paragraph.style.name if paragraph.style is not None else ""
    heading_level = heading_level_from_style(style_name)
    if heading_level is not None:
        return f"{'#' * heading_level} {text}"

    if is_list_paragraph(paragraph):
        return f"- {text}"

    return text


def heading_level_from_style(style_name: str) -> int | None:
    lowered = style_name.lower()
    if not (lowered.startswith("heading") or lowered.startswith("überschrift")):
        return None

    for token in reversed(style_name.split()):
        if token.isdigit():
            return min(max(int(token), 1), 6)
    return 1


def is_list_paragraph(paragraph: Paragraph) -> bool:
    style_name = paragraph.style.name.lower() if paragraph.style is not None else ""
    if "list" in style_name or "liste" in style_name:
        return True
    paragraph_properties = paragraph._p.pPr
    return paragraph_properties is not None and paragraph_properties.numPr is not None


def table_to_markdown(table: Table) -> str:
    rows = [[cell_text(cell.text) for cell in row.cells] for row in table.rows]
    rows = [row for row in rows if any(cell.strip() for cell in row)]
    if not rows:
        return ""

    column_count = max(len(row) for row in rows)
    normalized_rows = [row + [""] * (column_count - len(row)) for row in rows]
    header = normalized_rows[0]
    separator = ["---"] * column_count
    body = normalized_rows[1:]

    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(separator) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in body)
    return "\n".join(lines)


def cell_text(text: str) -> str:
    return text.replace("|", "\\|").replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>").strip()


@dataclass(frozen=True)
class DocParser:
    name: str = "doc-parser"
    version: str = PARSER_VERSION
    supported_mime_types: set[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.supported_mime_types is None:
            object.__setattr__(self, "supported_mime_types", {"application/msword"})

    def _find_libreoffice(self) -> str | None:
        for cmd in ("soffice", "libreoffice"):
            try:
                result = subprocess.run([cmd, "--version"], capture_output=True, timeout=10)
                if result.returncode == 0:
                    return cmd
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        return None

    def parse(self, request: ImportRequest) -> ExtractedContent:
        libreoffice = self._find_libreoffice()
        if libreoffice is None:
            raise ConverterNotAvailableError(
                "LibreOffice is required to import .doc files but was not found on this system. "
                "Install LibreOffice and ensure 'soffice' is available on the PATH."
            )

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_doc = Path(tmpdir) / "input.doc"
            tmp_doc.write_bytes(request.source_bytes)

            try:
                result = subprocess.run(
                    [libreoffice, "--headless", "--convert-to", "docx", "--outdir", tmpdir, str(tmp_doc)],
                    capture_output=True,
                    timeout=60,
                )
            except subprocess.TimeoutExpired as exc:
                raise ParserError("LibreOffice conversion timed out") from exc

            if result.returncode != 0:
                stderr = result.stderr.decode("utf-8", errors="replace").strip()
                detail = f": {stderr}" if stderr else ""
                raise ParserError(f".doc conversion failed{detail}")

            tmp_docx = Path(tmpdir) / "input.docx"
            if not tmp_docx.exists():
                raise ParserError("LibreOffice produced no output file for the .doc conversion")

            docx_bytes = tmp_docx.read_bytes()

        docx_request = ImportRequest(
            filename=Path(request.filename).with_suffix(".docx").name,
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            source_bytes=docx_bytes,
        )
        extracted = DocxParser().parse(docx_request)

        metadata = dict(extracted.metadata)
        metadata["source_filename"] = request.filename
        metadata["mime_type"] = request.mime_type
        metadata["byte_size"] = len(request.source_bytes)
        metadata["converter_used"] = libreoffice

        return ExtractedContent(
            text=extracted.text,
            metadata=metadata,
            parser_name=self.name,
            parser_version=self.version,
            source_content_hash=source_hash(request.source_bytes),
        )


@dataclass(frozen=True)
class PdfParser:
    name: str = "pdf-parser"
    version: str = PARSER_VERSION
    supported_mime_types: set[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.supported_mime_types is None:
            object.__setattr__(self, "supported_mime_types", {"application/pdf"})

    def parse(self, request: ImportRequest) -> ExtractedContent:
        try:
            reader = PdfReader(BytesIO(request.source_bytes))
        except Exception as exc:
            raise ParserError("PDF file could not be opened") from exc

        page_count = len(reader.pages)
        if page_count == 0:
            raise ParserError("PDF file contains no pages")

        sections: list[str] = []
        total_chars = 0

        for page_num, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text() or ""
            except Exception:
                page_text = ""
            page_text = page_text.strip()
            total_chars += len(page_text)

            section = f"<!-- page:{page_num} -->"
            if page_text:
                section += f"\n\n{page_text}"
            sections.append(section)

        markdown = "\n\n".join(sections)
        ocr_required = total_chars < page_count * OCR_MIN_CHARS_PER_PAGE

        metadata = _parser_metadata(self.name, self.version, request, detected_encoding=None)
        metadata["page_count"] = page_count
        metadata["extraction_method"] = "text"
        metadata["total_chars_extracted"] = total_chars
        metadata["ocr_required"] = ocr_required

        return ExtractedContent(
            text=markdown + "\n",
            metadata=metadata,
            parser_name=self.name,
            parser_version=self.version,
            ocr_required=ocr_required,
            source_content_hash=source_hash(request.source_bytes),
        )
