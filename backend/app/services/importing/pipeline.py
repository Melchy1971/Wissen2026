class ImportPipeline:
    """Orchestrates parse -> OCR fallback -> normalize -> persist -> chunk -> tag."""

    def run(self, file_bytes: bytes, filename: str, mime_type: str) -> dict:
        raise NotImplementedError("Implemented in M2 task contract")
