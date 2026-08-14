"""Structuring Agent (Cleaner + Question Splitter).

Input : { "raw_text": "...", "student_id": "CS2026-084" }  (+ prompt, client)
Output: { "student_id": "CS2026-084",
          "questions": [ { "question_number": 1, "answer": "..." } ] }

Milestone 2: raw OCR text -> structured question packets.
"""


def structuring_agent(raw_text, student_id, prompt, client):
    """Clean raw OCR text and split it into numbered question packets."""
    schema_hint = (
        'Return ONLY a single JSON object of the form:\n'
        '{"student_id": string, "questions": [{"question_number": integer, "answer": string}]}\n'
        'Each answer must keep the student\'s wording. No extra fields.'
    )
    prompt_with_text = f"{prompt}\n\nStudent ID: {student_id}\n\nRaw OCR text:\n{raw_text}"
    payload = client.generate_json(prompt_with_text, schema_hint)

    questions = []
    for item in payload.get("questions", []):
        try:
            num = int(item.get("question_number", 0))
        except (TypeError, ValueError):
            num = 0
        questions.append({
            "question_number": num,
            "answer": str(item.get("answer", ""))
        })
    questions = [q for q in questions if q["question_number"] > 0]

    if not questions:
        raise ValueError("Structuring agent could not identify any questions.")

    return {"student_id": student_id, "questions": questions}