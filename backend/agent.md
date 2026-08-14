# AI-Assisted Agentic Evaluation System
## Backend Architecture Documentation

### Objective

The backend acts as the central coordinator between the Frontend and AI modules. It manages answer sheet uploads, stores data, invokes AI agents, tracks evaluation progress, and serves results to examiners.

The goal is to keep the architecture **simple, modular, scalable, and easy to demonstrate** during project presentations.

---

# System Architecture

```text
Frontend (React)
       |
       v
Backend API (FastAPI)
       |
       +-------------------+
       |                   |
       v                   v
 Database            AI Services
(PostgreSQL)         (Agents)
       |
       v
 Examiner Dashboard
```

---

# Responsibilities of Backend

The backend is responsible for:

- User authentication
- Answer sheet upload management
- File storage handling
- Communication with AI agents
- Database operations
- Evaluation tracking
- Result generation
- Examiner review workflow

The backend does **not** perform actual AI evaluation. It only coordinates the evaluation pipeline.

---

# Technology Stack

## Backend Framework

### FastAPI (Python)

Why FastAPI?

- Easy integration with AI modules
- High performance
- Automatic API documentation
- Async support
- Simple learning curve

---

## Database

### PostgreSQL

Used for storing:

- Users
- Answer sheets
- Questions
- Rubrics
- Evaluation results
- Feedback
- Review history

---

## File Storage

Stores uploaded answer sheets.

Options:

- Local Storage (for project/demo)
- MinIO
- AWS S3

For the first version, local storage is sufficient.

---

# Backend Workflow

## Step 1: Upload Answer Sheet

Student or examiner uploads:

```text
answer_sheet.pdf
```

### API

```http
POST /upload
```

### Backend Actions

1. Receive file
2. Store file
3. Create database record
4. Generate Sheet ID

### Response

```json
{
  "sheet_id": 101,
  "status": "uploaded"
}
```

---

## Step 2: Start Evaluation

### API

```http
POST /evaluate/{sheet_id}
```

### Backend Actions

1. Fetch uploaded file
2. Create evaluation job
3. Send file to OCR Agent

---

## Step 3: OCR Agent

### Purpose

Extract text from handwritten or typed answer sheets.

### Input

```text
PDF/Image
```

### Output

```json
{
    "raw_text": "Question 1 ... Answer ..."
}
```

### Suggested Tools

- Tesseract OCR
- EasyOCR

---

## Step 4: Answer Structuring Agent

### Purpose

Separate answers according to question numbers.

### Example

Input:

```text
1. Explain TCP/IP

TCP/IP is ...

2. Explain DNS

DNS is ...
```

Output:

```json
{
  "Q1": "TCP/IP is ...",
  "Q2": "DNS is ..."
}
```

---

## Step 5: Rubric Mapping Agent

### Purpose

Compare student answers with:

- Model answers
- Rubrics
- Marking scheme

Instead of keyword matching, semantic similarity is used.

### Output

```json
{
  "question": "Q1",
  "score": 7,
  "max_score": 10
}
```

---

## Step 6: Reasoning Agent

### Purpose

Check:

- Concept understanding
- Logical flow
- Completeness
- Partial correctness
- Paraphrased answers

### Output

```json
{
  "reasoning_score": 8,
  "confidence": 0.91
}
```

---

## Step 7: Consistency Agent

### Purpose

Ensure fairness across all answer sheets.

Checks:

- Similar answers receive similar marks
- No scoring anomalies
- Uniform marking standards

### Output

```json
{
  "adjusted_score": 8,
  "consistency_passed": true
}
```

---

## Step 8: Feedback Agent

### Purpose

Generate explainable feedback.

Example:

```text
Strengths:
- Correct explanation of TCP handshake

Missing:
- ACK sequence discussion

Marks:
8/10
```

---

## Step 9: Human Review

Examiner reviews AI-generated results.

### Dashboard Displays

- Student Answer
- AI Score
- Confidence Score
- Feedback
- Suggested Corrections

### Actions

```text
Approve
Edit
Reject
```

---

## Step 10: Final Result

After approval:

```text
Marks Finalized
Report Generated
Export Available
```

---

# Database Design

## Users Table

```sql
users
-----
id
name
email
role
created_at
```

---

## Answer Sheets Table

```sql
answer_sheets
-------------
id
student_id
file_path
status
uploaded_at
```

Status Values:

```text
UPLOADED
PROCESSING
REVIEW
APPROVED
COMPLETED
```

---

## Questions Table

```sql
questions
---------
id
subject
question_text
max_marks
rubric
model_answer
```

---

## Evaluations Table

```sql
evaluations
-----------
id
sheet_id
question_id
ai_marks
confidence_score
human_marks
status
```

---

## Feedback Table

```sql
feedback
--------
id
evaluation_id
feedback_text
generated_at
```

---

# Recommended Folder Structure

```text
backend/
│
├── app.py
│
├── routes/
│   ├── upload.py
│   ├── evaluation.py
│   ├── review.py
│   └── report.py
│
├── services/
│   ├── file_service.py
│   ├── ocr_service.py
│   ├── grading_service.py
│   ├── feedback_service.py
│   └── review_service.py
│
├── agents/
│   ├── ocr_agent.py
│   ├── structuring_agent.py
│   ├── rubric_agent.py
│   ├── reasoning_agent.py
│   ├── consistency_agent.py
│   └── feedback_agent.py
│
├── database/
│   ├── connection.py
│   ├── models.py
│   └── schemas.py
│
├── storage/
│
├── utils/
│
└── requirements.txt
```

---

# API Endpoints

## Upload Answer Sheet

```http
POST /upload
```

---

## Start Evaluation

```http
POST /evaluate/{sheet_id}
```

---

## Get Evaluation Status

```http
GET /evaluation/{sheet_id}
```

---

## Get Feedback

```http
GET /feedback/{sheet_id}
```

---

## Approve Evaluation

```http
POST /review/{sheet_id}
```

---

## Export Report

```http
GET /report/{sheet_id}
```

---

# Development Plan

## Phase 1

Build:

- FastAPI setup
- Database connection
- File upload API

Goal:

Upload answer sheets successfully.

---

## Phase 2

Build:

- OCR integration
- Answer extraction

Goal:

Convert answer sheets into structured text.

---

## Phase 3

Build:

- AI evaluation pipeline
- Scoring system

Goal:

Generate marks automatically.

---

## Phase 4

Build:

- Examiner dashboard integration
- Review workflow

Goal:

Allow human verification.

---

## Phase 5

Build:

- Reports
- Analytics
- Export functionality

Goal:

Generate final evaluation reports.

---

# Key Design Principle

The backend should act as an **orchestrator**, not an evaluator.

Its primary responsibility is to:

1. Receive answer sheets.
2. Store and manage data.
3. Coordinate AI agents.
4. Track evaluation progress.
5. Serve results to the frontend.
6. Support human review and approval.

Keeping the backend modular ensures future AI models or agents can be replaced without changing the overall system architecture.