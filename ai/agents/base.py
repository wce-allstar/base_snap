"""
Base Agent Class

Simple abstraction for agent execution with retries, timing, and envelope wrapping.
"""

from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from schemas import ErrorInfo, PipelineEnvelope, PipelineStage, PipelineStatus

T = TypeVar("T")


class AgentError(Exception):
    """Agent-specific error with error code."""

    def __init__(self, code: str, message: str, details: dict | None = None, recoverable: bool = True):
        self.code = code
        self.message = message
        self.details = details or {}
        self.recoverable = recoverable
        super().__init__(message)


class BaseAgent(ABC, Generic[T]):
    """
    Base class for all pipeline agents.

    Subclasses implement `process()`; this class handles:
    - Retry logic (exponential backoff)
    - Timing metadata
    - Envelope wrapping
    - Error normalization
    """

    def __init__(
        self,
        stage: PipelineStage,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
    ):
        self.stage = stage
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

    @abstractmethod
    async def _execute(self, input_data: Any) -> T:
        """Actual agent logic. Must be implemented by subclass."""
        pass

    async def process(self, input_data: Any) -> PipelineEnvelope:
        """Execute with retries and return envelope."""
        last_error: AgentError | None = None

        for attempt in range(self.max_retries + 1):
            start = time.perf_counter()
            try:
                result = await self._execute(input_data)
                elapsed_ms = int((time.perf_counter() - start) * 1000)

                return PipelineEnvelope(
                    stage=self.stage,
                    status=PipelineStatus.SUCCESS,
                    payload=result,
                    metadata={"attempt": attempt + 1, "latency_ms": elapsed_ms},
                )

            except AgentError as e:
                last_error = e
                elapsed_ms = int((time.perf_counter() - start) * 1000)

                if not e.recoverable or attempt == self.max_retries:
                    break

                delay = min(self.base_delay * (2**attempt), self.max_delay)
                await asyncio.sleep(delay)

            except Exception as e:
                last_error = AgentError(
                    code="UNEXPECTED_ERROR",
                    message=str(e),
                    details={"type": type(e).__name__},
                    recoverable=True,
                )
                if attempt == self.max_retries:
                    break
                delay = min(self.base_delay * (2**attempt), self.max_delay)
                await asyncio.sleep(delay)

        # All retries exhausted
        return PipelineEnvelope(
            stage=self.stage,
            status=PipelineStatus.ERROR,
            payload=None,
            error=ErrorInfo(
                code=last_error.code if last_error else "UNKNOWN_ERROR",
                message=last_error.message if last_error else "Unknown error",
                details=last_error.details if last_error else {},
                recoverable=last_error.recoverable if last_error else False,
            ),
        )


def run_sync(agent: BaseAgent, input_data: Any) -> PipelineEnvelope:
    """Synchronous wrapper for testing."""
    return asyncio.run(agent.process(input_data))