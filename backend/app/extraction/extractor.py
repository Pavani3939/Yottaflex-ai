"""
YottaPay AI – Invoice Extraction Service
=========================================
Handles extraction of invoice fields from:
  1. PDF files (via PyMuPDF)
  2. Image files (via Tesseract OCR)
  3. Gemini API (AI-assisted, optional)
  4. Manual entry (passthrough)

Falls back gracefully if AI unavailable.
Never exposes API keys; reads from environment.
"""
import io
import json
import re
from pathlib import Path
from typing import Optional

from loguru import logger

from app.config import get_settings

settings = get_settings()


# ---------------------------------------------------------------------------
# Extracted Fields Schema (plain dict for flexibility)
# ---------------------------------------------------------------------------
def empty_extracted_fields() -> dict:
    return {
        "invoice_number": None,
        "invoice_date": None,
        "vendor_name": None,
        "vendor_id": None,
        "po_number": None,
        "lines": [],
        "subtotal": None,
        "tax_amount": None,
        "total_amount": None,
        "currency": "INR",
        "confidence": 0.0,
        "extraction_method": None,
        "raw_text": "",
    }


# ---------------------------------------------------------------------------
# PDF Extraction via PyMuPDF
# ---------------------------------------------------------------------------
def extract_from_pdf(file_bytes: bytes) -> dict:
    """Extract text from a PDF and parse invoice fields."""
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(stream=file_bytes, filetype="pdf")
        raw_text = ""
        for page in doc:
            raw_text += page.get_text()
        doc.close()

        fields = _parse_text_to_fields(raw_text)
        fields["extraction_method"] = "PYMUPDF"
        fields["raw_text"] = raw_text
        logger.info(f"PDF extracted: {len(raw_text)} chars")
        return fields

    except ImportError:
        logger.warning("PyMuPDF not installed. Falling back to OCR.")
        return extract_from_image(file_bytes)
    except Exception as exc:
        logger.error(f"PDF extraction failed: {exc}")
        return empty_extracted_fields()


# ---------------------------------------------------------------------------
# Image Extraction via Tesseract OCR
# ---------------------------------------------------------------------------
def extract_from_image(file_bytes: bytes) -> dict:
    """Extract text from an image using Tesseract OCR."""
    try:
        import pytesseract
        from PIL import Image

        image = Image.open(io.BytesIO(file_bytes))
        raw_text = pytesseract.image_to_string(image)

        fields = _parse_text_to_fields(raw_text)
        fields["extraction_method"] = "TESSERACT_OCR"
        fields["raw_text"] = raw_text
        logger.info(f"OCR extracted: {len(raw_text)} chars")
        return fields

    except ImportError:
        logger.warning("pytesseract/Pillow not installed. Manual entry required.")
        return empty_extracted_fields()
    except Exception as exc:
        logger.error(f"OCR extraction failed: {exc}")
        return empty_extracted_fields()


# ---------------------------------------------------------------------------
# Gemini AI Extraction (optional)
# ---------------------------------------------------------------------------
def extract_with_gemini(raw_text: str) -> dict:
    """
    Use Gemini API to extract structured invoice fields from raw text.
    Falls back to rule-based extraction if API key not configured.
    """
    if not settings.GEMINI_API_KEY:
        logger.info("GEMINI_API_KEY not set. Using rule-based extraction.")
        return _parse_text_to_fields(raw_text)

    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(settings.GEMINI_MODEL)

        prompt = f"""
Extract the following fields from this invoice text and return as valid JSON only.
Do not include any explanation. Return only the JSON object.

Fields to extract:
- invoice_number (string)
- invoice_date (string, YYYY-MM-DD format)
- vendor_name (string)
- po_number (string or null)
- subtotal (number)
- tax_amount (number)
- total_amount (number)
- currency (string, default "INR")
- lines (array of objects with: description, sku, quantity, unit_price, tax_rate, line_total)

Invoice text:
{raw_text[:4000]}
"""
        response = model.generate_content(prompt)
        response_text = response.text.strip()

        # Clean markdown code fences if present
        if response_text.startswith("```"):
            response_text = re.sub(r"```(?:json)?", "", response_text).strip()

        extracted = json.loads(response_text)
        extracted["extraction_method"] = "GEMINI_AI"
        extracted["raw_text"] = raw_text
        extracted["confidence"] = 85.0  # AI extraction confidence estimate
        logger.info("Gemini extraction successful.")
        return extracted

    except Exception as exc:
        logger.warning(f"Gemini extraction failed ({exc}). Falling back to rule-based.")
        result = _parse_text_to_fields(raw_text)
        result["extraction_method"] = "PYMUPDF"
        return result


