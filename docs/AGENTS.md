# AGENTS.md — Agent Responsibilities & Contracts

Every agent in this system is a **pure function over JSON**:

- It receives exactly one input payload (JSON).
- It returns exactly one output payload (JSON).
- It never knows how other modules work.
- It never imports Flask, routes, or the database.

---

## 1. OCR Agent

| Field        | Value                                        |
| ------------ | -------------------------------------------- |
| **Module**   | `backend/agents/ocr_agent.py`                |
| **Input**    | `{ "file_path": "/path/to/sheet.pdf" }`      |
| **Output**   | `{ "raw_text": "..." }`                      |
| **Never knows** | Rubrics, marks, prompts, or who uploaded the file. |

Extracts text (typed or handwritten) from a PDF or image using a Gemini vision model.

---

## 2. Structuring Agent

| Field        | Value                                                                                     |
| ------------ | ----------------------------------------------------------------------------------------- |
| **Module**   | `backend/agents/structuring_agent.py`                                                       |
| **Input**    | `{ "raw_text": "...", "student_id": "CS2026-084" }`                                       |
| **Output**   | `{ "student_id": "CS2026-084", "questions": [ { "question_number": 1, "answer": "..." } ] }` |
| **Never knows** | Rubrics, marks, or where the text came from (PDF, image, paste).                         |

Cleans noisy OCR output and splits it into numbered question packets.

---

## 3. Rubric Agent

| Field        | Value                                                                                                                       |
| ------------ | --------------------------------------------------------------------------------------------------------------------------- |
| **Module**   | `backend/agents/rubric_agent.py`                                                                                            |
| **Input**    | `{ "question": { "question_number": 1, "answer": "..." }, "rubric": { "question_text": "...", "max_marks": 10, "criteria": [ { "text": "...", "marks": 3 } ] } }` |
| **Output**   | `{ "question_number": 1, "coverage": [ { "criterion": "...", "status": "Fully Covered" \| "Partially Covered" \| "Not Covered" } ], "similarity": 0.87 }` |
| **Never knows** | How OCR worked, how scores are finalized, or other students.                                                            |

Semantic (not keyword) matching of the answer against each rubric criterion.

---

## 4. Reasoning Agent

| Field        | Value                                                                        |
| ------------ | ---------------------------------------------------------------------------- |
| **Module**   | `backend/agents/reasoning_agent.py`                                          |
| **Input**    | `{ "question": { "question_number": 1, "answer": "..." }, "rubric": { ... } }` |
| **Output**   | `{ "question_number": 1, "reasoning_score": 8, "logic_issues": [ "..." ], "confidence": 0.91 }` |
| **Never knows** | It only audits logic; it never decides final marks.                       |

Checks concept understanding, logical flow, completeness, partial correctness, and paraphrased answers.

---

## 5. Consistency Agent

| Field        | Value                                                                                       |
| ------------ | ------------------------------------------------------------------------------------------- |
| **Module**   | `backend/agents/consistency_agent.py`                                                        |
| **Input**    | `{ "question_number": 1, "candidate_marks": 8, "cohort": [ { "student_id": "...", "marks": 8 } ] }` |
| **Output**   | `{ "question_number": 1, "adjusted_marks": 8, "consistency_passed": true, "notes": "..." }`   |
| **Never knows** | What the answer text was; it only sees score distributions.                              |

Ensures fairness: similar answers receive similar marks, no scoring anomalies, uniform standards.

---

## 6. Feedback Agent

| Field        | Value                                                                   |
| ------------ | ----------------------------------------------------------------------- |
| **Module**   | `backend/agents/feedback_agent.py`                                      |
| **Input**    | `{ "student_id": "...", "question_number": 1, "marks": 8, "max_marks": 10, "reasoning": [ "..." ], "coverage": [ { "criterion": "...", "status": "..." } ] }` |
| **Output**   | `{ "strengths": [ "..." ], "missing": [ "..." ], "feedback_text": "..." }` |
| **Never knows** | Whether the answer came from a PDF, image, frontend upload, or API request. |

Generates explainable, examiner-style feedback for each question.

---

# Core Development Rule

> No module knows how another module works. Every module knows only:
> - What input it receives.
> - What output it returns.

Agents must never import Flask, routes, or the database. Services may call agents.
Routes may call services only. This keeps the system modular, testable, and swappable.
