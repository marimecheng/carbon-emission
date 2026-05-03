# document_ai.py

import re
from datetime import datetime
from typing import Dict, Optional


def _clean_text(text: str) -> str:
    """
    Fix common PDF extraction artifacts:
    - Merge broken numbers like '1 , 250' -> '1,250'
    - Light keyword cleanup (Date, Energy, Cons)
    """
    text = re.sub(r"Da\s+te", "Date", text, flags=re.IGNORECASE)
    text = re.sub(r"Ener\s+gy", "Energy", text, flags=re.IGNORECASE)
    text = re.sub(r"C\s+ons", "Cons", text, flags=re.IGNORECASE)
    # Remove spaces around commas/dots in numbers: "1 , 250" -> "1,250"
    text = re.sub(r"(\d)\s*([,.])\s*(\d)", r"\1\2\3", text)
    return text


def _num(pattern: str, text: str) -> Optional[float]:
    # Try the provided pattern first
    m = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
    if m:
        try:
            # clean "1 , 250" -> "1250"
            val = m.group(1).replace(" ", "").replace(",", "")
            return float(val)
        except ValueError:
            pass
            
    # Fallback: aggressive search for numbers with spaces/commas near keywords
    # This specifically targets broken OCR numbers like "1 , 2 5 0 . 00"
    # It looks for a sequence of digits/commas/dots/spaces
    match = re.search(r"(\d[\d,\.\s]*\d)", text)
    if match:
         try:
            val = match.group(1).replace(" ", "").replace(",", "")
            return float(val)
         except ValueError:
            pass
            
    return None



def _find_first_match(patterns, text: str):
    for p in patterns:
        m = re.search(p, text, flags=re.IGNORECASE | re.MULTILINE)
        if m:
            return m
    return None


def extract_fields(raw_text: str, image_bytes: bytes | None = None) -> Dict:
    """
    Current implementation: regex-only, robust version.
    (LayoutLM can be added later; for now image_bytes is ignored.)
    """
    cleaned = _clean_text(raw_text)
    lines = [l.strip() for l in cleaned.splitlines() if l.strip()]
    text = cleaned

    fields: Dict = {
        "energy_kwh": None,
        "water_gallons": None,
        "gas_therms": None,
        "fuel_liters": None,
        "distance_km": None,
        "vendor": None,
        "date": None,
    }

    # --- quantities ---
    fields["energy_kwh"] = _num(
        # Allow spaces between digits, commas, and dots
        r"(?:Energy\s+Cons|Electric(?:ity)?(?:\s+usage)?)[^0-9]*([\d\s,]+(?:\.\d+)?)",
        text,
    )

    fields["water_gallons"] = _num(
        r"(?:water(?:\s+usage)?[:\s]+)([\d,]+(?:\.\d+)?)\s*(?:gallons?|gal)", text
    )

    fields["gas_therms"] = _num(
        r"(?:gas|natural\s+gas)[:\s]+(\d+(?:\.\d+)?)\s*(?:therms?|th)", text
    )

    fields["fuel_liters"] = _num(
        r"(?:diesel|petrol|fuel)[:\s]+(\d+(?:\.\d+)?)\s*(?:l|liters?)", text
    )

    fields["distance_km"] = _num(
        r"(?:distance|flight|travel)[:\s]+(\d+(?:\.\d+)?)\s*km", text
    )

    # --- vendor ---
    candidate_vendor = None
    for l in lines[:10]:
        if "[YOUR COMPANY" in l or "Template.net" in l:
            continue
        if l.lower().startswith(("bill to", "invoice", "utility bill")):
            continue
        if "@" in l or "." in l:
            candidate_vendor = l
            break
    if not candidate_vendor:
        for l in lines:
            if "[YOUR COMPANY" in l or "Template.net" in l:
                continue
            if l.lower().startswith(("bill to", "invoice", "utility bill")):
                continue
            candidate_vendor = l
            break
    fields["vendor"] = candidate_vendor

    # --- date ---
    m = _find_first_match(
        [
            r"invoice\s+date[:\s]+([A-Za-z]+\s+\d{1,2},\s*\d{4})",
            r"invoice\s+date[:\s]+(\d{1,2}/\d{1,2}/\d{2,4})",
            r"date[:\s]+([A-Za-z]+\s+\d{1,2},\s*\d{4})",
            r"date[:\s]+(\d{1,2}-\d{1,2}-\d{2,4})",
            r"date[:\s]+(\d{1,2}\s*-\s*[A-Za-z]+\s*-\s*\d{4})",
        ],
        text,
    )

    parsed_date = None
    if m:
        date_str = m.group(1).strip()
        for fmt in ("%B %d, %Y", "%b %d, %Y", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%m-%d-%Y"):
            try:
                parsed_date = datetime.strptime(date_str, fmt).date().isoformat()
                break
            except ValueError:
                continue
        if not parsed_date:
            parsed_date = date_str

    fields["date"] = parsed_date
    return fields
