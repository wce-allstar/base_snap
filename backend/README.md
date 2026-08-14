# Backend — File Reference & Developer Guide

## ⚠️ CRITICAL: Backend-Only Work Rule

**Read, edit, create, and delete files ONLY inside the `backend/` folder — never outside it.**

Do **NOT** modify anything outside `backend/`, in particular:

| Path                | Why it will conflict                                |
| ------------------- | --------------------------------------------------- |
| `Frontend/`         | Belongs to Member 5. Changes collide on push.       |
| `ai/`               | Belongs to the AI team (Member 1–3 pipeline work).  |
| `docs/`             | Belongs to Member 6 (documentation & integration).  |
| `requirements.txt`  | Lives at repo root. If backend deps change, ask Member 6 to update it. |
| `sample_student_paper.pdf` | Shared test fixture owned by Member 1. You may copy it **into** `backend/tests/fixtures/`, never edit the original. |
| `.gitignore`        | Root-owned. New ignore rules go through Member 6.   |

The backend serves the Frontend folder at runtime (`backend/app.py` resolves `../Frontend`),
and reads the sample paper from the repo root only for manual testing — but you must never
**write** to those locations.

Rules that keep the git history clean for everyone:

1. All code changes happen under `backend/`.
2. Never commit `backend/db.json` or `backend/uploads/` (already in `.gitignore`).
3. Before pushing: `git status` — if anything outside `backend/` shows up in your changes, it was not you. Do not stage it.
4. Secret keys go into `backend/db.json` (gitignored) — never into code or commits.

---

## How to Run

```bash
# from the repo root
python -m backend.app            # server on http://localhost:8000
python -m backend.tests.test_pipeline          # run unit tests
GEMINI_API_KEY=... python -m backend.agents.ocr_agent sample_student_paper.pdf  # OCR milestone check
```

First run creates `backend/db.json` (seed data) and `backend/uploads/`.

The Gemini API key is **required** for evaluation (no offline mock): set it via
Settings → Gemini API Key in the UI, or set the `GEMINI_API_KEY` environment variable
(honored by `LLMClient` in `agents/base.py`). Missing key → `POST /api/evaluate` returns 503.

---

## File-by-File Reference

### Root of backend/

| File | Purpose |
| ---- | ------- |
| `__init__.py` | Marks `backend/` as a Python package so imports like `from backend.app import app` work. |
| `app.py` | **Entrypoint.** Creates the Flask app, enables CORS, registers all routes (`routes/`), serves the Frontend's static files (`index.html`, `app.js`, …) and starts the server on port 8000. Run with `python -m backend.app`. |
| `agent.md` | Architecture notes spec (team planning doc). Not code. |
| `generate_sample_pdf.py` | Generator for the sample answer sheet PDF. Run manually to regenerate test data. |
| `db.json` | **Runtime data (gitignored).** Generated on first run. Holds students, rubrics, settings, agent prompts, logs, question papers. |
| `requirements.txt` *(root-level)* | Python dependencies: Flask, Flask-Cors, pypdf, google-genai. Owned by Member 6 — do not edit directly. |
| `README.md` | This file. |

### `agents/` — the six AI modules (pure JSON in / JSON out)

These are the AI. They import **no Flask, no routes, no database** — only each
other's shared `base.py`. Contracts are fixed in `docs/JSON_SCHEMA.md`; never change
an agent's contract without updating that doc.

| File | Role | Input → Output |
| ---- | ---- | -------------- |
| `__init__.py` | Exports the six agents for `from backend.agents import ocr_agent`. |
| `base.py` | Shared LLM plumbing: `LLMClient` (thin google-genai wrapper; `generate`, `generate_with_file` for PDF/image bytes, `generate_json` with schema enforcement) and `parse_json_response` (strips markdown fences, extracts JSON). Model default `gemini-3.5-flash`. |
| `ocr_agent.py` | **Milestone 1.** Extracts text from PDF/PNG/JPG/WebP via Gemini vision. Also runnable as a CLI (`python -m backend.agents.ocr_agent <file>`). |
| `structuring_agent.py` | **Milestone 2.** Cleans noisy OCR text and splits it into numbered question packets. |
| `rubric_agent.py` | **Milestone 3.** Semantic mapping of an answer against rubric criteria (Fully / Partially / Not Covered) + similarity score. |
| `reasoning_agent.py` | **Milestone 3.** Audits logic flow, completeness, partial correctness; returns reasoning score, logic issues, confidence. |
| `consistency_agent.py` | **Milestone 3.** Computes final marks from coverage + reasoning and validates them against the cohort (drift/anomaly check). |
| `feedback_agent.py` | **Milestone 3.** Writes examiner-style strengths / missing items / feedback text per question. |

### `services/` — business logic (backend = orchestrator, not evaluator)

