"""Feedback Agent.

Input : { "student_id", "question_number", "marks", "max_marks",
          "coverage": [...], "reasoning": [...] }  (+ prompt, client)
Output: { "strengths": [...], "missing": [...], "feedback_text": "..." }

Generates explainable, examiner-style feedback per question.
"""


def feedback_agent(payload, prompt, client):
    """Write examiner-style strengths / missing items / feedback text."""
    schema_hint = (
        'Return ONLY a single JSON object of the form:\n'
        '{"strengths": [string], "missing": [string], "feedback_text": string}\nNo extra fields.'
    )
    prompt_with_data = (
        f"{prompt}\n\nStudent: {payload.get('student_id')} - Question {payload.get('question_number')}\n"
        f"Marks: {payload.get('marks')}/{payload.get('max_marks')}\n"
        f"Rubric coverage:\n{format_coverage(payload.get('coverage', []))}\n"
        f"Reasoning notes:\n{chr(10).join(payload.get('reasoning', []))}"
    )
    data = client.generate_json(prompt_with_data, schema_hint)

    return {
        "strengths": data.get("strengths", []),
        "missing": data.get("missing", []),
        "feedback_text": data.get("feedback_text", ""),
    }


def format_coverage(coverage):
    entries = []
    for c in coverage:
        entries.append(f"{c['status']}: {c['criterion']}")
    return "\n".join(entries) if entries else "(no coverage data)"