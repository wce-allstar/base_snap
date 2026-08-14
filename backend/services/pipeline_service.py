"""Pipeline Orchestrator.

Chains the six agents end-to-end:

file -> OCR -> Structuring -> (Rubric + Reasoning + Consistency) xN -> Feedback xN -> Report

The backend coordinates; it never performs AI evaluation itself.
"""

import os

from ..agents.base import LLMClient
from ..agents.ocr_agent import ocr_agent
from ..agents.structuring_agent import structuring_agent
from ..agents.rubric_agent import rubric_agent
from ..agents.reasoning_agent import reasoning_agent
from ..agents.consistency_agent import consistency_agent
from ..agents.feedback_agent import feedback_agent
from ..database.connection import load_db, save_db
from ..utils.logging import append_log


class PipelineError(Exception):
    """Raised when the pipeline cannot complete. Carries an HTTP status."""

    def __init__(self, status_code, message):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def run_evaluation(student_id, question_paper_id=None):
    """Run the full AI pipeline for one answer sheet. Returns the updated student."""
    db = load_db()
    students = db.get("students", [])
    student = next((s for s in students if s["id"] == student_id), None)
    if student is None:
        raise PipelineError(404, "Student not found")

    api_key = db.get("settings", {}).get("geminiApiKey", "")
    if not api_key:
        raise PipelineError(503, "Gemini API key required. Set it in Settings, then retry.")

    client = LLMClient(api_key=api_key)
    prompts = db.get("agent_prompts", {})
    student["status"] = "Processing"

    # ---------- Stage 1: OCR ----------
    file_path = resolve_sheet_path(student)
    if not file_path or not os.path.exists(file_path):
        raise PipelineError(400, "No answer sheet file found for this student.")

    append_log("extractor", f"Running OCR on {os.path.basename(file_path)}...", "info")
    raw = ocr_agent(file_path, prompts.get("extractor"), client)["raw_text"]
    append_log("extractor", "Handwriting transcription compiled.", "success")

    # ---------- Stage 2: Structuring ----------
    append_log("mapper", "Cleaning text and splitting into question packets...", "info")
    packets = structuring_agent(raw, student_id, prompts.get("structurer"), client)
    append_log("mapper", f"Split {len(packets['questions'])} question packets.", "success")

    # ---------- Stage 3: Evaluation per question ----------
    paper = resolve_question_paper(db, question_paper_id or student.get("questionPaperId"))
    append_log("mapper", f"Loading rubric '{paper.get('subject', 'default')}'...", "info")

    report_questions = []
    total_score = 0.0
    max_total = 0.0
    confidence_sum = 0.0

    for packet in packets["questions"]:
        num = packet["question_number"]
        key = f"q{num}"
        rubric = build_rubric(paper, num, packet)

        append_log("mapper", f"Mapping Q{num} against rubric criteria...", "info")
        mapping = rubric_agent(packet, rubric, prompts.get("mapper"), client)

        append_log("reasoner", f"Auditing logic flow of Q{num}...", "info")
        reasoning = reasoning_agent(packet, rubric, prompts.get("reasoner"), client)

        cohort = cohort_for(db, key)
        append_log("grader", f"Computing marks for Q{num} with cohort of {len(cohort)}...", "info")
        consistency = consistency_agent({
            "question_number": num,
            "coverage": mapping["coverage"],
            "reasoning_score": reasoning["reasoning_score"],
            "max_marks": rubric["max_marks"],
            "cohort": cohort,
        }, prompts.get("grader"), client)
        append_log("checker", f"Consistency check Q{num}: {consistency['notes']}", "success" if consistency["consistency_passed"] else "warn")

        append_log("grader", f"Writing feedback for Q{num}...", "info")
        feedback = feedback_agent({
            "student_id": student_id,
            "question_number": num,
            "marks": consistency["adjusted_marks"],
            "max_marks": rubric["max_marks"],
            "coverage": mapping["coverage"],
            "reasoning": reasoning["logic_issues"],
        }, prompts.get("feedback"), client)

        report_questions.append({
            "question_number": num,
            "marks": consistency["adjusted_marks"],
            "max_marks": rubric["max_marks"],
            "coverage": mapping["coverage"],
            "reasoning": reasoning["logic_issues"],
            "confidence": reasoning["confidence"],
            "consistency_passed": consistency["consistency_passed"],
            "feedback": feedback,
        })

        student["questions"][key] = {
            "score": consistency["adjusted_marks"],
            "maxScore": rubric["max_marks"],
            "ocrText": packet["answer"],
            "coverage": mapping["coverage"],
            "strengths": feedback["strengths"],
            "weaknesses": feedback["missing"],
            "justification": feedback["feedback_text"],
            "confidence": reasoning["confidence"],
            "consistency_passed": consistency["consistency_passed"],
        }
        total_score += consistency["adjusted_marks"]
        max_total += rubric["max_marks"]
        confidence_sum += reasoning["confidence"]

    # ---------- Finalize ----------
    student["aiScore"] = round(total_score, 1)
    student["maxScore"] = float(paper.get("totalMarks") or max_total or 20.0)
    student["confidence"] = int(round((confidence_sum / len(report_questions)) * 100))
    student["status"] = "Pending Review"
    student["selfCheck"] = "Consistent"
    student["handwritingQuality"] = "Average"
    student["report"] = {
        "student_id": student_id,
        "status": "Pending Review",
        "ai_score": student["aiScore"],
        "max_score": student["maxScore"],
        "confidence": student["confidence"] / 100.0,
        "questions": report_questions,
    }

    save_db(db)
    append_log("grader", f"Pipeline complete: {student['aiScore']}/{student['maxScore']} for {student_id}.", "success")
    return student


def resolve_sheet_path(student):
    """Find the uploaded answer sheet path stored on the student record."""
    if student.get("filePath"):
        return student["filePath"]
    hint = student.get("questions", {}).get("q1", {}).get("handwritingMock", "")
    if hint.startswith("Uploaded file path: "):
        return hint.replace("Uploaded file path: ", "", 1)
    return None


def resolve_question_paper(db, paper_id):
    """Pick the question paper/rubric: linked paper first, else the default rubric."""
    paper = next((p for p in db.get("questionPapers", []) if p["id"] == paper_id), None)
    if paper:
        return paper
    return db.get("rubrics", [{}])[0]


def build_rubric(paper, question_number, packet):
    """Adapt a paper's rubric entry to the rubric agent contract."""
    entries = paper.get("questions", [])
    entry = None
    if entries:
        entry = entries[question_number - 1] if question_number - 1 < len(entries) else entries[-1]
    return {
        "question_text": (entry or {}).get("title", f"Question {question_number}"),
        "max_marks": (entry or {}).get("maxMarks", 10),
        "criteria": [
            {"text": c.get("text", ""), "marks": c.get("marks", 0)}
            for c in (entry or {}).get("criteria", [])
        ],
    }


def cohort_for(db, question_key):
    """Existing scores for the same question across the cohort (for consistency)."""
    cohort = []
    for s in db.get("students", []):
        q = s.get("questions", {}).get(question_key, {})
        marks = q.get("score", 0.0) or 0.0
        if marks > 0:
            cohort.append({"student_id": s["id"], "marks": marks})
    return cohort