# backend/AGENTS.md — Backend Work Instructions

Read by opencode whenever working inside `backend/`. For project-wide rules read
the root `AGENTS.md` first, then this file for backend specifics.

## Scope (git-conflict safety)

You may read anything, but **only write files under `backend/`**:

- ✅ Allowed: everything in `backend/` (code, tests, fixtures).
- ❌ Never write: `Frontend/`, `ai/`, `docs/`, root `requirements.txt`, `.gitignore`, `sample_student_paper.pdf`.
- The backend *serves* the frontend (`../Frontend`) and *reads* the sample PDF at runtime — reading is fine, writing is not.
- `backend/db.json`, `backend/uploads/`, `backend/.venv/` are runtime artifacts (gitignored) — never commit them.

## Quick Start

```bash
# from repo root (venv already created, deps installed)
backend/.venv/bin/python -m backend.app                 # server on :8000, serves Frontend/
backend/.venv/bin/python -m backend.tests.test_pipeline # unit tests (stub LLM — offline)
```

Gemini key: required (no mock fallback). Set in Settings → Gemini API Key (stored
in gitignored `db.json`) or export `GEMINI_API_KEY`. Missing key → 503.

## Architecture (layer rules — never reverse)

```text
routes/  ->  services/  ->  agents/  ->  Gemini API
             database/, utils/         (leaf)
```

- `routes/` — URL layer. Read request → call service → return JSON.
- `services/` — business logic (orchestration, files, review). May import agents + database.
- `agents/` — pure JSON-in/out AI modules. NO Flask, NO routes, NO database imports.
- `database/` — `db.json` load/save + seed data.
- `utils/` — shared helpers (`logging.append_log`).

## File Map (backend)

| Path | Purpose |
|---|---|
| `app.py` | Entrypoint: Flask app, CORS, registers routes, serves Frontend statics. |
| `routes/upload.py` | `POST /api/upload`, `GET/POST /api/question-papers(/upload)` |
| `routes/evaluation.py` | `GET /api/queue`, `GET/POST /api/rubrics(/save)`, `POST /api/evaluate` |
| `routes/review.py` | `POST /api/approve` |
| `routes/settings.py` | `POST /api/login`, `GET/POST /api/settings(/save)`, `GET /api/agents`, `POST /api/agents/update`, `GET /api/agents/logs` |
| `services/pipeline_service.py` | **Orchestrator**: chains all 6 agents; raises `PipelineError(status, msg)`. |
| `services/file_service.py` | Upload saving + pypdf text extraction. |
| `services/review_service.py` | Examiner approval. |
| `agents/base.py` | `LLMClient` (Gemini wrapper, **429 retry/backoff — do not remove**), `parse_json_response`. |
| `agents/ocr_agent.py` | Gemini vision OCR (PDF/image bytes). CLI: `python -m backend.agents.ocr_agent <file>` |
| `agents/structuring_agent.py` | Clean + split raw text into question packets. |
| `agents/rubric_agent.py` | Semantic criterion coverage (Fully/Partially/Not Covered) + similarity. |
| `agents/reasoning_agent.py` | Logic/completeness audit → reasoning_score, logic_issues, confidence. |
| `agents/consistency_agent.py` | Final marks from coverage+reasoning, cohort check. |
| `agents/feedback_agent.py` | Examiner-style strengths/missing/feedback_text. |
| `database/connection.py` | `load_db()`/`save_db()` on `db.json`; `seed_logs_if_empty`. |
| `database/seed.py` | Seed students, rubrics, settings, 7 agent prompts, log templates. |
| `utils/logging.py` | `append_log(agent, text, type)` per-agent log trails. |
| `tests/test_pipeline.py` | Pipeline unit tests with stubbed LLM (no network). |
| `README.md` | Full file-by-file reference + scope rules. |

## Agent Contracts (frozen — see docs/JSON_SCHEMA.md)

- OCR: `{file_path}` → `{raw_text}`
- Structuring: `{raw_text, student_id}` → `{student_id, questions:[{question_number, answer}]}`
- Rubric: `{question, rubric}` → `{question_number, coverage:[{criterion, status}], similarity}`
- Reasoning: `{question, rubric}` → `{question_number, reasoning_score, logic_issues, confidence}`
- Consistency: `{question_number, coverage, reasoning_score, max_marks, cohort}` → `{adjusted_marks, consistency_passed, notes}`
- Feedback: `{student_id, question_number, marks, max_marks, coverage, reasoning}` → `{strengths, missing, feedback_text}`

Never change a contract without updating `docs/JSON_SCHEMA.md` (Member 6 owns docs — coordinate).

## Verification Workflow (before considering a task done)

1. `backend/.venv/bin/python -m backend.tests.test_pipeline` — all green.
2. Start server, then curl checks:
   - `GET /api/queue` → 200 + student list
   - `POST /api/evaluate` without key → 503 message
   - With key: upload `sample_student_paper.pdf` via `POST /api/upload`, then evaluate → student gets
     `status=Pending Review`, per-question `score`/`maxScore`, `ocrText`, `strengths`, `weaknesses`, `justification`, `report`.
3. `git status` — only intended `backend/` files staged.

## Status

- ✅ M1–M4 live-verified with real Gemini (OCR → structure → rubric → reasoning → consistency → feedback; review/approve flow works).
- 🔲 Backlog: `GET /api/report` export endpoint (`routes/report.py`), >2-question sheets, edge cases (empty OCR, very long sheets).
