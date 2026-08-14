# PIPELINE.md — End-to-End Execution Flow

## Pipeline

```text
PDF/Image
    |
    v
OCR Agent (Gemini vision)          -> raw_text
    |
    v
Structuring Agent                   -> question packets
    |
    v
Rubric Agent                        -> coverage per criterion
    |
    v
Reasoning Agent                     -> reasoning score + logic issues
    |
    v
Consistency Agent                   -> adjusted marks
    |
    v
Feedback Agent                      -> strengths / missing / feedback
    |
    v
Final Report (JSON)
```

## Stage Details

### Stage 1 — OCR

- Reads the uploaded file from `uploads/`.
- PDFs are rendered page-by-page and passed to Gemini vision; images are passed directly.
- Output: `{ "raw_text": "..." }`.
- Success criteria: extracted text is printed/visible in the frontend workspace.

### Stage 2 — Structuring

- Cleans OCR noise (headers, page numbers, [UNCERTAIN_OCR] markers).
- Splits text by question number into packets.
- Output: `{ "student_id": "CS2026-084", "questions": [ { "question_number": 1, "answer": "..." } ] }`.

### Stage 3 — Rubric Mapping

- For each question packet, load the matching rubric from the question paper.
- Semantic similarity match against each criterion.
- Output: `{ "question_number": 1, "coverage": [...], "similarity": 0.87 }`.

### Stage 4 — Reasoning Audit

- Checks logic flow, completeness, partial correctness, paraphrasing.
- Output: `{ "question_number": 1, "reasoning_score": 8, "logic_issues": [...], "confidence": 0.91 }`.

### Stage 5 — Consistency Check

- Compares the candidate marks against the cohort's existing scores for the same question.
- Flags drift / anomalies, may adjust marks.
- Output: `{ "question_number": 1, "adjusted_marks": 8, "consistency_passed": true }`.

### Stage 6 — Feedback

- Produces explainable examiner-style feedback per question.
- Output: `{ "strengths": [...], "missing": [...], "feedback_text": "..." }`.

### Stage 7 — Final Report

`pipeline_service` assembles the report and persists it on the student record:

```json
{
  "student_id": "CS2026-084",
  "status": "Pending Review",
  "questions": [
    {
      "question_number": 1,
      "marks": 8,
      "max_marks": 10,
      "coverage": [ { "criterion": "...", "status": "Fully Covered" } ],
      "reasoning": [ "Definition is correct.", "Diagram missing." ],
      "confidence": 0.94,
      "feedback": { "strengths": [...], "missing": [...], "feedback_text": "..." }
    }
  ]
}
```

## Failure Handling

- Missing API key -> HTTP 503 with a clear message (`Gemini API key required`).
- Gemini call failure -> log to the failing agent's trail, abort evaluation with HTTP 502 and the error text.
- No mock fallback. Grading is real Gemini only.
