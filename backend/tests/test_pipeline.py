"""Pipeline tests with a stubbed LLM client (no network / no API key).

Run:  python -m backend.tests.test_pipeline   (from repo root)
"""

import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import connection  # noqa: E402
from backend.services import pipeline_service  # noqa: E402


class StubLLMClient:
    """Replies canned JSON in call order. Mirrors LLMClient's interface."""

    def __init__(self, api_key=None, model=None):
        assert api_key

    def generate_with_file(self, prompt, file_path, mime_type):
        return (
            'Question 1: Explain BST and its search complexity.\n'
            'A BST is a binary tree where left children are smaller and '
            'right children are larger than the root. Search is O(log N) '
            'average and O(N) worst case.\n\n'
            'Question 2: Write BST insertion pseudocode.\n'
            'if (root == null) return new Node(val); if (val < root.key) '
            'root.left = insert(root.left, val); else root.right = '
            'insert(root.right, val). Time O(h), space O(h).'
        )

    def generate(self, prompt):
        if "Raw OCR text" in prompt:
            return json.dumps({
                "student_id": "TEST-001",
                "questions": [
                    {"question_number": 1, "answer": "A BST is a binary tree where left children are smaller..."},
                    {"question_number": 2, "answer": "if (root == null) return new Node(val); ..."},
                ],
            })
        if "adjusted_marks" in prompt:
            return json.dumps({
                "question_number": 1,
                "adjusted_marks": 8,
                "consistency_passed": True,
                "notes": "Within cohort variance.",
            })
        if "reasoning_score" in prompt:
            return json.dumps({
                "question_number": 1,
                "reasoning_score": 8.0,
                "logic_issues": ["ACK sequence discussion missing."],
                "confidence": 0.91,
            })
        if "coverage" in prompt:
            return json.dumps({
                "question_number": 1,
                "coverage": [
                    {"criterion": "BST property", "status": "Fully Covered"},
                    {"criterion": "Complexities", "status": "Partially Covered"},
                ],
                "similarity": 0.87,
            })
        if "strengths" in prompt:
            return json.dumps({
                "strengths": ["Correct BST definition."],
                "missing": ["AVL balance factor."],
                "feedback_text": "Strengths: ... Missing: ... Marks: 8/10",
            })
        raise AssertionError(f"Unhandled prompt: {prompt[:80]}")

    def generate_json(self, prompt, schema_hint):
        return json.loads(self.generate(prompt + f"\n\n{schema_hint}"))


class PipelineTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        connection.DB_PATH = os.path.join(self.tmpdir, 'db.json')
        pipeline_service.load_db = connection.load_db
        pipeline_service.save_db = connection.save_db

        import shutil as _shutil
        sample = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'sample_student_paper.pdf')
        self.sheet_path = os.path.join(self.tmpdir, 'sheet.pdf')
        _shutil.copy(sample, self.sheet_path)

        db = connection.default_db()
        db["settings"]["geminiApiKey"] = "fake-key"
        db["students"] = [{
            "id": "TEST-001",
            "name": "Test Student",
            "format": "Scanned PDF",
            "filePath": self.sheet_path,
            "aiScore": 0.0,
            "maxScore": 50,
            "confidence": 80,
            "status": "Awaiting Pipeline",
            "selfCheck": "Awaiting Ingest",
            "handwritingQuality": "Analyzing...",
            "questionPaperId": "",
            "questions": {
                "q1": {"score": 0.0, "maxScore": 10, "ocrText": "", "strengths": [], "weaknesses": [], "justification": ""},
                "q2": {"score": 0.0, "maxScore": 10, "ocrText": "", "strengths": [], "weaknesses": [], "justification": ""},
            },
        }]
        connection.save_db(db)
        pipeline_service.LLMClient = StubLLMClient

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_run_evaluation(self):
        student = pipeline_service.run_evaluation("TEST-001")

        self.assertEqual(student["status"], "Pending Review")
        self.assertEqual(student["questions"]["q1"]["score"], 8.0)
        self.assertEqual(student["questions"]["q2"]["score"], 8.0)
        self.assertIn("BST", student["questions"]["q1"]["ocrText"])
        self.assertIn("strengths", student["questions"]["q1"])
        self.assertTrue(student["report"]["questions"][0]["consistency_passed"])

    def test_missing_key_raises_503(self):
        db = connection.load_db()
        db["settings"]["geminiApiKey"] = ""
        connection.save_db(db)
        with self.assertRaises(pipeline_service.PipelineError) as ctx:
            pipeline_service.run_evaluation("TEST-001")
        self.assertEqual(ctx.exception.status_code, 503)

    def test_missing_student_raises_404(self):
        with self.assertRaises(pipeline_service.PipelineError) as ctx:
            pipeline_service.run_evaluation("NOPE-999")
        self.assertEqual(ctx.exception.status_code, 404)

    def test_cohort_collection(self):
        db = connection.load_db()
        db["students"].append({
            "id": "OTHER-1", "aiScore": 20.0,
            "questions": {"q1": {"score": 7.0}},
        })
        connection.save_db(db)
        cohort = pipeline_service.cohort_for(db, "q1")
        self.assertEqual([c["student_id"] for c in cohort], ["OTHER-1"])


if __name__ == "__main__":
    unittest.main(verbosity=2)