import hashlib
from dataclasses import dataclass
from typing import Protocol

from app.models.import_models import ExtractedContent, ImportRequest


PARSER_VERSION = "1.0"


class ParserError(Exception):
    pass


class UnsupportedMimeTypeError(ParserError):
    pass


class EmptyContentError(ParserError):
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


def _parser_metadata(
    parser_name: str,
    parser_version: str,
    request: ImportRequest,
    detected_encoding: str,
) -> dict[str, object]:
    return {
        "parser_name": parser_name,
        "parser_version": parser_version,
        "mime_type": request.mime_type,
        "source_filename": request.filename,
        "byte_size": len(request.source_bytes),
        "detected_encoding": detected_encoding,
    }
