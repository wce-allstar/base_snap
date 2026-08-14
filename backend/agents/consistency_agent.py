"""Consistency Agent.

Input : { "question_number", "candidate_marks", "coverage": [...], "reasoning_score",
          "max_marks", "cohort": [ {"student_id", "marks"} ] }  (+ prompt, client)
Output: { "question_number", "adjusted_marks", "consistency_passed", "notes" }

Computes final marks from rubric coverage + reasoning and checks them
against the cohort for fairness (no drift, no anomalies).
"""


def consistency_agent(payload, prompt, client):
    """Derive marks per question and validate against the cohort."""
    schema_hint = (
        'Return ONLY a single JSON object of the form:\n'
        '{"question_number": integer, "adjusted_marks": float, '
        '"consistency_passed": boolean, "notes": string}\nNo extra fields.'
    )
    prompt_with_data = (
        f"{prompt}\n\nQuestion number: {payload.get('question_number')}\n"
        f"Coverage: {format_coverage(payload.get('coverage', []))}\n"
        f"Reasoning score: {payload.get('reasoning_score')}\n"
        f"Max marks: {payload.get('max_marks')}\n"
        f"Cohort scores for this question: {payload.get('cohort', [])}\n"
        "Assign adjusted_marks within 0 and max marks. Flag consistency_passed=false "
        "if the score deviates anomalously from the cohort."
    )
    data = client.generate_json(prompt_with_data, schema_hint)

    try:
        adjusted = float(data.get("adjusted_marks", 0.0))
        max_marks = float(payload.get("max_marks", 0.0)) or 10.0
    except (TypeError, ValueError):
        adjusted = 0.0
        max_marks = 10.0

    return {
        "question_number": payload.get("question_number"),
        "adjusted_marks": round(min(max(adjusted, 0.0), max_marks), 1),
        "consistency_passed": bool(data.get("consistency_passed", True)),
        "notes": data.get("notes", ""),
    }


def format_coverage(coverage):
    entries = []
    for c in coverage:
        entries.append(f"{c['status']}: {c['criterion']}")
    return "\n".join(entries) if entries else "(no coverage data)"