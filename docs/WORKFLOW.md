# WORKFLOW.md — Development Milestones & Process

## Milestone 1 — OCR Extraction

```text
Local PDF/Image -> OCR Agent -> Print Extracted Text to Terminal
```

Goal: verify the system can read an answer sheet and extract contents.

Done when: `GEMINI_API_KEY=... python -m backend.agents.ocr_agent sample_student_paper.pdf`
prints the text of the answer sheet to the terminal.

---

## Milestone 2 — Data Structuring

```text
Extracted Text -> Cleaner -> Question Splitter -> Structured JSON Packets
```

Goal: transform raw OCR text into structured, machine-readable JSON packets
(`{ "student_id", "questions": [ { "question_number", "answer" } ] }`).

---

## Milestone 3 — AI Evaluation

```text
Question Packet + Rubric -> LLM Evaluation Agent -> Marks + Reasoning
```

Goal: evaluate a student's answer against the rubric and generate explainable
marks with reasoning and confidence.

---

## Milestone 4 — Complete AI Pipeline

```text
PDF/Image -> OCR -> Cleaner -> Splitter -> Evaluation -> Feedback -> Final Report
```

Goal: connect all AI modules into a single end-to-end evaluation pipeline
(`services/pipeline_service.py`), reachable via `POST /api/evaluate`.

---

## Milestone 5 — Web Integration

```text
Frontend -> FastAPI/Flask Backend -> AI Pipeline -> LLM API
```

Goal: expose the pipeline through the API and show results in the web app.

Done when: upload a script in the UI, run evaluate, review (approve/edit), and
the dashboard shows real OCR text + real grades.

---

## Process

1. Every agent is a pure JSON function (see AGENTS.md / JSON_SCHEMA.md).
2. Backend must act as orchestrator, not evaluator.
3. All endpoints must preserve behavior across refactors (regression check via manual API calls).
4. No module imports another module's internals.
5. Tests and docs accompany each milestone.

---

## Team Responsibilities

| Member   | Responsibility                          |
| -------- | --------------------------------------- |
| Member 1 | OCR & Image Processing                  |
| Member 2 | Text Cleaner & Question Splitter        |
| Member 3 | Evaluation Agent & Prompt Engineering   |
| Member 4 | Backend API & Pipeline Orchestrator     |
| Member 5 | Frontend & Dashboard                    |
| Member 6 | Testing, Documentation & Integration    |
