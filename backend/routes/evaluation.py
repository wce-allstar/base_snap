"""Evaluation endpoints: queue, rubrics, and the pipeline trigger."""

from flask import jsonify, request

from ..database.connection import load_db, save_db
from ..services.pipeline_service import PipelineError, run_evaluation
from ..utils.logging import append_log


def register_routes(app):
    @app.route('/api/queue', methods=['GET'])
    def api_get_queue():
        db = load_db()
        return jsonify(db.get('students', []))

    @app.route('/api/rubrics', methods=['GET'])
    def api_get_rubrics():
        db = load_db()
        return jsonify(db.get('rubrics', []))

    @app.route('/api/rubrics/save', methods=['POST'])
    def api_save_rubrics():
        db = load_db()
        data = request.json or {}
        rubrics = db.get('rubrics', [])

        idx = next((i for i, r in enumerate(rubrics) if r['id'] == data.get('id')), -1)
        if idx != -1:
            rubrics[idx] = data
        else:
            rubrics.append(data)

        db['rubrics'] = rubrics
        save_db(db)
        append_log('mapper', f"Compiled rubric published: {data.get('subject')}", 'success')
        return jsonify({"status": "success"})

    @app.route('/api/evaluate', methods=['POST'])
    def api_evaluate_script():
        data = request.json or {}
        student_id = data.get('studentId')
        question_paper_id = data.get('questionPaperId') or ''

        try:
            student = run_evaluation(student_id, question_paper_id)
        except PipelineError as e:
            return jsonify({"status": "error", "message": e.message}), e.status_code
        except Exception as e:
            append_log('grader', f"Pipeline failed: {str(e)}", 'warn')
            return jsonify({"status": "error", "message": f"Evaluation failed: {str(e)}"}), 502

        return jsonify({"status": "success", "student": student})