# ---------------------------------------------------------------------------
# Rule-Based Text Parser (deterministic fallback)
# ---------------------------------------------------------------------------
def _parse_text_to_fields(raw_text: str) -> dict:
    """
    Extract invoice fields from raw text using regex patterns.
    Returns partially filled dict — user edits the rest.
    """
    fields = empty_extracted_fields()

    # Invoice number patterns
    inv_patterns = [
        r"Invoice\s*(?:No|Number|#)[:\s]*([A-Z0-9/\-]+)",
        r"INV[/\-]([A-Z0-9/\-]+)",
        r"Bill\s*No[:\s]*([A-Z0-9/\-]+)",
    ]
    for pattern in inv_patterns:
        m = re.search(pattern, raw_text, re.IGNORECASE)
        if m:
            fields["invoice_number"] = m.group(1).strip()
            break

    # Date patterns
    date_patterns = [
        r"Invoice\s*Date[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        r"Date[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        r"Date[:\s]*(\d{4}-\d{2}-\d{2})",
    ]
    for pattern in date_patterns:
        m = re.search(pattern, raw_text, re.IGNORECASE)
        if m:
            fields["invoice_date"] = _normalise_date(m.group(1))
            break

    # PO number
    po_m = re.search(r"PO\s*(?:No|Number|#)?[:\s]*([A-Z0-9\-]+)", raw_text, re.IGNORECASE)
    if po_m:
        fields["po_number"] = po_m.group(1).strip()

    # Total amount
    total_m = re.search(r"(?:Grand\s*)?Total[:\s]*(?:INR|₹|Rs\.?)?\s*([\d,]+\.?\d*)", raw_text, re.IGNORECASE)
    if total_m:
        fields["total_amount"] = float(total_m.group(1).replace(",", ""))

    # Tax amount
    tax_m = re.search(r"(?:GST|Tax|VAT)[:\s]*(?:INR|₹|Rs\.?)?\s*([\d,]+\.?\d*)", raw_text, re.IGNORECASE)
    if tax_m:
        fields["tax_amount"] = float(tax_m.group(1).replace(",", ""))

    # Subtotal
    sub_m = re.search(r"(?:Sub\s*Total|Net\s*Amount)[:\s]*(?:INR|₹|Rs\.?)?\s*([\d,]+\.?\d*)", raw_text, re.IGNORECASE)
    if sub_m:
        fields["subtotal"] = float(sub_m.group(1).replace(",", ""))

    # Confidence: proportion of fields extracted
    filled = sum(1 for v in [
        fields["invoice_number"], fields["invoice_date"],
        fields["total_amount"]
    ] if v is not None)
    fields["confidence"] = round(filled / 3 * 60, 1)  # max 60% for rule-based

    return fields


def _normalise_date(date_str: str) -> Optional[str]:
    """Convert various date formats to YYYY-MM-DD."""
    from datetime import datetime
    formats = ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y", "%d-%m-%y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return date_str


# ---------------------------------------------------------------------------
# Main Dispatcher
# ---------------------------------------------------------------------------
def extract_invoice(
    file_bytes: bytes,
    file_type: str,
    use_gemini: bool = True,
) -> dict:
    """
    Main extraction dispatcher.

    Args:
        file_bytes: Raw file content.
        file_type: "PDF", "JPEG", "PNG", "TIFF".
        use_gemini: If True and API key set, use Gemini for post-processing.

    Returns:
        Extracted fields dict.
    """
    if file_type.upper() == "PDF":
        fields = extract_from_pdf(file_bytes)
    else:
        fields = extract_from_image(file_bytes)

    # Try Gemini enhancement if we have raw text
    if use_gemini and fields.get("raw_text") and settings.GEMINI_API_KEY:
        gemini_fields = extract_with_gemini(fields["raw_text"])
        # Merge: use Gemini values where rule-based failed
        for key, val in gemini_fields.items():
            if val and not fields.get(key):
                fields[key] = val
        fields["extraction_method"] = "GEMINI_AI"

    return fields
