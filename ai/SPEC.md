# AgenticEval — AI Specification

**Version:** 1.0  
**Branch:** `feat/ai`  
**Owner:** AI Team  
**Last Updated:** 2026-08-14

---

## 1. Overview

AgenticEval is a multi-agent pipeline that evaluates handwritten/typed subjective answer sheets end-to-end. The system uses specialized LLM agents coordinated through a deterministic orchestrator to achieve human-like grading with explainable reasoning.

**Core Principle:** *No module knows how another works — only its input/output contract.*

---

## 2. Architecture

```
��─────────────────────────────────────────────────────────────────────────────��
│                            AI PIPELINE ORCHESTRATOR                         │
│  (deterministic flow control, error handling, retry logic, observability)  │
��─────────────────────────────────────────────────────────────────────────────��
                                      │
        ��─────────────────────────────��─────────────────────────────��
        ��                             ��                             ��
��───────────────��             ��───────────────��             ��───────────────��
│  OCR AGENT    │             │  CLEANER      │             │  SPLITTER     │
│  (digitize)   │────────────��│  AGENT        │────────────��│  AGENT        │
│               │   raw text  │  (normalize)  │  clean text │  (structure)  │
��───────────────��             └───────────────��             └───────────────��
                                                                       │
                                                                       ��
                                                             ��───────────────��
                                                             │  EVALUATION   │
                                                             │  AGENT        │
                                                             │  (grade)      │
                                                             └───────────────��
                                                                       │
                                                                       ��
                                                             ��───────────────��
                                                             │  FEEDBACK     │
                                                             │  AGENT        │
                                                             │  (explain)    │
                                                             └───────────────��
                                                                       │
                                                                       ��
                                                             ��───────────────��
                                                             │  AGGREGATOR   │
                                                             │  (report)     │
                                                             └───────────────��
```

**Data Flow:**
```
PDF/Image → raw_text → clean_text → QuestionPacket[] → EvaluationResult[] → FinalReport
```

---

## 3. Agent Contracts

### 3.1 OCR Agent

| Aspect | Specification |
|--------|---------------|
| **Input** | `bytes` (PDF or image), `source_type: "pdf" \| "image"` |
| **Output** | `OCRResult` |
| **Responsibility** | Extract text from documents using OCR. No understanding of content. |
| **Error Modes** | `OCR_FAILED`, `UNSUPPORTED_FORMAT`, `EMPTY_DOCUMENT` |
| **Retry** | Yes (transient API failures) |
| **Config** | `language_hints: string[]`, `dpi: int = 300` |

```python
# Output schema
class OCRResult(BaseModel):
    raw_text: str
    page_count: int
    confidence: float  # 0-1 average OCR confidence
    metadata: dict     # engine_used, processing_time_ms, etc.
```

---

### 3.2 Cleaner Agent

| Aspect | Specification |
|--------|---------------|
| **Input** | `raw_text: str`, `config: CleanerConfig` |
| **Output** | `CleanedText` |
| **Responsibility** | Normalize OCR artifacts: fix line breaks, remove headers/footers, handle hyphenation, decode garbled chars. |
| **Error Modes** | `CLEANING_FAILED` |
| **Retry** | Yes (deterministic, usually succeeds on retry) |
| **Config** | `remove_page_numbers: bool`, `remove_headers_footers: bool`, `fix_hyphenation: bool` |

```python
class CleanedText(BaseModel):
    text: str
    transformations_applied: list[str]
    metadata: dict
```

---

### 3.3 Splitter Agent

| Aspect | Specification |
|--------|---------------|
| **Input** | `clean_text: str`, `question_paper: QuestionPaper` (optional context) |
| **Output** | `QuestionPacket[]` |
| **Responsibility** | Segment text into individual Q/A pairs. Detect question numbers, match to paper structure. |
| **Error Modes** | `SPLIT_FAILED`, `QUESTION_MISMATCH`, `EMPTY_ANSWER` |
| **Retry** | No (deterministic parsing) |
| **Config** | `strict_matching: bool`, `min_answer_length: int` |

