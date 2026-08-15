"""
Pipeline Orchestrator — Coordinate all agents end-to-end.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from schemas import (
    SourceType,
    QuestionPaper,
    Rubric,
    StudentMeta,
    FinalReport,
    PipelineEnvelope,
    PipelineStatus,
    ErrorCode,
)
from agents import (
    OCRAgent,
    CleanerAgent,
    SplitterAgent,
    EvaluationAgent,
    FeedbackAgent,
    AggregatorAgent,
    AgentError,
)


@dataclass
class PipelineConfig:
    ocr: dict[str, Any]
    cleaner: dict[str, Any]
    splitter: dict[str, Any]
    evaluator: dict[str, Any]
    feedback: dict[str, Any]
    aggregator: dict[str, Any]
    pipeline: dict[str, Any]

    @classmethod
    def load(cls, path: str | Path = "config.yaml") -> "PipelineConfig":
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(**data)


@dataclass
class PipelineInput:
    file_bytes: bytes
    source_type: SourceType
    student_id: str
    exam_id: str
    subject: str
    question_paper: QuestionPaper
    rubrics: dict[int, Rubric]


class AIPipeline:
    """End-to-end evaluation pipeline."""

    def __init__(self, config: PipelineConfig, api_key: str | None = None):
        self.config = config
        self.api_key = api_key

        # Initialize agents
        self.ocr = OCRAgent(
            api_key=api_key,
            model=config.ocr.get("engine", "gemini") == "gemini" and "gemini-2.0-flash" or "tesseract",
            max_retries=config.ocr.get("max_retries", 3),
        )

        self.cleaner = CleanerAgent(
            remove_page_numbers=config.cleaner.get("remove_page_numbers", True),
            remove_headers_footers=config.cleaner.get("remove_headers_footers", True),
            fix_hyphenation=config.cleaner.get("fix_hyphenation", True),
            max_retries=config.cleaner.get("max_retries", 3),
        )

        self.splitter = SplitterAgent(
            strict_matching=config.splitter.get("strict_matching", True),
            min_answer_length=config.splitter.get("min_answer_length", 10),
            max_retries=config.splitter.get("max_retries", 1),
        )

        self.evaluator = EvaluationAgent(
            api_key=api_key,
            model=config.evaluator.get("model", "gemini-2.0-flash"),
            temperature=config.evaluator.get("temperature", 0.1),
            max_retries=config.evaluator.get("max_retries", 3),
            timeout_seconds=config.evaluator.get("timeout_seconds", 60),
        )

        self.feedback = FeedbackAgent(
            api_key=api_key,
            model=config.feedback.get("model", "gemini-2.0-flash"),
            temperature=config.feedback.get("temperature", 0.3),
            tone=config.feedback.get("tone", "constructive"),
            include_exemplar=config.feedback.get("include_exemplar", True),
            max_length=config.feedback.get("max_length", 500),
            max_retries=config.feedback.get("max_retries", 3),
        )

        self.aggregator = AggregatorAgent(
            consistency_threshold=config.aggregator.get("consistency_threshold", 0.15),
            max_retries=config.aggregator.get("max_retries", 1),
        )

        self.max_concurrent = config.pipeline.get("max_concurrent", 5)
        self.parallel = config.pipeline.get("parallel_evaluation", True)

    async def evaluate(self, input_data: PipelineInput) -> FinalReport:
        """Execute full pipeline."""
        start_time = time.perf_counter()
        trace_id = f"eval_{int(start_time * 1000)}"

        # 1. OCR
        ocr_env = await self.ocr.process((input_data.file_bytes, input_data.source_type))
        if ocr_env.status == PipelineStatus.ERROR:
            raise AgentError(ocr_env.error.code, ocr_env.error.message, ocr_env.error.details)
        ocr_result = ocr_env.payload

        # 2. Clean
        clean_env = await self.cleaner.process(ocr_result.raw_text)
        if clean_env.status == PipelineStatus.ERROR:
            raise AgentError(clean_env.error.code, clean_env.error.message, clean_env.error.details)
        clean_result = clean_env.payload

        # 3. Split
        split_env = await self.splitter.process((clean_result.text, input_data.question_paper))
        if split_env.status == PipelineStatus.ERROR:
            raise AgentError(split_env.error.code, split_env.error.message, split_env.error.details)
        packets = split_env.payload

        # 4. Evaluate (parallel or sequential)
        eval_results = await self._evaluate_all(packets, input_data.rubrics)

        # 5. Feedback (parallel)
        feedback_results = await self._generate_feedback_all(packets, eval_results)

        # 6. Aggregate
        student_meta = StudentMeta(
            student_id=input_data.student_id,
            exam_id=input_data.exam_id,
            subject=input_data.subject,
            total_max_marks=sum(r.max_marks for r in eval_results),
        )
        agg_env = await self.aggregator.process((eval_results, feedback_results, student_meta))
        if agg_env.status == PipelineStatus.ERROR:
            raise AgentError(agg_env.error.code, agg_env.error.message, agg_env.error.details)

        report = agg_env.payload
        report.metadata["trace_id"] = trace_id
        report.metadata["total_latency_ms"] = int((time.perf_counter() - start_time) * 1000)
        report.metadata["stage_latencies"] = {
            "ocr": ocr_env.metadata.get("latency_ms", 0),
            "clean": clean_env.metadata.get("latency_ms", 0),
            "split": split_env.metadata.get("latency_ms", 0),
            "evaluate": sum(r.metadata.get("latency_ms", 0) for r in eval_results),
            "feedback": sum(f.metadata.get("latency_ms", 0) for f in feedback_results),
            "aggregate": agg_env.metadata.get("latency_ms", 0),
        }

        return report

    async def _evaluate_all(
        self, packets: list, rubrics: dict[int, Rubric]
    ) -> list:
        """Evaluate all packets, with optional parallelism."""

        async def eval_one(packet):
            rubric = rubrics.get(packet.question_number)
            if not rubric:
                # Create minimal rubric for unmatched questions
                from schemas import Rubric, KeyPoint, MarkingScheme, MarkingSchemeType
                rubric = Rubric(
                    model_answer="",
                    key_points=[KeyPoint(concept="general", weight=1.0)],
                    marking_scheme=MarkingScheme(
                        type=MarkingSchemeType.HOLISTIC,
                        partial_credit_enabled=True,
                    ),
                )
            env = await self.evaluator.process((packet, rubric))
            if env.status == PipelineStatus.ERROR:
                # Return a zero-score result instead of failing entire pipeline
                from schemas import EvaluationResult
                return EvaluationResult(
                    question_number=packet.question_number,
                    marks_awarded=0.0,
                    max_marks=packet.max_marks,
                    confidence=0.0,
                    reasoning=[f"Evaluation failed: {env.error.message}"],
                    metadata={"error": env.error.code},
                )
            return env.payload

        if self.parallel and len(packets) > 1:
            semaphore = asyncio.Semaphore(self.max_concurrent)

            async def limited_eval(p):
                async with semaphore:
                    return await eval_one(p)

            return await asyncio.gather(*[limited_eval(p) for p in packets])
        else:
            return await asyncio.gather(*[eval_one(p) for p in packets])

    async def _generate_feedback_all(
        self, packets: list, eval_results: list
    ) -> list:
        """Generate feedback for all evaluated questions."""

        async def feedback_one(packet, evaluation):
            env = await self.feedback.process((packet, evaluation))
            if env.status == PipelineStatus.ERROR:
                from schemas import FeedbackResult
                return FeedbackResult(
                    question_number=packet.question_number,
                    student_feedback="Feedback generation failed.",
                    examiner_notes=f"Feedback error: {env.error.message}",
                    metadata={"error": env.error.code},
                )
            return env.payload

        return await asyncio.gather(*[
            feedback_one(p, e) for p, e in zip(packets, eval_results)
        ])


class PipelineError(Exception):
    """Pipeline-level error."""

    def __init__(self, code: str, message: str, details: dict | None = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)