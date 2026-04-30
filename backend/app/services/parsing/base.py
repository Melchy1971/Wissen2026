from dataclasses import dataclass

@dataclass(frozen=True)
class ParsedDocument:
    text: str
    metadata: dict
    ocr_required: bool = False

class ParserError(Exception):
    pass
