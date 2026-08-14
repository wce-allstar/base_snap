# JSON_SCHEMA.md — Standardized Data Contracts

All agents exchange JSON only. These contracts are fixed; changes require updating this file and every affected agent.

---

## 1. OCR Agent

### Input

```json
{ "file_path": "/path/to/sheet.pdf" }
```

### Output

```json
{ "raw_text": "Question 1 ... Answer ..." }
```

---

## 2. Structuring Agent

### Input

```json
{
  "raw_text": "1. Explain TCP/IP ... 2. Explain DNS ...",
  "student_id": "CS2026-084"
}
```

### Output

```json
{
  "student_id": "CS2026-084",
  "questions": [
    { "question_number": 1, "answer": "TCP/IP is ..." },
    { "question_number": 2, "answer": "DNS is ..." }
  ]
}
```

---

## 3. Rubric Agent

### Input

```json
{
  "question": { "question_number": 1, "answer": "TCP/IP is ..." },
  "rubric": {
    "question_text": "Explain TCP/IP",
    "max_marks": 10,
    "criteria": [
      { "text": "Defines TCP.", "marks": 4 },
      { "text": "Defines IP.", "marks": 3 },
      { "text": "Explains layering.", "marks": 3 }
    ]
  }
}
```

### Output

```json
{
  "question_number": 1,
  "coverage": [
    { "criterion": "Defines TCP.", "status": "Fully Covered" },
    { "criterion": "Defines IP.", "status": "Partially Covered" },
    { "criterion": "Explains layering.", "status": "Not Covered" }
  ],
  "similarity": 0.87
}
```

`status` is one of: `"Fully Covered"`, `"Partially Covered"`, `"Not Covered"`.

---

## 4. Reasoning Agent

### Input

```json
{
  "question": { "question_number": 1, "answer": "TCP/IP is ..." },
  "rubric": { "question_text": "Explain TCP/IP", "max_marks": 10, "criteria": [] }
}
```

### Output

```json
{
  "question_number": 1,
  "reasoning_score": 8,
  "logic_issues": ["ACK sequence discussion missing."],
  "confidence": 0.91
}
```

---

## 5. Consistency Agent

### Input

```json
{
  "question_number": 1,
  "candidate_marks": 8,
  "cohort": [
    { "student_id": "CS2026-084", "marks": 8 },
    { "student_id": "CS2026-003", "marks": 9 }
  ]
}
```

### Output

```json
{
  "question_number": 1,
  "adjusted_marks": 8,
  "consistency_passed": true,
  "notes": "Within cohort variance."
}
```

---

## 6. Feedback Agent

### Input

```json
{
  "student_id": "CS2026-084",
  "question_number": 1,
  "marks": 8,
  "max_marks": 10,
  "coverage": [ { "criterion": "Defines TCP.", "status": "Fully Covered" } ],
  "reasoning": ["ACK sequence discussion missing."]
}
```

### Output

```json
{
  "strengths": ["Correct explanation of TCP handshake."],
  "missing": ["ACK sequence discussion."],
  "feedback_text": "Strengths: ... Missing: ... Marks: 8/10"
}
```

---

## 7. Final Report (produced by `pipeline_service`)

```json
{
  "student_id": "CS2026-084",
  "status": "Pending Review",
  "ai_score": 35.0,
  "max_score": 50,
  "confidence": 0.91,
  "handwriting_quality": "Average",
  "questions": [
    {
      "question_number": 1,
      "marks": 8,
      "max_marks": 10,
      "coverage": [ { "criterion": "Defines TCP.", "status": "Fully Covered" } ],
      "reasoning": ["ACK sequence discussion missing."],
      "confidence": 0.91,
      "feedback": {
        "strengths": ["Correct explanation of TCP handshake."],
        "missing": ["ACK sequence discussion."],
        "feedback_text": "Strengths: ... Missing: ... Marks: 8/10"
      }
    }
  ]
}
```

## Persistence mapping (student record in db.json)

Legacy frontend shape is preserved for compatibility:

| Report field          | Student record field                 |
| --------------------- | ------------------------------------ |
| `questions[n].marks`  | `questions["qN"]["score"]`           |
| `questions[n].max_marks` | `questions["qN"]["maxScore"]`     |
| `questions[n].coverage`  | `questions["qN"]["coverage"]`     |
| `questions[n].reasoning` | `questions["qN"]["justification"]` |
| `feedback.strengths`  | `questions["qN"]["strengths"]`       |
| `feedback.missing`    | `questions["qN"]["weaknesses"]`      |
| `ai_score`            | `aiScore`                            |
| `confidence`          | `confidence` (0-100 scale)           |