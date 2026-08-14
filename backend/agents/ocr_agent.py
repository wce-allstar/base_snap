"""OCR Agent.

Input : { "file_path": "/path/to/sheet.pdf" } (+ prompt, client)
Output: { "raw_text": "..." }

Milestone 1: extracting readable text from an answer sheet.
"""

import mimetypes
import os


def ocr_agent(file_path, prompt, client):
    """Run OCR on a PDF/image via the Gemini vision model.

    Returns {"raw_text": str}. Raises ValueError if the file is missing
    or has an unsupported type.
    """
    if not os.path.exists(file_path):
        raise ValueError(f"OCR file not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    mime_map = {
        '.pdf': 'application/pdf',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.webp': 'image/webp',
    }
    mime_type = mime_map.get(ext) or mimetypes.guess_type(file_path)[0]
    if not mime_type:
        raise ValueError(f"Unsupported OCR file type: {ext}")

    text = client.generate_with_file(prompt, file_path, mime_type)
    return {"raw_text": (text or "").strip()}


if __name__ == "__main__":
    import sys
    from .base import LLMClient

    api_key = os.environ.get("GEMINI_API_KEY", None)
    target = sys.argv[1] if len(sys.argv) > 1 else "sample_student_paper.pdf"
    if not api_key:
        print("Set GEMINI_API_KEY to run OCR.", file=sys.stderr)
        sys.exit(1)

    result = ocr_agent(target, "Extract all text from this answer sheet.", LLMClient(api_key=api_key))
    print(result["raw_text"])