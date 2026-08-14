"""File handling: upload persistence and PDF text extraction."""

import os
from datetime import datetime

from ..database.connection import UPLOAD_FOLDER

try:
    from pypdf import PdfReader
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False


def save_upload(file, filename):
    """Save an uploaded file (Werkzeug FileStorage) and return its path."""
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    safe_name = os.path.basename(filename)
    file_path = os.path.join(UPLOAD_FOLDER, safe_name)
    file.save(file_path)
    return file_path


def extract_text(path):
    """Best-effort text extraction for PDFs (pypdf). Returns '' otherwise."""
    if not path.lower().endswith('.pdf') or not HAS_PYPDF:
        return ""
    try:
        reader = PdfReader(path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        return f"Error extracting text from PDF: {str(e)}"


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")