"""Agent log trail helpers (preserved from the original server.py)."""

from datetime import datetime

from ..database.connection import load_db, save_db
from ..database.seed import DEFAULT_AGENT_PROMPTS


def append_log(agent, text, log_type='info'):
    db = load_db()
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = {
        "text": f"[{timestamp}] {log_type.upper()}: {text}" if log_type != 'agent-message' else text,
        "type": log_type
    }
    if "logs" not in db:
        db["logs"] = {name: [] for name in DEFAULT_AGENT_PROMPTS}
    db["logs"][agent].append(log_entry)

    if len(db["logs"][agent]) > 100:
        db["logs"][agent].pop(0)

    save_db(db)
    return log_entry