| File | Purpose |
| ---- | ------- |
| `__init__.py` | Package marker. |
| `file_service.py` | Upload persistence (`save_upload`, saves into `backend/uploads/`) and best-effort PDF text extraction via pypdf (`extract_text`). |
| `pipeline_service.py` | **The orchestrator.** `run_evaluation()` chains all six agents: OCR → structuring → (rubric + reasoning + consistency + feedback) per question → final report. Stores results into the student record in the legacy frontend shape. Raises `PipelineError` with HTTP status (404/400/503/502). |
| `review_service.py` | Examiner approval workflow: `approve_grades()` applies human-edited per-question scores and marks the sheet `Approved`. |

### `routes/` — the URL layer

Each module registers its endpoints onto the Flask app. Routes only read the
request, call a service, and return JSON.

| File | Endpoints |
| ---- | --------- |
| `__init__.py` | `register_routes(app)` — registers all four modules. |
| `upload.py` | `GET /api/question-papers` · `POST /api/question-papers/upload` · `POST /api/upload` |
| `evaluation.py` | `GET /api/queue` · `GET /api/rubrics` · `POST /api/rubrics/save` · `POST /api/evaluate` |
| `review.py` | `POST /api/approve` |
| `settings.py` | `POST /api/login` · `GET/POST /api/settings` · `GET /api/agents` · `POST /api/agents/update` · `GET /api/agents/logs` |

### `database/` — JSON storage for the demo

| File | Purpose |
| ---- | ------- |
| `__init__.py` | Package marker. |
| `connection.py` | `load_db()` / `save_db()` on `backend/db.json`, upload-folder creation, initial seed + seed-logs on first run. |
| `seed.py` | All seed data preserved from the original server: 3 demo students, 2 rubrics (CS101, ME202), default settings, **7 agent prompts** (extractor, structurer, mapper, reasoner, grader, checker, feedback) and initial log templates. |

### `utils/` — shared helpers

| File | Purpose |
| ---- | ------- |
| `__init__.py` | Package marker. |
| `logging.py` | `append_log(agent, text, type)` — writes timestamped entries to each agent's log trail in db.json (cap 100 entries). Used by routes/services. |

### `tests/` — verification

| File | Purpose |
| ---- | ------- |
| `test_pipeline.py` | Unit tests with a **stubbed** LLM (no network, no API key). Covers: full `run_evaluation` flow, missing-key → 503, unknown student → 404, cohort collection. |

### Runtime folders

| Path | Purpose |
| ---- | ------- |
| `uploads/` | Uploaded answer sheets and question papers (gitignored). |
| `db.json` | Live database (gitignored, auto-generated). |

---

## Status — What Is Complete & What Remains

### ✅ Complete (Milestones 1–4 backend-side, per `docs/WORKFLOW.md`)

| Milestone | Backend status |
| --------- | -------------- |
| **M1 OCR** | `agents/ocr_agent.py` is Gemini-vision based (PDF/image bytes). CLI available. |
| **M2 Structuring** | `agents/structuring_agent.py` validates question numbers, drops empty packets. |
| **M3 Evaluation** | `rubric_agent` + `reasoning_agent` + `consistency_agent` + `feedback_agent` produce marks, reasoning, confidence, feedback. |
| **M4 Full pipeline** | `services/pipeline_service.py` orchestrates end-to-end via `POST /api/evaluate`; final report stored on the student record. |
| Restructure | 782-line `server.py` removed → `app.py` + `routes/` + `services/` + `agents/` + `database/` + `utils/`. All endpoints regression-tested. |
| Behavior | Mock pipeline removed (Gemini-only per team decision); 4 unit tests pass with a stubbed LLM. |

### 🔲 Remaining / Next Steps (backend scope only)

1. **Real Gemini end-to-end run** — paste the API key into Settings, upload `sample_student_paper.pdf`,
   hit `POST /api/evaluate`, and confirm M1–M3 live output (covers the current open todo).
2. **More than 2 questions per sheet** — pipeline already writes `q3…qN` keys; verify the workspace UI shows
   them (UI is Member 5's scope — report findings via docs, don't edit `Frontend/`).
3. **Report export endpoint** — `GET /api/report/{sheet_id}` is specified in `backend/agent.md` but not built
   (Member 4 backlog; would be a new `routes/report.py` + service).
4. **Edge hardening** — very long OCR text (multi-page), blank/failed OCR (empty `raw_text`), and rubric
   papers with more questions than the sheet (currently falls back to the last rubric entry).
5. **Docs sync** — update `docs/PIPELINE.md` / `docs/AGENTS.md` only through Member 6's workflow
   (docs are outside backend; coordinate, don't edit directly).

### Suggested workflow for parallel team work

- Members 1–3 (AI): own `backend/agents/*` — but review `docs/JSON_SCHEMA.md` first; contracts are frozen.
- Member 4 (backend): owns `backend/routes/`, `backend/services/`, `backend/app.py`, `backend/database/`.
- Member 6 (testing): extends `backend/tests/`; may not touch agents' contracts without a doc change.
- Any new backend dependency: ask Member 6 to add it to the root `requirements.txt`.
- Anything outside `backend/`: **stop and coordinate** — direct edits will cause push conflicts.