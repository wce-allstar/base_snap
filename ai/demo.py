#!/usr/bin/env python3
"""
Demo script — Run the pipeline on a sample answer sheet (deterministic parts only).

Usage:
    python -m ai.demo

Note: Full pipeline requires GEMINI_API_KEY environment variable.
This demo runs the deterministic agents (cleaner, splitter, aggregator)
and shows the structure. For LLM evaluation/feedback, set GEMINI_API_KEY.
"""

from __future__ import annotations

import asyncio
import os
import json
from pathlib import Path

from schemas import (
    SourceType,
    QuestionPaper,
    QuestionMeta,
    Rubric,
    KeyPoint,
    MarkingScheme,
    MarkingSchemeType,
    StudentMeta,
)
from agents.cleaner_agent import CleanerAgent
from agents.splitter_agent import SplitterAgent
from agents.aggregator_agent import AggregatorAgent


# Sample question paper
SAMPLE_PAPER = QuestionPaper(questions=[
    QuestionMeta(number=1, text="What is an operating system? Explain its main functions.", max_marks=10),
    QuestionMeta(number=2, text="Define deadlock. Explain the four necessary conditions for deadlock.", max_marks=15),
    QuestionMeta(number=3, text="What is a process control block (PCB)? List its components.", max_marks=10),
])

# Sample rubrics
SAMPLE_RUBRICS = {
    1: Rubric(
        model_answer=(
            "An operating system (OS) is system software that manages computer hardware "
            "and software resources and provides common services for computer programs. "
            "Main functions: process management, memory management, file system management, "
            "device management, security, and user interface."
        ),
        key_points=[
            KeyPoint(concept="definition", weight=0.2, required=True),
            KeyPoint(concept="process management", weight=0.2),
            KeyPoint(concept="memory management", weight=0.2),
            KeyPoint(concept="file/device management", weight=0.2),
            KeyPoint(concept="security/ui", weight=0.2),
        ],
        marking_scheme=MarkingScheme(type=MarkingSchemeType.POINTS, partial_credit_enabled=True),
    ),
    2: Rubric(
        model_answer=(
            "Deadlock is a situation where a set of processes are blocked because each "
            "holds a resource and waits for another resource held by another process. "
            "Four necessary conditions (Coffman conditions): "
            "1) Mutual Exclusion, 2) Hold and Wait, 3) No Preemption, 4) Circular Wait."
        ),
        key_points=[
            KeyPoint(concept="definition", weight=0.2, required=True),
            KeyPoint(concept="mutual exclusion", weight=0.2),
            KeyPoint(concept="hold and wait", weight=0.2),
            KeyPoint(concept="no preemption", weight=0.2),
            KeyPoint(concept="circular wait", weight=0.2),
        ],
        marking_scheme=MarkingScheme(type=MarkingSchemeType.POINTS, partial_credit_enabled=True),
    ),
    3: Rubric(
        model_answer=(
            "A Process Control Block (PCB) is a data structure used by the OS to store "
            "all information about a process. Components: Process ID, Process State, "
            "Program Counter, CPU Registers, Memory Management Info, Accounting Info, "
            "I/O Status Info."
        ),
        key_points=[
            KeyPoint(concept="definition", weight=0.3, required=True),
            KeyPoint(concept="components list", weight=0.7),
        ],
        marking_scheme=MarkingScheme(type=MarkingSchemeType.POINTS, partial_credit_enabled=True),
    ),
}

# Sample student answer (simulated OCR output)
SAMPLE_ANSWER_TEXT = """
1. What is an operating system? Explain its main functions.
Answer: An operating system is software that manages hardware and software resources of a computer. It acts as an intermediary between users and the computer hardware. The main functions of an OS are process management which handles creation and scheduling of processes, memory management which allocates and deallocates memory, file management which organizes files on disk, and device management which controls input/output devices. It also provides security and user interface.

2. Define deadlock. Explain the four necessary conditions for deadlock.
Answer: Deadlock occurs when two or more processes are waiting for each other to release resources and none can proceed. The four conditions are mutual exclusion where only one process can use a resource at a time, hold and wait where a process holds a resource while waiting for another, no preemption where resources cannot be forcibly taken away, and circular wait where processes form a cycle waiting for resources.

3. What is a process control block (PCB)? List its components.
Answer: A PCB is a data structure that contains information about a process. It includes the process ID, the process state like ready running or waiting, the program counter, CPU registers, memory limits, and open files list.
"""


