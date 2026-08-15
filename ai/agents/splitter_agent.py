"""
Splitter Agent — Segment cleaned text into QuestionPackets.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher

from schemas import QuestionPacket, QuestionPaper, QuestionMeta
from agents.base import BaseAgent, AgentError, PipelineStage
from schemas import ErrorCode


class SplitterAgent(BaseAgent[list[QuestionPacket]]):
    """Split cleaned text into individual question/answer packets."""

    def __init__(
        self,
        strict_matching: bool = True,
        min_answer_length: int = 10,
        max_retries: int = 1,
    ):
        super().__init__(PipelineStage.SPLIT, max_retries=max_retries)
        self.strict_matching = strict_matching
        self.min_answer_length = min_answer_length

    async def _execute(self, input_data: tuple[str, QuestionPaper | None]) -> list[QuestionPacket]:
        clean_text, question_paper = input_data

        if not clean_text.strip():
            raise AgentError(ErrorCode.SPLIT_FAILED.value, "Empty input text", recoverable=False)

        # Detect question boundaries
        qa_pairs = self._extract_qa_pairs(clean_text)

        if not qa_pairs:
            raise AgentError(
                ErrorCode.SPLIT_FAILED.value,
                "No question/answer pairs detected",
                details={"text_preview": clean_text[:200]},
            )

        # Match to question paper if provided
        if question_paper:
            packets = self._match_to_paper(qa_pairs, question_paper)
        else:
            packets = self._create_packets_from_pairs(qa_pairs)

        # Validate
        valid_packets = [p for p in packets if len(p.student_answer.strip()) >= self.min_answer_length]
        if len(valid_packets) != len(packets):
            # Some answers too short - keep them but flag in metadata
            for p in packets:
                if len(p.student_answer.strip()) < self.min_answer_length:
                    p.metadata["warning"] = "answer_below_min_length"

        return packets

    def _extract_qa_pairs(self, text: str) -> list[tuple[int, str, str]]:
        """
        Extract (question_number, question_text, answer_text) tuples.
        Handles formats like:
        - "Q1. What is... Answer: ..."
        - "1. What is... \n\n ..."
        - "Question 1: ..."
        """
        # Split by question markers
        # Pattern: Q1., Q1), Question 1, 1., 1)
        pattern = re.compile(
            r"(?:^|\n)\s*(?:Q(?:uestion)?\s*)?(\d+)[\).:]",
            re.MULTILINE | re.IGNORECASE
        )

        matches = list(pattern.finditer(text))
        if not matches:
            # Fallback: try to split by double newlines and detect numbers
            return self._fallback_split(text)

        pairs = []
        for i, match in enumerate(matches):
            q_num = int(match.group(1))
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            content = text[start:end].strip()

            # Try to split question from answer
            q_text, a_text = self._separate_question_answer(content)
            pairs.append((q_num, q_text, a_text))

        return pairs

    def _fallback_split(self, text: str) -> list[tuple[int, str, str]]:
        """Fallback: split by double newlines, try to find numbers."""
        chunks = [c.strip() for c in text.split("\n\n") if c.strip()]
        pairs = []
        q_num = 1

        for chunk in chunks:
            # Look for leading number
            m = re.match(r"^(\d+)[\).:]\s*(.+)", chunk)
            if m:
                q_num = int(m.group(1))
                content = m.group(2)
            else:
                content = chunk

            q_text, a_text = self._separate_question_answer(content)
            pairs.append((q_num, q_text, a_text))
            q_num += 1

        return pairs

    def _separate_question_answer(self, content: str) -> tuple[str, str]:
        """Split content into question and answer parts."""
        # Common answer markers
        answer_markers = [
            r"(?:Answer|Ans|Solution|Response)\s*[:\-]",
            r"[Aa]nswer\s*\n",
            r"[Ss]olution\s*\n",
        ]

        for marker in answer_markers:
            parts = re.split(marker, content, maxsplit=1, flags=re.IGNORECASE)
            if len(parts) == 2:
                return parts[0].strip(), parts[1].strip()

        # No marker: assume first sentence/paragraph is question, rest is answer
        paragraphs = [p.strip() for p in content.split("\n") if p.strip()]
        if len(paragraphs) >= 2:
            # Heuristic: question ends with ? or :
            for i, p in enumerate(paragraphs):
                if p.endswith(("?", ":")) and i < len(paragraphs) - 1:
                    return "\n".join(paragraphs[:i+1]), "\n".join(paragraphs[i+1:])
            # Default: first paragraph = question
            return paragraphs[0], "\n".join(paragraphs[1:])

        return content, ""

    def _match_to_paper(
        self, qa_pairs: list[tuple[int, str, str]], paper: QuestionPaper
    ) -> list[QuestionPacket]:
        """Match extracted Q/A to question paper by number and content similarity."""
        paper_by_num = {q.number: q for q in paper.questions}
        packets = []

        for q_num, q_text, a_text in qa_pairs:
            paper_q = paper_by_num.get(q_num)

            if paper_q:
                # Use paper's question text and marks
                packet = QuestionPacket(
                    question_number=q_num,
                    question_text=paper_q.text,
                    max_marks=paper_q.max_marks,
                    student_answer=a_text,
                    metadata={
                        "matched_by": "number",
                        "extracted_question": q_text,
                        "similarity": self._similarity(q_text, paper_q.text),
                    },
                )
            elif self.strict_matching:
                # Strict: skip unmatched
                continue
            else:
                # Lenient: create packet with extracted question
                packet = QuestionPacket(
                    question_number=q_num,
                    question_text=q_text,
                    max_marks=10,  # default
                    student_answer=a_text,
                    metadata={"matched_by": "none", "warning": "no_paper_match"},
                )
            packets.append(packet)

        return packets

    def _create_packets_from_pairs(self, qa_pairs: list[tuple[int, str, str]]) -> list[QuestionPacket]:
        """Create packets without question paper reference."""
        return [
            QuestionPacket(
                question_number=q_num,
                question_text=q_text,
                max_marks=10,
                student_answer=a_text,
                metadata={"matched_by": "none"},
            )
            for q_num, q_text, a_text in qa_pairs
        ]

    def _similarity(self, a: str, b: str) -> float:
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()