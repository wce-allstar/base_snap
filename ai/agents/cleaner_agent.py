"""
Cleaner Agent — Normalize OCR artifacts.
"""

from __future__ import annotations

import re

from schemas import CleanedText
from agents.base import BaseAgent, PipelineStage


class CleanerAgent(BaseAgent[CleanedText]):
    """Clean and normalize extracted OCR text."""

    def __init__(
        self,
        remove_page_numbers: bool = True,
        remove_headers_footers: bool = True,
        fix_hyphenation: bool = True,
        max_retries: int = 3,
    ):
        super().__init__(PipelineStage.CLEAN, max_retries=max_retries)
        self.remove_page_numbers = remove_page_numbers
        self.remove_headers_footers = remove_headers_footers
        self.fix_hyphenation = fix_hyphenation

    async def _execute(self, raw_text: str) -> CleanedText:
        text = raw_text
        transformations = []

        # 1. Fix hyphenation (words split across lines)
        if self.fix_hyphenation:
            text, count = self._fix_hyphenation(text)
            if count:
                transformations.append(f"fixed_hyphenation:{count}")

        # 2. Remove page numbers (standalone numbers on lines)
        if self.remove_page_numbers:
            text, count = self._remove_page_numbers(text)
            if count:
                transformations.append(f"removed_page_numbers:{count}")

        # 3. Remove headers/footers (repeated patterns at top/bottom of pages)
        if self.remove_headers_footers:
            text, count = self._remove_headers_footers(text)
            if count:
                transformations.append(f"removed_headers_footers:{count}")

        # 4. Normalize whitespace
        text = self._normalize_whitespace(text)
        transformations.append("normalized_whitespace")

        # 5. Fix common OCR artifacts
        text, artifacts = self._fix_ocr_artifacts(text)
        if artifacts:
            transformations.append(f"fixed_artifacts:{artifacts}")

        return CleanedText(text=text.strip(), transformations_applied=transformations)

    def _fix_hyphenation(self, text: str) -> tuple[str, int]:
        """Join hyphenated words split across lines."""
        # Pattern: word- \n word -> wordword
        pattern = re.compile(r"(\w+)-\s*\n\s*(\w+)")
        count = 0

        def repl(match):
            nonlocal count
            count += 1
            return match.group(1) + match.group(2)

        return pattern.sub(repl, text), count

    def _remove_page_numbers(self, text: str) -> tuple[str, int]:
        """Remove standalone page numbers."""
        lines = text.split("\n")
        cleaned = []
        count = 0

        for line in lines:
            stripped = line.strip()
            # Match: just a number, or "Page X", "X of Y", etc.
            if re.match(r"^(page\s+)?\d+(\s+of\s+\d+)?$", stripped, re.IGNORECASE):
                count += 1
                continue
            # Match: number at start/end with only whitespace around
            if re.match(r"^\d+$", stripped) and len(stripped) <= 3:
                count += 1
                continue
            cleaned.append(line)

        return "\n".join(cleaned), count

    def _remove_headers_footers(self, text: str) -> tuple[str, int]:
        """Remove repeated header/footer lines across pages."""
        pages = text.split("\f")  # Form feed = page break
        if len(pages) < 2:
            return text, 0

        # Find lines that appear on every page (likely headers/footers)
        page_lines = [p.split("\n") for p in pages]
        min_lines = min(len(pl) for pl in page_lines)

        header_candidates = set(page_lines[0][:3])
        footer_candidates = set(page_lines[0][-3:])

        for pl in page_lines[1:]:
            header_candidates &= set(pl[:3])
            footer_candidates &= set(pl[-3:])

        # Remove identified headers/footers
        count = 0
        cleaned_pages = []
        for pl in page_lines:
            cleaned = [l for l in pl if l not in header_candidates and l not in footer_candidates]
            count += len(pl) - len(cleaned)
            cleaned_pages.append("\n".join(cleaned))

        return "\f".join(cleaned_pages), count

    def _normalize_whitespace(self, text: str) -> str:
        # Replace form feeds with double newline
        text = text.replace("\f", "\n\n")
        # Collapse multiple blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Collapse spaces/tabs but keep newlines
        text = re.sub(r"[ \t]{2,}", " ", text)
        # Trim trailing spaces on each line
        text = "\n".join(line.rstrip() for line in text.split("\n"))
        return text

    def _fix_ocr_artifacts(self, text: str) -> tuple[str, int]:
        """Fix common OCR misreads."""
        fixes = {
            r"\b(\w) \| (\w)\b": r"\1\2",  # "a | b" -> "ab"
            r"\b(\w) — (\w)\b": r"\1\2",   # em dash between chars
            r"\b(\w) \. (\w)\b": r"\1\2",  # spaced periods
            r"��": "",                      # stray box drawing
            r"[•●������]": "-",               # bullets to dashes
        }
        count = 0
        for pattern, repl in fixes.items():
            new_text, n = re.subn(pattern, repl, text)
            count += n
            text = new_text
        return text, count