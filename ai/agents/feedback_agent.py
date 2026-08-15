"""
Feedback Agent — Generate personalized feedback for student and examiner.
"""

from __future__ import annotations

import json
from pathlib import Path

from google import genai
from google.genai.errors import APIError
from pydantic import ValidationError

from schemas import (
    QuestionPacket,
    EvaluationResult,
    FeedbackResult,
    FeedbackTone,
    ErrorCode,
)
from agents.base import BaseAgent, AgentError, PipelineStage


class FeedbackAgent(BaseAgent[FeedbackResult]):
    """Generate feedback based on evaluation results."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-2.0-flash",
        temperature: float = 0.3,
        tone: FeedbackTone = FeedbackTone.CONSTRUCTIVE,
        include_exemplar: bool = True,
        max_length: int = 500,
        max_retries: int = 3,
    ):
        super().__init__(PipelineStage.FEEDBACK, max_retries=max_retries)
        self.client = genai.Client(api_key=api_key) if api_key else genai.Client()
        self.model = model
        self.temperature = temperature
        self.tone = tone
        self.include_exemplar = include_exemplar
        self.max_length = max_length
        self._prompt_template = self._load_prompt()

    def _load_prompt(self) -> str:
        prompt_path = Path(__file__).parent.parent / "prompts" / "feedback.md"
        return prompt_path.read_text(encoding="utf-8")

    async def _execute(
        self, input_data: tuple[QuestionPacket, EvaluationResult]
    ) -> FeedbackResult:
        packet, evaluation = input_data

        prompt = self._build_prompt(packet, evaluation)

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    "temperature": self.temperature,
                    "response_mime_type": "application/json",
                },
            )
        except APIError as e:
            raise AgentError(
                code=ErrorCode.FEEDBACK_FAILED.value,
                message=f"Gemini API error: {e}",
                details={"status_code": getattr(e, "status_code", None)},
            )

        try:
            data = json.loads(response.text or "{}")
            return self._validate_and_build(data, packet, evaluation)
        except (json.JSONDecodeError, ValidationError) as e:
            raise AgentError(
                code=ErrorCode.FEEDBACK_FAILED.value,
                message=f"Invalid LLM response: {e}",
                details={"raw_response": response.text[:500] if response.text else ""},
            )

    def _build_prompt(
        self, packet: QuestionPacket, evaluation: EvaluationResult
    ) -> str:
        kp_scores_json = json.dumps(
            [
                {
                    "concept": kp.concept,
                    "awarded_weight": kp.awarded_weight,
                    "reasoning": kp.reasoning,
                }
                for kp in evaluation.key_point_scores
            ],
            indent=2,
        )

        return (
            self._prompt_template.replace("{{question_text}}", packet.question_text)
            .replace("{{student_answer}}", packet.student_answer or "[NO ANSWER]")
            .replace("{{marks_awarded}}", str(evaluation.marks_awarded))
            .replace("{{max_marks}}", str(evaluation.max_marks))
            .replace("{{reasoning}}", "; ".join(evaluation.reasoning))
            .replace("{{key_point_scores_json}}", kp_scores_json)
            .replace("{{tone}}", self.tone.value)
            .replace("{{max_length}}", str(self.max_length))
            .replace("{{question_number}}", str(packet.question_number))
        )

    def _validate_and_build(
        self, data: dict, packet: QuestionPacket, evaluation: EvaluationResult
    ) -> FeedbackResult:
        student_fb = data.get("student_feedback", "")
        if len(student_fb) > self.max_length:
            student_fb = student_fb[: self.max_length - 3] + "..."

        return FeedbackResult(
            question_number=packet.question_number,
            student_feedback=student_fb,
            examiner_notes=data.get("examiner_notes", ""),
            strengths=data.get("strengths", [])[:3],
            improvements=data.get("improvements", [])[:3],
            exemplar_snippet=data.get("exemplar_snippet") if self.include_exemplar else None,
            metadata={"model": self.model, "tone": self.tone.value},
        )