```python
class QuestionPacket(BaseModel):
    question_number: int
    question_text: str           # from question paper
    max_marks: int               # from rubric
    student_answer: str          # extracted
    metadata: dict               # confidence, page_ref, etc.

class QuestionPaper(BaseModel):
    questions: list[QuestionMeta]
    
class QuestionMeta(BaseModel):
    number: int
    text: str
    max_marks: int
    keywords: list[str] = []     # optional hints for matching
```

---

### 3.4 Evaluation Agent

| Aspect | Specification |
|--------|---------------|
| **Input** | `packet: QuestionPacket`, `rubric: Rubric` |
| **Output** | `EvaluationResult` |
| **Responsibility** | Semantic comparison of student answer vs model answer/rubric. Assess: conceptual correctness, reasoning flow, coverage, partial credit. |
| **Error Modes** | `EVALUATION_FAILED`, `LLM_TIMEOUT`, `INVALID_RESPONSE` |
| **Retry** | Yes (exponential backoff, max 3) |
| **Config** | `model: str`, `temperature: float = 0.1`, `strict_json: bool = True` |

```python
class Rubric(BaseModel):
    model_answer: str
    key_points: list[KeyPoint]
    marking_scheme: MarkingScheme
    
class KeyPoint(BaseModel):
    concept: str
    weight: float              # 0-1, sums to 1 per question
    required: bool             # if true, missing = major deduction
    partial_credit: bool       # allow partial for this point

class MarkingScheme(BaseModel):
    type: Literal["points", "holistic", "checklist"]
    partial_credit_enabled: bool
    deduction_rules: list[str] = []

class EvaluationResult(BaseModel):
    question_number: int
    marks_awarded: float
    max_marks: int
    confidence: float          # 0-1
    reasoning: list[str]       # human-readable justifications
    key_point_scores: list[KeyPointScore]
    metadata: dict             # model, tokens, latency_ms
    
class KeyPointScore(BaseModel):
    concept: str
    awarded_weight: float      # 0 to key_point.weight
    reasoning: str
```

**Prompt Strategy:** Structured prompt with few-shot examples, explicit rubric injection, chain-of-thought reasoning, strict JSON output.

---

### 3.5 Feedback Agent

| Aspect | Specification |
|--------|---------------|
| **Input** | `packet: QuestionPacket`, `evaluation: EvaluationResult`, `tone: "constructive" \| "encouraging" \| "formal"` |
| **Output** | `FeedbackResult` |
| **Responsibility** | Generate personalized, actionable feedback for student and examiner. Highlight strengths, gaps, specific improvements. |
| **Error Modes** | `FEEDBACK_FAILED` |
| **Retry** | Yes |
| **Config** | `include_exemplar: bool`, `max_length: int` |

```python
class FeedbackResult(BaseModel):
    question_number: int
    student_feedback: str      # for student
    examiner_notes: str        # for examiner review
    strengths: list[str]
    improvements: list[str]
    exemplar_snippet: str | None
    metadata: dict
```

---

### 3.6 Aggregator Agent

| Aspect | Specification |
|--------|---------------|
| **Input** | `results: list[EvaluationResult]`, `feedbacks: list[FeedbackResult]`, `student_meta: StudentMeta` |
| **Output** | `FinalReport` |
| **Responsibility** | Compile final report: total marks, percentage, per-question breakdown, consistency checks, flag anomalies. |
| **Error Modes** | `AGGREGATION_FAILED` |
| **Retry** | No |
| **Config** | `consistency_threshold: float = 0.15` |

```python
class StudentMeta(BaseModel):
    student_id: str
    exam_id: str
    subject: str
    total_max_marks: int

class FinalReport(BaseModel):
    student_id: str
    exam_id: str
    subject: str
    total_marks: float
    total_max_marks: int
    percentage: float
    per_question: list[QuestionReport]
    consistency_flags: list[ConsistencyFlag]
    overall_feedback: str
    confidence_score: float    # aggregate confidence
    generated_at: datetime
    metadata: dict
    
class QuestionReport(BaseModel):
    question_number: int
    marks: float
    max_marks: int
    percentage: float
    confidence: float
    reasoning: list[str]
    feedback: str

class ConsistencyFlag(BaseModel):
    type: Literal["score_variance", "confidence_drop", "pattern_anomaly"]
    description: str
    severity: Literal["low", "medium", "high"]
    affected_questions: list[int]
```

