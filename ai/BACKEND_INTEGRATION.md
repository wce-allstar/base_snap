# Backend Integration Guide — AgenticEval AI

**For your backend colleague (on `feat/backend` branch)**

---

## 1. Quick Start

```bash
# In ai/ directory (separate service)
export GEMINI_API_KEY=your_key
uvicorn main:app --port 8000

# Your backend calls: POST http://localhost:8000/api/v1/evaluate
```

---

## 2. API Contract

### Endpoint
```
POST /api/v1/evaluate
Content-Type: multipart/form-data
```

### Request Fields (multipart/form-data)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | `UploadFile` | �� | PDF or image (PNG/JPEG/WebP) |
| `student_id` | `string` | �� | Student identifier |
| `exam_id` | `string` | �� | Exam identifier |
| `subject` | `string` | �� | Subject name |
| `question_paper_json` | `string` | �� | JSON-encoded `QuestionPaper` |
| `rubrics_json` | `string` | �� | JSON-encoded `dict[int, Rubric]` |

### Response
```json
{
  "report": { /* FinalReport object */ },
  "trace_id": "eval_1234567890",
  "processing_time_ms": 2341
}
```

---

## 3. Required JSON Structures

### 3.1 QuestionPaper (question_paper_json)
```json
{
  "questions": [
    {
      "number": 1,
      "text": "What is an operating system? Explain its main functions.",
      "max_marks": 10,
      "keywords": ["OS", "process management", "memory management"]
    },
    {
      "number": 2,
      "text": "Define deadlock. Explain the four necessary conditions.",
      "max_marks": 15,
      "keywords": ["deadlock", "mutual exclusion", "hold and wait"]
    }
  ]
}
```

### 3.2 Rubrics (rubrics_json) — Keyed by question_number
```json
{
  "1": {
    "model_answer": "An operating system (OS) is system software that manages computer hardware and software resources...",
    "key_points": [
      {"concept": "definition", "weight": 0.2, "required": true, "partial_credit": true},
      {"concept": "process management", "weight": 0.2, "required": false, "partial_credit": true},
      {"concept": "memory management", "weight": 0.2, "required": false, "partial_credit": true},
      {"concept": "file/device management", "weight": 0.2, "required": false, "partial_credit": true},
      {"concept": "security/ui", "weight": 0.2, "required": false, "partial_credit": true}
    ],
    "marking_scheme": {
      "type": "points",
      "partial_credit_enabled": true,
      "deduction_rules": []
    }
  },
  "2": {
    "model_answer": "Deadlock is a situation where a set of processes are blocked...",
    "key_points": [
      {"concept": "definition", "weight": 0.2, "required": true, "partial_credit": true},
      {"concept": "mutual exclusion", "weight": 0.2, "required": false, "partial_credit": true},
      {"concept": "hold and wait", "weight": 0.2, "required": false, "partial_credit": true},
      {"concept": "no preemption", "weight": 0.2, "required": false, "partial_credit": true},
      {"concept": "circular wait", "weight": 0.2, "required": false, "partial_credit": true}
    ],
    "marking_scheme": {
      "type": "points",
      "partial_credit_enabled": true,
      "deduction_rules": []
    }
  }
}
```

**Critical:** `key_points` weights **must sum to 1.0** per question.

---

## 4. Python Client Example

```python
import httpx
import json
from pathlib import Path

async def evaluate_answer_sheet(
    file_path: str,
    student_id: str,
    exam_id: str,
    subject: str,
    question_paper: dict,
    rubrics: dict,
) -> dict:
    url = "http://localhost:8000/api/v1/evaluate"
    
    files = {"file": open(file_path, "rb")}
    data = {
        "student_id": student_id,
        "exam_id": exam_id,
        "subject": subject,
        "question_paper_json": json.dumps(question_paper),
        "rubrics_json": json.dumps({str(k): v for k, v in rubrics.items()}),  # keys as strings
    }
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(url, files=files, data=data)
        resp.raise_for_status()
        return resp.json()

# Usage
result = await evaluate_answer_sheet(
    file_path="answer_sheet.pdf",
    student_id="STU-001",
    exam_id="MID-SEM-CS301",
    subject="Operating Systems",
    question_paper={...},  # from 3.1
    rubrics={...},         # from 3.2
)
print(result["report"]["percentage"])  # 70.0
```

---

## 5. Response Structure (FinalReport)

```json
{
  "student_id": "STU-001",
  "exam_id": "MID-SEM-CS301",
  "subject": "Operating Systems",
  "total_marks": 24.5,
  "total_max_marks": 35,
  "percentage": 70.0,
  "per_question": [
    {
      "question_number": 1,
      "marks": 7.0,
      "max_marks": 10,
      "percentage": 70.0,
      "confidence": 0.92,
      "reasoning": ["Correctly identifies hardware management", "Missing security aspect"],
      "feedback": "Good job identifying hardware management. To improve, discuss security..."
    }
  ],
  "consistency_flags": [],
  "overall_feedback": "Good understanding demonstrated. Strong areas: Q1, Q2.",
  "confidence_score": 0.89,
  "generated_at": "2026-08-14T10:30:00Z",
  "metadata": {
    "trace_id": "eval_1234567890",
    "total_latency_ms": 2341,
    "stage_latencies": {"ocr": 450, "evaluate": 1800, ...}
  }
}
```

---

## 6. Error Responses

| Status | Code | Meaning |
|--------|------|---------|
| 400 | `INVALID_INPUT` | Bad JSON, missing fields, unsupported file type |
| 500 | `PIPELINE_ERROR` | AI pipeline failure (OCR, LLM, etc.) |
| 500 | `EVALUATION_FAILED` | LLM evaluation error |
| 503 | `SERVICE_UNAVAILABLE` | AI service down |

```json
{
  "detail": {
    "code": "EVALUATION_FAILED",
    "message": "Gemini API error: ...",
    "details": {"status_code": 429}
  }
}
```

---

## 7. Health Check

```bash
GET http://localhost:8000/api/v1/health
# {"status": "healthy", "service": "agenticeval-ai", "version": "0.1.0"}
```

---

## 8. Deployment Notes

- **AI service runs separately** on port 8000 (or configured port)
- **Backend calls AI via HTTP** — no shared memory, no direct imports
- **Set `GEMINI_API_KEY`** in AI service environment
- **CORS enabled** — add your frontend origin to `ALLOWED_ORIGINS` env var
- **Timeouts:** AI pipeline can take 10-60s; set backend proxy timeout ≥ 120s

---

## 9. Shared Types Reference

All Pydantic models are in `ai/schemas.py`. Key imports:

```python
from schemas import (
    QuestionPaper, QuestionMeta,
    Rubric, KeyPoint, MarkingScheme, MarkingSchemeType,
    FinalReport, QuestionReport, ConsistencyFlag,
    EvaluateResponse, SourceType,
)
```

---

## 10. Checklist for Backend

- [ ] AI service running on accessible host:port
- [ ] `GEMINI_API_KEY` configured in AI service
- [ ] Multipart request with all 6 fields
- [ ] `question_paper_json` and `rubrics_json` are valid JSON strings
- [ ] Rubric key_points weights sum to 1.0 per question
- [ ] Backend timeout ≥ 120s
- [ ] Error handling for 400/500/503 responses
- [ ] Parse `report.percentage` and `report.per_question` for frontend