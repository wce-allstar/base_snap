"""Upload endpoints: answer sheet scripts and question papers."""

import os
import time

from flask import jsonify, request

from ..database.connection import load_db, save_db
from ..services.file_service import extract_text, now_str, save_upload
from ..utils.logging import append_log


def register_routes(app):
    @app.route('/api/question-papers', methods=['GET'])
    def api_list_question_papers():
        db = load_db()
        return jsonify({"status": "success", "questionPapers": db.get('questionPapers', [])})

    @app.route('/api/question-papers/upload', methods=['POST'])
    def api_upload_question_paper():
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "No file uploaded"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"status": "error", "message": "No empty filename"}), 400

        file_path = save_upload(file, file.filename)
        extracted_text = extract_text(file_path)

        db = load_db()
        papers = db.get('questionPapers', [])
        paper = {
            "id": f"qp-{len(papers) + 1}-{int(time.time())}",
            "name": os.path.splitext(file.filename)[0].replace('_', ' ').replace('-', ' ').title(),
            "fileName": file.filename,
            "filePath": file_path,
            "text": extracted_text,
            "uploadedAt": now_str()
        }
        papers.append(paper)
        db['questionPapers'] = papers
        save_db(db)

        append_log('mapper', f"Question paper '{paper['name']}' stored for evaluation mapping.", 'info')
        return jsonify({"status": "success", "questionPaper": paper})

    @app.route('/api/upload', methods=['POST'])
    def api_upload_script():
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "No file uploaded"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"status": "error", "message": "No empty filename"}), 400

        question_paper_id = request.form.get('questionPaperId', '') or ''
        db = load_db()
        papers = db.get('questionPapers', [])
        linked_paper = next((p for p in papers if p['id'] == question_paper_id), None)

        file_path = save_upload(file, file.filename)
        extracted_text = extract_text(file_path)

        temp_id = f"CS2026-00{len(db['students']) + 10}"
        new_student = {
            "id": temp_id,
            "name": file.filename.split('_')[0] if '_' in file.filename else "Uploaded Script",
            "format": "Scanned PDF" if file.filename.lower().endswith('.pdf') else "Scanned Image",
            "filePath": file_path,
            "aiScore": 0.0,
            "maxScore": 50,
            "confidence": 80,
            "status": "Awaiting Pipeline",
            "selfCheck": "Awaiting Ingest",
            "handwritingQuality": "Analyzing...",
            "questionPaperId": linked_paper['id'] if linked_paper else "",
            "questionPaper": linked_paper['name'] if linked_paper else "",
            "questions": {
                "q1": {
                    "score": 0.0,
                    "maxScore": 10,
                    "ocrText": extracted_text or "Scanning in progress...",
                    "handwritingMock": "",
                    "strengths": [],
                    "weaknesses": [],
                    "justification": "Evaluation pending."
                },
                "q2": {
                    "score": 0.0,
                    "maxScore": 10,
                    "ocrText": "Analysis pending...",
                    "handwritingMock": "",
                    "strengths": [],
                    "weaknesses": [],
                    "justification": "Evaluation pending."
                }
            }
        }
        db['students'].append(new_student)
        save_db(db)

        append_log('extractor', f"Uploaded script '{file.filename}' saved and segmented.", 'info')
        return jsonify({"status": "success", "studentId": temp_id})