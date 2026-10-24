"""Document parser adapter."""

from app.document_parser import extract_text


class DocumentMaterialAdapter:
    def __call__(self, filename: str, raw: bytes, max_chars: int) -> str:
        return extract_text(filename, raw, max_chars)