async def run_demo():
    print("=" * 60)
    print("AgenticEval AI — Demo Run (Deterministic Agents)")
    print("=" * 60)

    has_api_key = os.getenv("GEMINI_API_KEY") is not None
    if not has_api_key:
        print("\n��� GEMINI_API_KEY not set — skipping LLM agents (evaluation, feedback)")
        print("   Set GEMINI_API_KEY to run full pipeline\n")

    # 1. Clean
    print("[1/4] Cleaning OCR text...")
    cleaner = CleanerAgent()
    clean_env = await cleaner.process(SAMPLE_ANSWER_TEXT)
    clean_text = clean_env.payload.text
    print(f"       Transformations: {clean_env.payload.transformations_applied}")

    # 2. Split
    print("[2/4] Splitting questions...")
    splitter = SplitterAgent()
    split_env = await splitter.process((clean_text, SAMPLE_PAPER))
    packets = split_env.payload
    print(f"       Found {len(packets)} questions")
    for p in packets:
        print(f"       Q{p.question_number}: {len(p.student_answer)} chars | max_marks={p.max_marks}")

    # 3. Evaluation & Feedback (mock or real)
    if has_api_key:
        print("[3/4] Evaluating & generating feedback (LLM)...")
        from pipeline import AIPipeline, PipelineConfig
        config = PipelineConfig.load("config.yaml")
        pipeline = AIPipeline(config, api_key=os.getenv("GEMINI_API_KEY"))
        eval_results = await pipeline._evaluate_all(packets, SAMPLE_RUBRICS)
        feedback_results = await pipeline._generate_feedback_all(packets, eval_results)
    else:
        print("[3/4] Skipping LLM evaluation/feedback (no API key)")
        from schemas import EvaluationResult, KeyPointScore, FeedbackResult
        eval_results = [
            EvaluationResult(
                question_number=p.question_number,
                marks_awarded=p.max_marks * 0.7,
                max_marks=p.max_marks,
                confidence=0.8,
                reasoning=["Mock evaluation"],
                key_point_scores=[KeyPointScore(concept="mock", awarded_weight=0.7, reasoning="mock")],
            )
            for p in packets
        ]
        feedback_results = [
            FeedbackResult(
                question_number=p.question_number,
                student_feedback="Mock feedback - set GEMINI_API_KEY for real feedback",
                examiner_notes="Mock",
                strengths=["Mock"],
                improvements=["Add API key"],
            )
            for p in packets
        ]

    # 4. Aggregate
    print("[4/4] Aggregating report...")
    student_meta = StudentMeta(
        student_id="STU-2024-001",
        exam_id="MID-SEM-CS301",
        subject="Operating Systems",
        total_max_marks=35,
    )
    aggregator = AggregatorAgent()
    agg_env = await aggregator.process((eval_results, feedback_results, student_meta))
    report = agg_env.payload

    print("[6/6] Done!")
    print("\n" + "=" * 60)
    print("FINAL REPORT")
    print("=" * 60)
    print(f"Student: {report.student_id}")
    print(f"Exam: {report.exam_id}")
    print(f"Subject: {report.subject}")
    print(f"Total: {report.total_marks}/{report.total_max_marks} ({report.percentage:.1f}%)")
    print(f"Confidence: {report.confidence_score:.2f}")
    print(f"\nPer-Question Breakdown:")
    for q in report.per_question:
        print(f"  Q{q.question_number}: {q.marks}/{q.max_marks} ({q.percentage:.1f}%) - conf: {q.confidence:.2f}")
        for r in q.reasoning:
            print(f"    - {r}")

    print(f"\nConsistency Flags: {len(report.consistency_flags)}")
    for flag in report.consistency_flags:
        print(f"  [{flag.severity.upper()}] {flag.description}")

    print(f"\nOverall Feedback: {report.overall_feedback}")

    # Save report
    output_path = Path("demo_report.json")
    output_path.write_text(report.model_dump_json(indent=2))
    print(f"\nReport saved to {output_path}")


if __name__ == "__main__":
    asyncio.run(run_demo())