---

## 4. JSON Schemas (Inter-Module Contracts)

All schemas defined in `schemas.py` using Pydantic v2. **These are the ONLY shared types between agents.**

### 4.1 Envelope (for pipeline messaging)

```python
class PipelineEnvelope(BaseModel):
    stage: Literal["ocr", "clean", "split", "evaluate", "feedback", "aggregate"]
    status: Literal["success", "error", "partial"]
    payload: Any
    error: ErrorInfo | None = None
    trace_id: str
    timestamp: datetime
```

---

## 5. Prompt Templates

Located in `prompts/` directory. Each agent has its own prompt file.

### 5.1 Evaluation Agent Prompt Structure

```markdown
# SYSTEM
You are an expert academic evaluator. Grade the student's answer against the provided rubric.

# RUBRIC
Question: {question_text}
Max Marks: {max_marks}
Model Answer: {model_answer}
Key Points: {key_points_json}
Marking Scheme: {marking_scheme_json}

# STUDENT ANSWER
{student_answer}

# INSTRUCTIONS
1. Evaluate EACH key point independently. Award weight 0 to key_point.weight.
2. Consider: conceptual accuracy, reasoning completeness, coverage, partial credit.
3. Output ONLY valid JSON matching EvaluationResult schema.
4. Reasoning must be specific, cite evidence from student answer.

# OUTPUT SCHEMA
{EvaluationResult_json_schema}
```

### 5.2 Feedback Agent Prompt Structure

```markdown
# SYSTEM
You are a supportive academic tutor. Generate personalized feedback.

# CONTEXT
Question: {question_text}
Student Answer: {student_answer}
Marks: {marks_awarded}/{max_marks}
Evaluation Reasoning: {reasoning}

# INSTRUCTIONS
1. Student feedback: encouraging, specific, actionable.
2. Examiner notes: technical, highlight grading rationale.
3. Identify 2-3 strengths and 2-3 improvements.
4. Output ONLY valid JSON matching FeedbackResult schema.
```

---

## 6. Pipeline Orchestrator

**File:** `pipeline.py`

```python
class AIPipeline:
    def __init__(self, config: PipelineConfig):
        self.ocr = OCRAgent(config.ocr)
        self.cleaner = CleanerAgent(config.cleaner)
        self.splitter = SplitterAgent(config.splitter)
        self.evaluator = EvaluationAgent(config.evaluator)
        self.feedback = FeedbackAgent(config.feedback)
        self.aggregator = AggregatorAgent(config.aggregator)
    
    async def evaluate(self, input: PipelineInput) -> FinalReport:
        # 1. OCR
        ocr_result = await self.ocr.process(input.file_bytes, input.source_type)
        
        # 2. Clean
        clean_result = await self.cleaner.process(ocr_result.raw_text)
        
        # 3. Split
        packets = await self.splitter.process(clean_result.text, input.question_paper)
        
        # 4. Evaluate (parallel per question)
        eval_results = await asyncio.gather(*[
            self.evaluator.process(p, input.rubrics[p.question_number])
            for p in packets
        ])
        
        # 5. Feedback (parallel per question)
        feedback_results = await asyncio.gather(*[
            self.feedback.process(p, e)
            for p, e in zip(packets, eval_results)
        ])
        
        # 6. Aggregate
        report = await self.aggregator.process(
            eval_results, feedback_results, input.student_meta
        )
        
        return report
```

**Error Handling:** Each stage wraps errors in `PipelineEnvelope` with stage info. Pipeline stops on critical errors, continues with `partial` on non-critical.

---

## 7. Configuration

**File:** `config.yaml`

