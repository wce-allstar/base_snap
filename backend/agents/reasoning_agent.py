"""Reasoning Agent.

Input : { "question": { "question_number", "answer" }, "rubric": {...} } (+ prompt, client)
Output: { "question_number", "reasoning_score", "logic_issues": [...], "confidence" }

Audits concept understanding, logical flow, completeness, partial
correctness, and paraphrased answers.
"""


def reasoning_agent(question, rubric, prompt, client):
    """Audit the logic and completeness of a student answer."""
    schema_hint = (
        'Return ONLY a single JSON object of the form:\n'
        '{"question_number": integer, "reasoning_score": float 0-10, '
        '"logic_issues": [string], "confidence": float 0-1}\nNo extra fields.'
    )
    prompt_with_data = (
        f"{prompt}\n\nQuestion number: {question.get('question_number')}\n"
        f"Question text: {rubric.get('question_text', '')}\n\nStudent answer:\n{question.get('answer', '')}"
    )
    payload = client.generate_json(prompt_with_data, schema_hint)

    try:
        reasoning_score = float(payload.get("reasoning_score", 0.0))
    except (TypeError, ValueError):
        reasoning_score = 0.0
    try:
        confidence = float(payload.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0

    return {
        "question_number": question.get("question_number"),
        "reasoning_score": min(max(reasoning_score, 0.0), 10.0),
        "logic_issues": payload.get("logic_issues", []),
        "confidence": min(max(confidence, 0.0), 1.0),
    }