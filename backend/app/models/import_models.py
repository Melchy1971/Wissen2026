from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


ImportStage = Literal["request", "parse", "ocr", "normalize", "hash", "persist"]
ImportErrorCode = Literal[
    "unsupported_type",
    "parser_failed",
    "ocr_failed",
    "normalization_failed",
    "empty_content",
]


class ImportError(BaseModel):
    code: ImportErrorCode
    stage: ImportStage
    message: str
    recoverable: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class ImportRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    filename: str
    mime_type: str
    source_bytes: bytes = Field(repr=False, exclude=True)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExtractedContent(BaseModel):
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    parser_name: str | None = None
    parser_version: str | None = None
    ocr_required: bool = False
    ocr_used: bool = False
    source_content_hash: str | None = None
    errors: list[ImportError] = Field(default_factory=list)


class NormalizedDocument(BaseModel):
    normalized_markdown: str
    markdown_hash: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    parser_version: str | None = None
    ocr_used: bool = False
    ki_provider: str | None = None
    ki_model: str | None = None
    fallback_used: bool = False


class ImportResult(BaseModel):
    success: bool
    filename: str
    mime_type: str
    source_content_hash: str | None = None
    document: NormalizedDocument | None = None
    errors: list[ImportError] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
