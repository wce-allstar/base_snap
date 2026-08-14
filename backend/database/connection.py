"""JSON file persistence. Stand-in for PostgreSQL for the project demo."""

import json
import os

from .seed import DEFAULT_AGENT_PROMPTS, DEFAULT_RUBRICS, DEFAULT_SETTINGS, INITIAL_STUDENTS, SEED_LOGS

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BACKEND_DIR, '..', 'db.json')
UPLOAD_FOLDER = os.path.join(BACKEND_DIR, '..', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def default_db():
    return {
        "students": INITIAL_STUDENTS,
        "rubrics": DEFAULT_RUBRICS,
        "settings": DEFAULT_SETTINGS,
        "agent_prompts": dict(DEFAULT_AGENT_PROMPTS),
        "questionPapers": [],
        "logs": {name: [] for name in DEFAULT_AGENT_PROMPTS},
    }


def load_db():
    if not os.path.exists(DB_PATH):
        db = default_db()
        save_db(db)
        return db
    try:
        with open(DB_PATH, 'r') as f:
            db = json.load(f)
        if "logs" not in db:
            db["logs"] = {name: [] for name in DEFAULT_AGENT_PROMPTS}
        return db
    except Exception:
        return default_db()


def save_db(db):
    with open(DB_PATH, 'w') as f:
        json.dump(db, f, indent=2)


def seed_logs_if_empty(db):
    if any(db.get("logs", {}).get(agent) for agent in DEFAULT_AGENT_PROMPTS):
        return db
    db["logs"] = {name: list(template) for name, template in SEED_LOGS.items()}
    save_db(db)
    return db