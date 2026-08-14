# Development Roadmap

## Milestone 1 - OCR Extraction

Workflow

```text
Local PDF/Image
      │
      ▼
OCR Agent
      │
      ▼
Print Extracted Text to Terminal
```

Goal

Verify that the system can successfully read an answer sheet and extract its contents.

---

## Milestone 2 - Data Structuring

Workflow

```text
Extracted Text
      │
      ▼
Cleaner Agent
      │
      ▼
Question Splitter
      │
      ▼
Structured JSON Packets
```

Example Output

```json
{
  "student_id": "TEMP",
  "questions": [
    {
      "question_number": 1,
      "answer": "Operating system is..."
    },
    {
      "question_number": 2,
      "answer": "Deadlock is..."
    }
  ]
}
```

Goal

Transform raw OCR text into structured, machine-readable data.

---

## Milestone 3 - AI Evaluation

Workflow

```text
Question Packet
      │
      ▼
Rubric
      │
      ▼
LLM Evaluation Agent
      │
      ▼
Marks + Reasoning
```

Example Output

```json
{
  "question_number": 1,
  "marks": 8,
  "max_marks": 10,
  "reasoning": [
    "Definition is correct.",
    "Diagram missing."
  ],
  "confidence": 0.94
}
```

Goal

Evaluate a student's answer against the rubric and generate explainable marks.

---

## Milestone 4 - Complete AI Pipeline

Workflow

```text
PDF/Image
    │
    ▼
OCR Agent
    │
    ▼
Cleaner Agent
    │
    ▼
Question Splitter
    │
    ▼
Evaluation Agent
    │
    ▼
Feedback Agent
    │
    ▼
Final Report
```

Goal

Connect all AI modules into a single end-to-end evaluation pipeline.

---

## Milestone 5 - Web Integration

Workflow

```text
Frontend
    │
    ▼
FastAPI Backend
    │
    ▼
AI Pipeline
    │
    ▼
LLM API
```

Goal

Expose the AI pipeline through an API and integrate it with the web application.

---

# Team Responsibilities

| Member   | Responsibility                        |
| -------- | ------------------------------------- |
| Member 1 | OCR & Image Processing                |
| Member 2 | Text Cleaner & Question Splitter      |
| Member 3 | Evaluation Agent & Prompt Engineering |
| Member 4 | Backend API & Pipeline Orchestrator   |
| Member 5 | Frontend & Dashboard                  |
| Member 6 | Testing, Documentation & Integration  |

---

# Core Development Rule

No module should know how another module works.

Every module should only know:

* What input it receives.
* What output it returns.

Example

OCR Agent

Input

* PDF
* Image

Output

* Extracted Text

The OCR agent should never know anything about rubrics, marks, prompts, or evaluation.

Evaluation Agent

Input

* Question Packet
* Rubric

Output

* Marks
* Reasoning
* Confidence

The Evaluation Agent should never know whether the question originated from a PDF, image, frontend upload, or API request.

This separation ensures the system remains modular, testable, scalable, and easy to maintain.

---

# Recommended Documentation Structure

```text
docs/
├── AGENTS.md
├── ARCHITECTURE.md
├── PIPELINE.md
├── JSON_SCHEMA.md
├── PROMPTS.md
└── WORKFLOW.md
```

Purpose

* AGENTS.md – Responsibilities and contracts for every AI agent.
* ARCHITECTURE.md – Overall system design and module interactions.
* PIPELINE.md – End-to-end execution flow.
* JSON_SCHEMA.md – Standardized data exchanged between modules.
* PROMPTS.md – Prompt templates used by LLM-based agents.
* WORKFLOW.md – Development milestones and implementation process.
