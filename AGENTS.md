# AGENTS.md — Project Context for AI Assistants (opencode)

This file is read automatically by opencode when opened in this repo. Use it to
orient yourself before doing anything.

## Project

**AI-Assisted Agentic Evaluation System** — upload scanned answer sheets, OCR them,
structure into question packets, evaluate against rubrics with Gemini, and let
examiners review/approve grades.

- **Backend**: Flask (Python) — `backend/` — orchestrator, JSON file DB
- **Frontend**: plain HTML/JS/CSS — `Frontend/` (served by the backend)
- **AI agents**: Gemini-based modules in `backend/agents/`
- **AI folder**: `ai/` (starter docs only, not wired yet)

## Documentation Map (read the relevant one before editing)

| File | What it tells you |
|---|---|
| `docs/AGENTS.md` | Agent contracts (input/output JSON) + core dev rule |
| `docs/JSON_SCHEMA.md` | Exact JSON shapes exchanged between modules (frozen — do not break) |
| `docs/ARCHITECTURE.md` | Layer rules: routes → services → agents → Gemini; never reverse |
| `docs/PIPELINE.md` | End-to-end flow: OCR → structure → rubric → reasoning → consistency → feedback → report |
| `docs/PROMPTS.md` | Agent prompt templates (also editable at runtime via the UI) |
| `docs/WORKFLOW.md` | Milestones M1–M5 + team responsibilities |
| `backend/README.md` | **File-by-file backend reference + scope rules (read first for backend work)** |
| `backend/agent.md`, `agent.md` | Older planning notes (superseded by docs/) |

## Quick Start (how to connect everything)

```bash
# from repo root
backend/.venv/bin/python -m backend.app        # server on http://localhost:8000
backend/.venv/bin/python -m backend.tests.test_pipeline   # unit tests (stub LLM, offline)
GEMINI_API_KEY=... backend/.venv/bin/python -m backend.agents.ocr_agent sample_student_paper.pdf  # OCR milestone check
```

- venv: `backend/.venv` (already created, deps installed from root `requirements.txt`)
- Gemini API key: required for evaluation (no mock). Stored in `backend/db.json`
  settings (gitignored) or `GEMINI_API_KEY` env. Missing key → `POST /api/evaluate` → 503.
- Free tier rate limits (5 req/min) are handled by retry/backoff in
  `backend/agents/base.py` — do not remove.

## ⚠️ Repo-Wide Scope Rule (git-conflict prevention)

**Only edit files inside your team member's scope.** Changes outside cause push conflicts.

| Member | Scope |
|---|---|
| Member 1 (OCR) | `backend/agents/ocr_agent.py`, test fixtures inside `backend/` |
| Member 2 (Cleaner/Splitter) | `backend/agents/structuring_agent.py` |
| Member 3 (Evaluation) | `backend/agents/rubric_agent.py`, `reasoning_agent.py`, `consistency_agent.py`, `feedback_agent.py` + prompts in `backend/database/seed.py` |
| Member 4 (Backend/Orchestrator) | `backend/routes/`, `backend/services/`, `backend/app.py`, `backend/database/` |
| Member 5 (Frontend) | `Frontend/` only |
| Member 6 (Testing/Docs) | `backend/tests/`, `docs/`, root `requirements.txt` |

- Never commit `backend/db.json`, `backend/uploads/`, `.venv/` (all gitignored).
- Never edit: root `requirements.txt`, `.gitignore`, `sample_student_paper.pdf`, `docs/` (unless you are Member 6).
- Contract changes (JSON shapes) require updating `docs/JSON_SCHEMA.md` + coordination.
- `git status` before pushing — stage only files in your scope.

## Status

- ✅ M1–M4 done backend-side; live end-to-end verified with real Gemini on `sample_student_paper.pdf`.
- 🔲 Backlog: `GET /api/report` export endpoint, >2-question sheets, edge cases (empty OCR, long sheets).
