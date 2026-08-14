"""Backend entrypoint.

Run from the repo root:
    python -m backend.app
"""

import os

from flask import Flask, send_from_directory
from flask_cors import CORS

from backend.database.connection import load_db, seed_logs_if_empty
from backend.routes import register_routes

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.normpath(os.path.join(BACKEND_DIR, '..', 'Frontend'))
STATIC_DIR = FRONTEND_DIR if os.path.isdir(FRONTEND_DIR) else BACKEND_DIR

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path='')
CORS(app)

register_routes(app)


@app.route('/')
def index_route():
    return send_from_directory(STATIC_DIR, 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(STATIC_DIR, path)


if __name__ == '__main__':
    seed_logs_if_empty(load_db())
    app.run(host='0.0.0.0', port=8000, debug=True)