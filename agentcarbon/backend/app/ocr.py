import io

from PIL import Image, UnidentifiedImageError
import PyPDF2
import pytesseract
from pytesseract import TesseractNotFoundError

import os

# Point directly to the exe (same as test_ocr.py) if on Windows locally
if os.name == 'nt':
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def _extract_pdf_text(content: bytes) -> str:
    """Lightweight PDF text extraction using PyPDF2 (avoids image conversion)."""
    reader = PyPDF2.PdfReader(io.BytesIO(content))
    pages = [p.extract_text() or "" for p in reader.pages]
    text = "\n".join(pages).strip()
    if not text:
        raise RuntimeError("Uploaded PDF has no extractable text.")
    return text


def extract_text_from_file(content: bytes) -> str:
    # PDF: detect by header to avoid PIL errors on non-images
    if content.lstrip().startswith(b"%PDF"):
        return _extract_pdf_text(content)

    # Images
    try:
        image = Image.open(io.BytesIO(content)).convert("RGB")
    except UnidentifiedImageError as exc:
        raise RuntimeError(
            "Unsupported file type. Upload a PNG/JPG image or a PDF with text."
        ) from exc

    try:
        text = pytesseract.image_to_string(image)
    except TesseractNotFoundError as exc:
        raise RuntimeError(
            "Tesseract OCR not found. Please install it and/or set TESSERACT_CMD "
            "to the full path of tesseract.exe."
        ) from exc

    return text
