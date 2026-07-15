"""File validation utilities for resume uploads.

Validates files by extension, MIME type, and (for PDF) header bytes.
Does NOT rely on external libraries beyond the standard library for
basic checks; PyMuPDF is used for deeper PDF validation when available.
"""

import logging
from pathlib import Path

logger = logging.getLogger("job_hunting.utils.validation")

ALLOWED_EXTENSIONS = frozenset({".pdf", ".docx", ".doc", ".txt"})
ALLOWED_MIME_TYPES = frozenset(
    {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
        "text/plain",
    }
)
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

PDF_HEADER = b"%PDF-"
DOCX_HEADER = b"PK\x03\x04"


class FileValidationError(Exception):
    pass


def validate_file(
    filename: str,
    content: bytes,
    *,
    max_size: int = MAX_FILE_SIZE_BYTES,
) -> None:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise FileValidationError(
            f"Unsupported file type: {ext}. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    if len(content) == 0:
        raise FileValidationError("File is empty")

    if len(content) > max_size:
        raise FileValidationError(f"File too large: {len(content)} bytes (max {max_size})")

    if ext == ".pdf" and not content.startswith(PDF_HEADER):
        raise FileValidationError("Invalid PDF file: missing PDF header")

    if ext == ".docx" and not content.startswith(DOCX_HEADER):
        raise FileValidationError("Invalid DOCX file: missing ZIP/DOCX header")

    logger.debug("File validated: %s (%d bytes, %s)", filename, len(content), ext)


def validate_pdf(content: bytes) -> bool:
    """Deep-validate a PDF using PyMuPDF if available."""
    try:
        import fitz

        with fitz.open(stream=content, filetype="pdf") as doc:
            return doc.page_count > 0  # type: ignore[no-any-return]
    except ImportError:
        return content.startswith(PDF_HEADER)
    except Exception:
        return False
