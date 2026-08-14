"""
Evaluation Agent — Grade student answers against rubric using LLM.
"""

from __future__ import annotations

import json
from pathlib import Path

from google import genai
from google.genai.errors import APIError
from pydantic import ValidationError

from schemas import (
    QuestionPacket,
    Rubric,
    EvaluationResult,
    KeyPointScore,
    ErrorCode,
)
from agents.base import BaseAgent, AgentError, PipelineStage


class EvaluationAgent(BaseAgent[EvaluationResult]):
    """Evaluate a single question packet against its rubric."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-2.0-flash",
        temperature: float = 0.1,
        max_retries: int = 3,
        timeout_seconds: int = 60,
    ):
        super().__init__(PipelineStage.EVALUATE, max_retries=max_retries)
        self.client = genai.Client(api_key=api_key) if api_key else genai.Client()
        self.model = model
        self.temperature = temperature
        self.timeout_seconds = timeout_seconds
        self._prompt_template = self._load_prompt()

    def _load_prompt(self) -> str:
        prompt_path = Path(__file__).parent.parent / "prompts" / "evaluation.md"
        return prompt_path.read_text(encoding="utf-8")

    async def _execute(self, input_data: tuple[QuestionPacket, Rubric]) -> EvaluationResult:
        packet, rubric = input_data

        # Build prompt
        prompt = self._build_prompt(packet, rubric)

        # Call LLM
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
                code=ErrorCode.EVALUATION_FAILED.value,
                message=f"Gemini API error: {e}",
                details={"status_code": getattr(e, "status_code", None)},
            )

        # Parse and validate
        try:
            data = json.loads(response.text or "{}")
            result = self._validate_and_build(data, packet, rubric)
        except (json.JSONDecodeError, ValidationError) as e:
            raise AgentError(
                code=ErrorCode.INVALID_RESPONSE.value,
                message=f"Invalid LLM response: {e}",
                details={"raw_response": response.text[:500] if response.text else ""},
            )

        return result

    def _build_prompt(self, packet: QuestionPacket, rubric: Rubric) -> str:
        key_points_json = json.dumps(
            [
                {
                    "concept": kp.concept,
                    "weight": kp.weight,
                    "required": kp.required,
                    "partial_credit": kp.partial_credit,
                }
                for kp in rubric.key_points
            ],
            indent=2,
        )

        marking_scheme_json = json.dumps(
            {
                "type": rubric.marking_scheme.type.value,
                "partial_credit_enabled": rubric.marking_scheme.partial_credit_enabled,
                "deduction_rules": rubric.marking_scheme.deduction_rules,
            },
            indent=2,
        )

        return self._prompt_template.replace("{{question_text}}", packet.question_text).replace(
            "{{max_marks}}", str(packet.max_marks)
        ).replace("{{model_answer}}", rubric.model_answer).replace(
            "{{key_points_json}}", key_points_json
        ).replace("{{marking_scheme_json}}", marking_scheme_json).replace(
            "{{student_answer}}", packet.student_answer or "[NO ANSWER PROVIDED]"
        ).replace("{{question_number}}", str(packet.question_number))

    def _validate_and_build(
        self, data: dict, packet: QuestionPacket, rubric: Rubric
    ) -> EvaluationResult:
        # Validate marks within bounds
        marks = float(data.get("marks_awarded", 0))
        marks = max(0.0, min(marks, packet.max_marks))

        # Validate confidence
        confidence = float(data.get("confidence", 0.5))
        confidence = max(0.0, min(confidence, 1.0))

        # Build key point scores
        kp_scores = []
        for kp_data in data.get("key_point_scores", []):
            concept = kp_data.get("concept", "")
            # Find matching key point for weight cap
            ref_kp = next((kp for kp in rubric.key_points if kp.concept == concept), None)
            max_weight = ref_kp.weight if ref_kp else 1.0
            awarded = max(0.0, min(float(kp_data.get("awarded_weight", 0)), max_weight))

            kp_scores.append(
                KeyPointScore(
                    concept=concept,
                    awarded_weight=awarded,
                    reasoning=kp_data.get("reasoning", ""),
                )
            )

        return EvaluationResult(
            question_number=packet.question_number,
            marks_awarded=marks,
            max_marks=packet.max_marks,
            confidence=confidence,
            reasoning=data.get("reasoning", []),
            key_point_scores=kp_scores,
            metadata={
                "model": self.model,
                "temperature": self.temperature,
            },
        )