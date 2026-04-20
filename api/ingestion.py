import pdfplumber
import re
from pathlib import Path
from typing import List, Dict

SECTION_PATTERNS = {
    "debt_incurrence": [
        r"(?i)^section\s+[\d\.]+[^\n]*?(incurrence of (indebtedness|debt)|debt incurrence)",
    ],
    "restricted_payments": [
        r"(?i)^section\s+[\d\.]+[^\n]*?restricted payments",
    ],
    "asset_sales": [
        r"(?i)^section\s+[\d\.]+[^\n]*?asset sales?",
    ],
    "collateral_guarantees": [
        r"(?i)^section\s+[\d\.]+[^\n]*?(collateral and guarantees?|collateral[^,\n]*guarantee)",
    ],
    "amendment_voting": [
        r"(?i)^section\s+[\d\.]+[^\n]*?(amendments?.*waivers?|waivers?.*amendments?)",
    ],
}

def extract_text_from_pdf(filepath: str) -> str:
    text = []
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)
    return "\n".join(text)

def clean_text(raw: str) -> str:
    text = re.sub(r'\f', '\n', raw)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'(?m)^\s*\d{1,3}\s*$', '', text)
    return text.strip()

def segment_clauses(text: str) -> List[Dict]:
    clauses = []
    lines = text.split('\n')
    current_type = None
    buffer = []

    for line in lines:
        matched = False
        for ctype, patterns in SECTION_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, line):
                    if current_type and buffer:
                        clauses.append({
                            "clause_type": current_type,
                            "raw_text": " ".join(buffer).strip()
                        })
                    current_type = ctype
                    buffer = [line]
                    matched = True
                    break
            if matched:
                break
        if not matched and current_type:
            buffer.append(line)

    if current_type and buffer:
        clauses.append({
            "clause_type": current_type,
            "raw_text": " ".join(buffer).strip()
        })

    return clauses

def ingest_document(filepath: str) -> List[Dict]:
    if filepath.endswith('.pdf'):
        raw = extract_text_from_pdf(filepath)
    else:
        raw = Path(filepath).read_text(encoding='utf-8', errors='ignore')
    clean = clean_text(raw)
    return segment_clauses(clean)
