"""AI agent modules. Pure JSON-in / JSON-out functions.

Agents never import Flask, routes, services, or the database.
They receive an LLM client and a prompt string; everything else is JSON.
"""

from .ocr_agent import ocr_agent
from .structuring_agent import structuring_agent
from .rubric_agent import rubric_agent
from .reasoning_agent import reasoning_agent
from .consistency_agent import consistency_agent
from .feedback_agent import feedback_agent

__all__ = [
    "ocr_agent",
    "structuring_agent",
    "rubric_agent",
    "reasoning_agent",
    "consistency_agent",
    "feedback_agent",
]