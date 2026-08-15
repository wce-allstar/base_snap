"""
AgenticEval — Shared Pydantic Schemas

All inter-agent data contracts live here. Agents import only what they need.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


# ──────────────────────────────────────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────────────────────────────────────

class SourceType(str, Enum):
    PDF = "pdf"
    IMAGE = "image"


class PipelineStage(str, Enum):
    OCR = "ocr"
    CLEAN = "clean"
    SPLIT = "split"
    EVALUATE = "evaluate"
    FEEDBACK = "feedback"
    AGGREGATE = "aggregate"


class PipelineStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"


class ErrorCode(str, Enum):
    OCR_FAILED = "OCR_FAILED"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    EMPTY_DOCUMENT = "EMPTY_DOCUMENT"
    CLEANING_FAILED = "CLEANING_FAILED"
    SPLIT_FAILED = "SPLIT_FAILED"
    QUESTION_MISMATCH = "QUESTION_MISMATCH"
    EMPTY_ANSWER = "EMPTY_ANSWER"
    EVALUATION_FAILED = "EVALUATION_FAILED"
    LLM_TIMEOUT = "LLM_TIMEOUT"
    INVALID_RESPONSE = "INVALID_RESPONSE"
    FEEDBACK_FAILED = "FEEDBACK_FAILED"
    AGGREGATION_FAILED = "AGGREGATION_FAILED"


class FeedbackTone(str, Enum):
    CONSTRUCTIVE = "constructive"
    ENCOURAGING = "encouraging"
    FORMAL = "formal"


class MarkingSchemeType(str, Enum):
    POINTS = "points"
    HOLISTIC = "holistic"
    CHECKLIST = "checklist"


class ConsistencyFlagType(str, Enum):
    SCORE_VARIANCE = "score_variance"
    CONFIDENCE_DROP = "confidence_drop"
    PATTERN_ANOMALY = "pattern_anomaly"


class ConsistencySeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ──────────────────────────────────────────────────────────────────────────────
# Base / Envelope
# ──────────────────────────────────────────────────────────────────────────────

class ErrorInfo(BaseModel):
    code: ErrorCode
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    recoverable: bool = True


class PipelineEnvelope(BaseModel):
    stage: PipelineStage
    status: PipelineStatus
    payload: Any = None
    error: ErrorInfo | None = None
    trace_id: str = Field(default_factory=lambda: uuid4().hex[:12])
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ──────────────────────────────────────────────────────────────────────────────
# OCR
# ──────────────────────────────────────────────────────────────────────────────

class OCRResult(BaseModel):
    raw_text: str
    page_count: int
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


# ──────────────────────────────────────────────────────────────────────────────
# Cleaner
# ──────────────────────────────────────────────────────────────────────────────

class CleanedText(BaseModel):
    text: str
    transformations_applied: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


# ──────────────────────────────────────────────────────────────────────────────
# Question Paper / Rubric
# ──────────────────────────────────────────────────────────────────────────────

class QuestionMeta(BaseModel):
    number: int
    text: str
    max_marks: int = Field(gt=0)
    keywords: list[str] = Field(default_factory=list)


class QuestionPaper(BaseModel):
    questions: list[QuestionMeta]


class KeyPoint(BaseModel):
    concept: str
    weight: float = Field(ge=0.0, le=1.0)
    required: bool = False
    partial_credit: bool = True


class MarkingScheme(BaseModel):
    type: MarkingSchemeType = MarkingSchemeType.POINTS
    partial_credit_enabled: bool = True
    deduction_rules: list[str] = Field(default_factory=list)


class Rubric(BaseModel):
    model_answer: str
    key_points: list[KeyPoint]
    marking_scheme: MarkingScheme = Field(default_factory=MarkingScheme)

    @field_validator("key_points", mode="after")
    @classmethod
    def validate_weights(cls, v: list[KeyPoint]) -> list[KeyPoint]:
        total = sum(kp.weight for kp in v)
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Key point weights must sum to 1.0, got {total}")
        return v


# ──────────────────────────────────────────────────────────────────────────────
# Splitter
# ──────────────────────────────────────────────────────────────────────────────

class QuestionPacket(BaseModel):
    question_number: int
    question_text: str
    max_marks: int
    student_answer: str
    metadata: dict[str, Any] = Field(default_factory=dict)


# ──────────────────────────────────────────────────────────────────────────────
# Evaluation
# ──────────────────────────────────────────────────────────────────────────────

class KeyPointScore(BaseModel):
    concept: str
    awarded_weight: float = Field(ge=0.0)
    reasoning: str


class EvaluationResult(BaseModel):
    question_number: int
    marks_awarded: float = Field(ge=0.0)
    max_marks: int = Field(gt=0)
    confidence: float = Field(ge=0.0)
    reasoning: list[str] = Field(default_factory=list)
    key_point_scores: list[KeyPointScore] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def percentage(self) -> float:
        return (self.marks_awarded / self.max_marks) * 100 if self.max_marks > 0 else 0.0


# ──────────────────────────────────────────────────────────────────────────────
# Feedback
# ──────────────────────────────────────────────────────────────────────────────

class FeedbackResult(BaseModel):
    question_number: int
    student_feedback: str
    examiner_notes: str
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    exemplar_snippet: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


# ──────────────────────────────────────────────────────────────────────────────
# Aggregator
# ──────────────────────────────────────────────────────────────────────────────

class StudentMeta(BaseModel):
    student_id: str
    exam_id: str
    subject: str
    total_max_marks: int = Field(gt=0)


class QuestionReport(BaseModel):
    question_number: int
    marks: float
    max_marks: int
    percentage: float
    confidence: float
    reasoning: list[str]
    feedback: str


class ConsistencyFlag(BaseModel):
    type: ConsistencyFlagType
    description: str
    severity: ConsistencySeverity
    affected_questions: list[int]


class FinalReport(BaseModel):
    student_id: str
    exam_id: str
    subject: str
    total_marks: float = Field(ge=0.0)
    total_max_marks: int = Field(gt=0)
    percentage: float = Field(ge=0.0, le=100.0)
    per_question: list[QuestionReport] = Field(default_factory=list)
    consistency_flags: list[ConsistencyFlag] = Field(default_factory=list)
    overall_feedback: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


# ──────────────────────────────────────────────────────────────────────────────
# API Request/Response
# ──────────────────────────────────────────────────────────────────────────────

class EvaluateRequest(BaseModel):
    student_id: str
    exam_id: str
    subject: str
    question_paper: QuestionPaper
    rubrics: dict[int, Rubric]


class EvaluateResponse(BaseModel):
    report: FinalReport
    trace_id: str
    processing_time_ms: int