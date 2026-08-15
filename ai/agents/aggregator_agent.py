"""
Aggregator Agent — Compile final report from evaluations and feedback.
"""

from __future__ import annotations

import statistics
from datetime import datetime

from schemas import (
    EvaluationResult,
    FeedbackResult,
    StudentMeta,
    FinalReport,
    QuestionReport,
    ConsistencyFlag,
    ConsistencyFlagType,
    ConsistencySeverity,
)
from agents.base import BaseAgent, PipelineStage


class AggregatorAgent(BaseAgent[FinalReport]):
    """Aggregate per-question results into a final report with consistency checks."""

    def __init__(self, consistency_threshold: float = 0.15, max_retries: int = 1):
        super().__init__(PipelineStage.AGGREGATE, max_retries=max_retries)
        self.consistency_threshold = consistency_threshold

    async def _execute(
        self, input_data: tuple[list[EvaluationResult], list[FeedbackResult], StudentMeta]
    ) -> FinalReport:
        eval_results, feedback_results, student_meta = input_data

        # Sort by question number
        eval_results = sorted(eval_results, key=lambda x: x.question_number)
        feedback_by_q = {f.question_number: f for f in feedback_results}

        # Build per-question reports
        per_question = []
        for e in eval_results:
            fb = feedback_by_q.get(e.question_number)
            per_question.append(
                QuestionReport(
                    question_number=e.question_number,
                    marks=e.marks_awarded,
                    max_marks=e.max_marks,
                    percentage=e.percentage,
                    confidence=e.confidence,
                    reasoning=e.reasoning,
                    feedback=fb.student_feedback if fb else "",
                )
            )

        # Compute totals
        total_marks = sum(e.marks_awarded for e in eval_results)
        total_max = student_meta.total_max_marks or sum(e.max_marks for e in eval_results)
        percentage = (total_marks / total_max * 100) if total_max > 0 else 0.0

        # Aggregate confidence (weighted by marks)
        if total_max > 0:
            confidence_score = sum(
                e.confidence * e.max_marks for e in eval_results
            ) / total_max
        else:
            confidence_score = statistics.mean([e.confidence for e in eval_results]) if eval_results else 0.0

        # Consistency checks
        flags = self._check_consistency(eval_results)

        # Overall feedback
        overall_feedback = self._generate_overall_feedback(per_question, percentage)

        return FinalReport(
            student_id=student_meta.student_id,
            exam_id=student_meta.exam_id,
            subject=student_meta.subject,
            total_marks=total_marks,
            total_max_marks=total_max,
            percentage=round(percentage, 2),
            per_question=per_question,
            consistency_flags=flags,
            overall_feedback=overall_feedback,
            confidence_score=round(confidence_score, 3),
            generated_at=datetime.utcnow(),
            metadata={
                "questions_evaluated": len(eval_results),
                "questions_in_paper": len(student_meta.__dict__.get("question_paper", [])),
            },
        )

    def _check_consistency(self, results: list[EvaluationResult]) -> list[ConsistencyFlag]:
        """Run consistency checks across evaluations."""
        flags = []

        if len(results) < 2:
            return flags

        # 1. Confidence drop check
        confidences = [r.confidence for r in results]
        avg_conf = statistics.mean(confidences)
        for r in results:
            if avg_conf - r.confidence > self.consistency_threshold:
                flags.append(
                    ConsistencyFlag(
                        type=ConsistencyFlagType.CONFIDENCE_DROP,
                        description=f"Q{r.question_number} confidence ({r.confidence:.2f}) "
                        f"significantly below average ({avg_conf:.2f})",
                        severity=ConsistencySeverity.MEDIUM,
                        affected_questions=[r.question_number],
                    )
                )

        # 2. Score variance check (unusually high/low scores)
        percentages = [r.percentage for r in results]
        if len(percentages) >= 3:
            avg_pct = statistics.mean(percentages)
            stdev_pct = statistics.stdev(percentages) if len(percentages) > 1 else 0
            for r in results:
                if stdev_pct > 0 and abs(r.percentage - avg_pct) > 2 * stdev_pct:
                    flags.append(
                        ConsistencyFlag(
                            type=ConsistencyFlagType.SCORE_VARIANCE,
                            description=f"Q{r.question_number} score ({r.percentage:.1f}%) "
                            f"is outlier vs mean ({avg_pct:.1f}%)",
                            severity=ConsistencySeverity.LOW,
                            affected_questions=[r.question_number],
                        )
                    )

        # 3. Pattern anomaly: all high confidence but low scores (or vice versa)
        high_conf_low_score = sum(1 for r in results if r.confidence > 0.8 and r.percentage < 40)
        low_conf_high_score = sum(1 for r in results if r.confidence < 0.4 and r.percentage > 70)
        if high_conf_low_score >= 2:
            flags.append(
                ConsistencyFlag(
                    type=ConsistencyFlagType.PATTERN_ANOMALY,
                    description=f"{high_conf_low_score} questions have high confidence but low scores — "
                    "possible rubric mismatch or systemic issue",
                    severity=ConsistencySeverity.HIGH,
                    affected_questions=[
                        r.question_number for r in results
                        if r.confidence > 0.8 and r.percentage < 40
                    ],
                )
            )
        if low_conf_high_score >= 2:
            flags.append(
                ConsistencyFlag(
                    type=ConsistencyFlagType.PATTERN_ANOMALY,
                    description=f"{low_conf_high_score} questions have low confidence but high scores — "
                    "review recommended",
                    severity=ConsistencySeverity.MEDIUM,
                    affected_questions=[
                        r.question_number for r in results
                        if r.confidence < 0.4 and r.percentage > 70
                    ],
                )
            )

        return flags

    def _generate_overall_feedback(
        self, per_question: list[QuestionReport], percentage: float
    ) -> str:
        if not per_question:
            return "No questions evaluated."

        if percentage >= 80:
            opening = "Excellent performance overall."
        elif percentage >= 60:
            opening = "Good understanding demonstrated."
        elif percentage >= 40:
            opening = "Satisfactory effort with room for improvement."
        else:
            opening = "Significant gaps identified; focused revision recommended."

        strengths = [q for q in per_question if q.percentage >= 70]
        weak = [q for q in per_question if q.percentage < 50]

        parts = [opening]
        if strengths:
            parts.append(
                f"Strong areas: Q{', Q'.join(str(q.question_number) for q in strengths)}."
            )
        if weak:
            parts.append(
                f"Needs improvement: Q{', Q'.join(str(q.question_number) for q in weak)}."
            )

        return " ".join(parts)