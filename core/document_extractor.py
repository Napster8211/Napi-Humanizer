"""Transient extraction of supported writing documents into bounded plain text."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Iterable
from zipfile import BadZipFile, ZipFile
from xml.etree import ElementTree

from pypdf import PdfReader


SUPPORTED_EXTENSIONS = {".txt", ".md", ".markdown", ".docx", ".pdf"}
MAX_UPLOAD_BYTES = 8 * 1024 * 1024


class DocumentExtractionError(ValueError):
    """Raised when an uploaded document cannot be safely extracted."""


def _normalise_text(parts: Iterable[str]) -> str:
    text = "\n".join(part.replace("\r\n", "\n").replace("\r", "\n") for part in parts)
    lines = [line.rstrip() for line in text.split("\n")]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def _extract_docx(data: bytes) -> str:
    try:
        with ZipFile(BytesIO(data)) as archive:
            xml = archive.read("word/document.xml")
    except (BadZipFile, KeyError, OSError) as exc:
        raise DocumentExtractionError("The DOCX file could not be opened.") from exc

    try:
        root = ElementTree.fromstring(xml)
    except ElementTree.ParseError as exc:
        raise DocumentExtractionError("The DOCX document structure is invalid.") from exc

    paragraphs = []
    current = []
    for node in root.iter():
        tag = node.tag.rsplit("}", 1)[-1]
        if tag == "t" and node.text:
            current.append(node.text)
        elif tag in {"tab", "br", "cr"}:
            current.append("\t" if tag == "tab" else "\n")
        elif tag == "p" and current:
            paragraphs.append("".join(current))
            current = []
    if current:
        paragraphs.append("".join(current))
    return _normalise_text(paragraphs)


def _extract_pdf(data: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(data), strict=False)
        pages = [(page.extract_text() or "") for page in reader.pages]
    except Exception as exc:  # pypdf raises several parser-specific exceptions.
        raise DocumentExtractionError("The PDF could not be read. It may be scanned or encrypted.") from exc
    return _normalise_text(pages)


def extract_document(filename: str, data: bytes) -> str:
    """Extract bounded plain text without persisting the uploaded bytes."""
    suffix = Path(filename or "").suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise DocumentExtractionError("Supported file types are .txt, .md, .docx, and .pdf.")
    if not data:
        raise DocumentExtractionError("The uploaded file is empty.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise DocumentExtractionError("The uploaded file is larger than the 8 MB limit.")

    if suffix in {".txt", ".md", ".markdown"}:
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise DocumentExtractionError("Text files must use UTF-8 encoding.") from exc
    elif suffix == ".docx":
        text = _extract_docx(data)
    else:
        text = _extract_pdf(data)

    text = _normalise_text([text])
    if not text:
        raise DocumentExtractionError("No readable text was found in the uploaded file.")
    return text
