"""Review endpoints: examiner approval of grades."""

from flask import jsonify, request

from ..services.review_service import approve_grades


def register_routes(app):
    @app.route('/api/approve', methods=['POST'])
    def api_approve_grade():
        data = request.json or {}
        student_id = data.get('studentId')
        q_scores = data.get('questions', {})
        comments = data.get('comments', '')

        student, error = approve_grades(student_id, q_scores, comments)
        if error:
            return jsonify({"status": "error", "message": error}), 404
        return jsonify({"status": "success", "student": student})