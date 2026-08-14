"""Review workflow: examiner approval of AI-generated grades."""

from ..database.connection import load_db, save_db
from ..utils.logging import append_log


def approve_grades(student_id, question_scores, comments=""):
    """Approve an evaluation; apply human-edited per-question scores."""
    db = load_db()
    students = db.get("students", [])
    idx = next((i for i, s in enumerate(students) if s["id"] == student_id), -1)
    if idx == -1:
        return None, "Student not found"

    student = students[idx]
    student["status"] = "Approved"

    total = 0.0
    for qid, qscore in question_scores.items():
        if qid in student.get("questions", {}):
            student["questions"][qid]["score"] = float(qscore)
            total += float(qscore)

    q1 = student["questions"].get("q1", {}).get("score", 0.0)
    q2 = student["questions"].get("q2", {}).get("score", 0.0)
    original_offset = student["aiScore"] - (q1 + q2)
    student["aiScore"] = float(round(total + original_offset, 1))

    if comments.strip():
        student["selfCheck"] = "Manually Overridden"

    db["students"] = students
    save_db(db)
    append_log("checker", f"Moderator approved and locked grades for Roll: {student_id}.", "success")
    return student, None