```yaml
ocr:
  engine: "gemini" | "tesseract"
  language_hints: ["en"]
  dpi: 300

cleaner:
  remove_page_numbers: true
  remove_headers_footers: true
  fix_hyphenation: true

splitter:
  strict_matching: true
  min_answer_length: 10

evaluator:
  model: "gemini-2.0-flash"
  temperature: 0.1
  max_retries: 3
  timeout_seconds: 60

feedback:
  tone: "constructive"
  include_exemplar: true
  max_length: 500

aggregator:
  consistency_threshold: 0.15

pipeline:
  parallel_evaluation: true
  max_concurrent: 5
```

---

## 8. Implementation Plan

| Phase | Deliverable | Files |
|-------|-------------|-------|
| 1 | Project scaffolding, schemas, config | `schemas.py`, `config.yaml`, `pyproject.toml` |
| 2 | OCR Agent | `agents/ocr_agent.py` |
| 3 | Cleaner Agent | `agents/cleaner_agent.py` |
| 4 | Splitter Agent | `agents/splitter_agent.py` |
| 5 | Evaluation Agent | `agents/evaluation_agent.py`, `prompts/evaluation.md` |
| 6 | Feedback Agent | `agents/feedback_agent.py`, `prompts/feedback.md` |
| 7 | Aggregator Agent | `agents/aggregator_agent.py` |
| 8 | Pipeline Orchestrator | `pipeline.py` |
| 9 | API Layer (FastAPI) | `main.py`, `routes.py` |
| 10 | Tests & Demo | `tests/`, `demo.py` |

---

## 9. API Interface (for Backend Integration)

**Endpoint:** `POST /api/v1/evaluate`

```python
# Request
class EvaluateRequest(BaseModel):
    file: bytes                          # multipart/form-data
    source_type: Literal["pdf", "image"]
    student_id: str
    exam_id: str
    subject: str
    question_paper: QuestionPaper        # JSON
    rubrics: dict[int, Rubric]           # keyed by question_number

# Response
class EvaluateResponse(BaseModel):
    report: FinalReport
    trace_id: str
    processing_time_ms: int
```

---

## 10. Testing Strategy

- **Unit:** Each agent tested in isolation with fixtures (mock LLM responses)
- **Integration:** Full pipeline with sample PDFs
- **Golden Set:** 20+ answer sheets with expert-graded references
- **Metrics:** Mark accuracy (MAE), confidence calibration, latency, cost

---

## 11. Dependencies

| Package | Purpose |
|---------|---------|
| `google-genai` | Gemini API (OCR + LLM) |
| `pypdf` | PDF parsing fallback |
| `pillow` | Image preprocessing |
| `pydantic` | Schema validation |
| `pyyaml` | Config loading |
| `fastapi` + `uvicorn` | API server |
| `pytest` + `pytest-asyncio` | Testing |

---

## 12. Directory Structure

```
ai/
├── SPEC.md                 # This file
├── config.yaml             # Pipeline configuration
├── pyproject.toml          # Package metadata
├── main.py                 # FastAPI entry point
├── pipeline.py             # Orchestrator
├── schemas.py              # All Pydantic models
├── agents/
│   ├── __init__.py
│   ├── base.py             # BaseAgent class
│   ├── ocr_agent.py
│   ├── cleaner_agent.py
│   ├── splitter_agent.py
│   ├── evaluation_agent.py
│   ├── feedback_agent.py
│   └── aggregator_agent.py
├── prompts/
│   ├── evaluation.md
│   └── feedback.md
��── tests/
    ├── __init__.py
    ├── test_schemas.py
    ├── test_agents.py
    └── test_pipeline.py
```

---

## 13. Ponytail Notes

- **No abstraction layers** until needed — agents are simple classes, not interfaces
- **Stdlib first** — `asyncio`, `json`, `dataclasses` before external deps
- **One prompt file per agent** — no prompt registry, no templating engine
- **Config as YAML** — not env vars, not database
- **Sync-by-default** — async only where I/O waits (LLM calls, file reads)
- **Error as data** — `PipelineEnvelope` carries errors, no exceptions across boundaries