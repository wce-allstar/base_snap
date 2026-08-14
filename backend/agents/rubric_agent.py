"""Rubric Mapping Agent.

Input : { "question": { "question_number", "answer" },
          "rubric":  { "question_text", "max_marks", "criteria": [{text, marks}] } }
         (+ prompt, client)
Output: { "question_number", "coverage": [{criterion, status}], "similarity" }

Semantic (not keyword) matching of the answer against each criterion.
"""


def rubric_agent(question, rubric, prompt, client):
    """Map a student answer against rubric criteria."""
    schema_hint = (
        'Return ONLY a single JSON object of the form:\n'
        '{"question_number": integer, '
        '"coverage": [{"criterion": string, "status": "Fully Covered" | "Partially Covered" | "Not Covered"}], '
        '"similarity": float between 0 and 1}\n'
        'Use exactly the three status values listed. No extra fields.'
    )
    prompt_with_data = (
        f"{prompt}\n\nQuestion number: {question.get('question_number')}\n"
        f"Student answer:\n{question.get('answer', '')}\n\n"
        f"Rubric:\n{criteria_lines(rubric)}"
    )
    payload = client.generate_json(prompt_with_data, schema_hint)

    coverage = []
    for item in payload.get("coverage", []):
        status = item.get("status")
        if status not in ("Fully Covered", "Partially Covered", "Not Covered"):
            status = "Not Covered"
        coverage.append({"criterion": item.get("criterion", ""), "status": status})

    try:
        similarity = float(payload.get("similarity", 0.0))
    except (TypeError, ValueError):
        similarity = 0.0

    return {
        "question_number": question.get("question_number"),
        "coverage": coverage,
        "similarity": min(max(similarity, 0.0), 1.0),
    }


def criteria_lines(rubric):
    lines = [f"Q: {rubric.get('question_text', '')} (max {rubric.get('max_marks', 0)} marks)"]
    for c in rubric.get("criteria", []):
        lines.append(f"- ({c.get('marks', 0)} marks) {c.get('text', '')}")
    return "\n".join(lines)