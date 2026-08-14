# ARCHITECTURE.md — System Design

## High-Level Flow

```text
Frontend (HTML/JS)
       |
       v
Flask API (backend/app.py)
       |
       +------------------+
       |                  |
       v                  v
  db.json            Pipeline Orchestrator
 (JSON DB)           (services/pipeline_service.py)
                          |
                          v
              +-----------+-----------+
              |           |           |
              v           v           v
        OCR Agent   Structuring   Evaluation Agents
       (Gemini)     Agent         (rubric / reasoning /
                                  consistency / feedback)
```

## Backend Role

The backend is an **orchestrator, not an evaluator**:

1. Receive answer sheets.
2. Store and manage data (JSON file DB).
3. Coordinate AI agents through the pipeline service.
4. Track evaluation progress via status + agent logs.
5. Serve results to the frontend.
6. Support human review and approval.

## Layer Rules (dependency direction)

```text
routes/  ->  services/  ->  agents/  ->  Gemini API
database/ , utils/        (leaf: no imports of other layers)
```

- `routes/` : URL handling only. Reads request, calls one service, returns JSON.
- `services/` : Business logic. May call agents and the database helpers.
- `agents/` : Pure AI modules. Input/output JSON only. No Flask, no DB, no routes.
- `database/` : Load/save `db.json`, seed data.
- `utils/` : Shared helpers (logging).

## Data Flow per Request

| Request                  | Route module      | Service called            | Agents used                  |
| ------------------------ | ----------------- | ------------------------- | ---------------------------- |
| `POST /api/upload`       | `upload.py`       | `file_service`            | —                            |
| `POST /api/evaluate`     | `evaluation.py`   | `pipeline_service`        | all six                     |
| `POST /api/approve`      | `review.py`       | `review_service`          | —                            |
| `GET/POST /api/rubrics`  | `evaluation.py`   | (direct db)               | —                            |
| `GET/POST /api/settings` | `settings.py`     | (direct db)               | —                            |
| `GET /api/agents/logs`   | `settings.py`     | `utils.logging`           | —                            |

## Database

JSON file (`backend/db.json`) for the project demo. Collections:

- `students` — uploaded answer sheets + evaluation results
- `rubrics` — question papers with criteria
- `questionPapers` — uploaded question paper files
- `settings` — institution + Gemini API key
- `agent_prompts` — system prompts per agent
- `logs` — agent log trails

Status lifecycle: `Awaiting Pipeline -> Processing -> Pending Review -> Approved`

## Config

- `requirements.txt` — Flask, Flask-Cors, pypdf, google-genai
- Run: `python -m backend.app` from the repo root (port 8000)
- `backend/db.json` — created on first run
- `backend/uploads/` — uploaded files
- Gemini API key stored in settings (`geminiApiKey`); the pipeline **requires** it.
