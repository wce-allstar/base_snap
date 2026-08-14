"""Settings, agent prompts, logs, and mock-login endpoints."""

from flask import jsonify, request

from ..database.connection import load_db, save_db
from ..utils.logging import append_log

try:
    from google import genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False


def register_routes(app):
    @app.route('/api/login', methods=['POST'])
    def api_login():
        data = request.json or {}
        email = data.get('email', '')
        password = data.get('password', '')

        if '@' in email and len(password) >= 6:
            append_log('checker', f"Examiner authenticated: {email}", 'success')
            return jsonify({"status": "success", "token": "mock-token-session-12345"})
        return jsonify({"status": "error", "message": "Verification failed"}), 400

    @app.route('/api/settings', methods=['GET'])
    def api_get_settings():
        db = load_db()
        return jsonify(db.get('settings', {}))

    @app.route('/api/settings/save', methods=['POST'])
    def api_save_settings():
        db = load_db()
        data = request.json or {}
        db['settings'] = data
        save_db(db)

        key = data.get('geminiApiKey', '')
        if key and HAS_GEMINI:
            try:
                genai.Client(api_key=key)
                append_log('grader', "Gemini API configurator connection initialized.", 'success')
            except Exception as e:
                append_log('grader', f"API key config fail: {str(e)}", 'warn')

        append_log('checker', "System configuration settings updated.", 'info')
        return jsonify({"status": "success"})

    @app.route('/api/agents', methods=['GET'])
    def api_get_agents():
        db = load_db()
        return jsonify(db.get('agent_prompts', {}))

    @app.route('/api/agents/update', methods=['POST'])
    def api_update_agent():
        db = load_db()
        data = request.json or {}
        agent_id = data.get('agentId')
        prompt = data.get('prompt')

        if agent_id in db['agent_prompts']:
            db['agent_prompts'][agent_id] = prompt
            save_db(db)
            append_log(agent_id, "System prompt updated. Restarting agent context...", 'warn')
            return jsonify({"status": "success"})
        return jsonify({"status": "error", "message": "Unknown agent"}), 400

    @app.route('/api/agents/logs', methods=['GET'])
    def api_get_logs():
        db = load_db()
        agent = request.args.get('agent', 'extractor')
        logs = db.get('logs', {}).get(agent, [])
        return jsonify(logs)