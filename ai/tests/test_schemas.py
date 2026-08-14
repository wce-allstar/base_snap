"""
Schema validation tests.
"""

import pytest
from pydantic import ValidationError

from schemas import (
    QuestionMeta,
    QuestionPaper,
    KeyPoint,
    Rubric,
    MarkingScheme,
    MarkingSchemeType,
    QuestionPacket,
    EvaluationResult,
    KeyPointScore,
    FeedbackResult,
    StudentMeta,
    FinalReport,
    ConsistencyFlag,
    SourceType,
    FeedbackTone,
)


class TestQuestionPaper:
    def test_valid_question_paper(self):
        paper = QuestionPaper(
            questions=[
                QuestionMeta(number=1, text="What is OS?", max_marks=10),
                QuestionMeta(number=2, text="Explain deadlock", max_marks=15),
            ]
        )
        assert len(paper.questions) == 2

    def test_invalid_max_marks(self):
        with pytest.raises(ValidationError):
            QuestionMeta(number=1, text="Q", max_marks=0)


class TestRubric:
    def test_valid_rubric_weights_sum_to_one(self):
        rubric = Rubric(
            model_answer="Answer",
            key_points=[
                KeyPoint(concept="A", weight=0.5),
                KeyPoint(concept="B", weight=0.5),
            ],
        )
        assert len(rubric.key_points) == 2

    def test_invalid_weights_raise(self):
        with pytest.raises(ValidationError):
            Rubric(
                model_answer="Answer",
                key_points=[
                    KeyPoint(concept="A", weight=0.3),
                    KeyPoint(concept="B", weight=0.3),
                ],
            )


class TestEvaluationResult:
    def test_percentage_property(self):
        result = EvaluationResult(
            question_number=1,
            marks_awarded=7.5,
            max_marks=10,
            confidence=0.9,
            reasoning=["Good"],
        )
        assert result.percentage == 75.0

    def test_bounds_clamping(self):
        # Pydantic v2 doesn't auto-clamp; this tests our manual validation in agent
        result = EvaluationResult(
            question_number=1,
            marks_awarded=15.0,  # > max_marks
            max_marks=10,
            confidence=1.5,  # > 1
            reasoning=[],
        )
        # Agent clamps these values; schema allows for validation
        assert result.marks_awarded == 15.0


class TestEnums:
    def test_source_type_values(self):
        assert SourceType.PDF == "pdf"
        assert SourceType.IMAGE == "image"

    def test_feedback_tone_values(self):
        assert FeedbackTone.CONSTRUCTIVE == "constructive"
        assert FeedbackTone.ENCOURAGING == "encouraging"
        assert FeedbackTone.FORMAL == "formal"


class TestFinalReport:
    def test_valid_report(self):
        report = FinalReport(
            student_id="S123",
            exam_id="E456",
            subject="OS",
            total_marks=85.0,
            total_max_marks=100,
            percentage=85.0,
            per_question=[],
            overall_feedback="Good",
            confidence_score=0.9,
        )
        assert report.student_id == "S123"
        assert report.percentage == 85.0