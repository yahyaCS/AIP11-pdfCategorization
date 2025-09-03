import re
from pypdf import PdfReader

def extract_text_from_pdf(path):
    reader = PdfReader(path)
    return "\n\n".join([p.extract_text() or "" for p in reader.pages])

def extract_field(regex, text):
    m = re.search(regex, text, re.I)
    return m.group(1).strip() if m else None

def is_soap(text):
    return all(re.search(h, text, re.I | re.M) for h in [
        r"^\s*S\s*[-–]\s*Subjective\b",
        r"^\s*O\s*[-–]\s*Objective\b",
        r"^\s*A\s*[-–]\s*Assessment\b",
        r"^\s*P\s*[-–]\s*Plan\b"
    ])
