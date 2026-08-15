"""
FastAPI Routes — API endpoints for the AI pipeline.
"""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import ValidationError

from schemas import (
    EvaluateRequest,
    EvaluateResponse,
    QuestionPaper,
    Rubric,
    SourceType,
    FinalReport,
    ErrorCode,
)
from pipeline import AIPipeline, PipelineInput, PipelineConfig, PipelineError

router = APIRouter(prefix="/api/v1", tags=["evaluation"])

# Global pipeline instance (initialized on startup)
_pipeline: AIPipeline | None = None


def get_pipeline() -> AIPipeline:
    global _pipeline
    if _pipeline is None:
        config_path = "config.yaml"
        config = PipelineConfig.load(config_path)
        _pipeline = AIPipeline(config)
    return _pipeline


@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate_answer_sheet(
    file: UploadFile = File(..., description="Answer sheet PDF or image"),
    student_id: str = Form(...),
    exam_id: str = Form(...),
    subject: str = Form(...),
    question_paper_json: str = Form(..., description="JSON string of QuestionPaper"),
    rubrics_json: str = Form(..., description="JSON string of dict[int, Rubric]"),
) -> EvaluateResponse:
    """
    Evaluate a subjective answer sheet.

    Multipart form data:
    - file: PDF or image file
    - student_id: Student identifier
    - exam_id: Exam identifier
    - subject: Subject name
    - question_paper_json: JSON-encoded QuestionPaper
    - rubrics_json: JSON-encoded dict[int, Rubric]
    """
    start = time.perf_counter()

    # Validate file
    allowed_types = {"application/pdf", "image/png", "image/jpeg", "image/jpg", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Allowed: {allowed_types}",
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    source_type = (
        SourceType.PDF if file.content_type == "application/pdf" else SourceType.IMAGE
    )

    # Parse JSON inputs
    try:
        question_paper = QuestionPaper.model_validate_json(question_paper_json)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=f"Invalid question_paper: {e}")

    try:
        rubrics_data = Rubric.model_validate_json(rubrics_json)
        # Handle dict[int, Rubric] - JSON keys are strings
        if isinstance(rubrics_data, dict):
            rubrics = {int(k): v for k, v in rubrics_data.items()}
        else:
            raise ValueError("rubrics_json must be a JSON object")
    except (ValidationError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid rubrics: {e}")

    # Build pipeline input
    pipeline_input = PipelineInput(
        file_bytes=file_bytes,
        source_type=source_type,
        student_id=student_id,
        exam_id=exam_id,
        subject=subject,
        question_paper=question_paper,
        rubrics=rubrics,
    )

    # Execute pipeline
    try:
        pipeline = get_pipeline()
        report = await pipeline.evaluate(pipeline_input)
    except PipelineError as e:
        raise HTTPException(status_code=500, detail={"code": e.code, "message": e.message, "details": e.details})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {type(e).__name__}: {e}")

    processing_time = int((time.perf_counter() - start) * 1000)

    return EvaluateResponse(
        report=report,
        trace_id=report.metadata.get("trace_id", "unknown"),
        processing_time_ms=processing_time,
    )


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "agenticeval-ai",
        "version": "0.1.0",
    }


@router.get("/config")
async def get_config() -> dict[str, Any]:
    """Return current pipeline configuration (non-sensitive)."""
    config = PipelineConfig.load("config.yaml")
    return {
        "ocr": config.ocr,
        "cleaner": config.cleaner,
        "splitter": config.splitter,
        "evaluator": {k: v for k, v in config.evaluator.items() if k != "api_key"},
        "feedback": config.feedback,
        "aggregator": config.aggregator,
        "pipeline": config.pipeline,
    }