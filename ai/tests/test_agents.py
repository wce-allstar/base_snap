"""
Agent unit tests with mocked LLM responses.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from schemas import (
    QuestionPacket, Rubric, KeyPoint, MarkingScheme,
    MarkingSchemeType, QuestionMeta, QuestionPaper,
    SourceType, OCRResult, CleanedText,
    StudentMeta, EvaluationResult, KeyPointScore,
    FeedbackResult, ConsistencyFlag, ConsistencyFlagType,
    ConsistencySeverity, PipelineStatus,
)
from agents.ocr_agent import OCRAgent
from agents.cleaner_agent import CleanerAgent
from agents.splitter_agent import SplitterAgent
from agents.evaluation_agent import EvaluationAgent
from agents.feedback_agent import FeedbackAgent
from agents.aggregator_agent import AggregatorAgent
from agents.base import PipelineEnvelope, PipelineStatus


class TestCleanerAgent:
    """Cleaner agent is deterministic - no mocking needed."""

    @pytest.fixture
    def agent(self):
        return CleanerAgent()

    @pytest.mark.asyncio
    async def test_fix_hyphenation(self, agent):
        text = "opera-\nting system"
        env = await agent.process(text)
        assert env.status == PipelineStatus.SUCCESS
        assert "operating" in env.payload.text

    @pytest.mark.asyncio
    async def test_remove_page_numbers(self, agent):
        text = "Page 1\n\nContent here\n\n2"
        env = await agent.process(text)
        assert env.status == PipelineStatus.SUCCESS
        assert "Page 1" not in env.payload.text
        assert "\n\n2\n" not in env.payload.text

    @pytest.mark.asyncio
    async def test_normalize_whitespace(self, agent):
        text = "  too   many    spaces\n\n\n\nmany newlines  "
        env = await agent.process(text)
        assert env.status == PipelineStatus.SUCCESS
        assert "too many spaces" in env.payload.text
        assert "\n\n\n" not in env.payload.text

    @pytest.mark.asyncio
    async def test_fix_ocr_artifacts(self, agent):
        text = "a | b — c . d  ����"
        env = await agent.process(text)
        assert env.status == PipelineStatus.SUCCESS
        assert "ab" in env.payload.text or "a b" in env.payload.text


class TestSplitterAgent:
    """Splitter agent tests."""

    @pytest.fixture
    def agent(self):
        return SplitterAgent()

    @pytest.fixture
    def sample_paper(self):
        return QuestionPaper(questions=[
            QuestionMeta(number=1, text="What is an OS?", max_marks=10),
            QuestionMeta(number=2, text="Explain deadlock", max_marks=15),
        ])

    @pytest.mark.asyncio
    async def test_basic_split(self, agent, sample_paper):
        text = "1. What is an OS? Answer: An OS manages hardware.\n\n2. Explain deadlock Answer: Deadlock is..."
        env = await agent.process((text, sample_paper))
        assert env.status == PipelineStatus.SUCCESS
        packets = env.payload
        assert len(packets) == 2
        assert packets[0].question_number == 1
        assert "manages hardware" in packets[0].student_answer

    @pytest.mark.asyncio
    async def test_split_with_q_marker(self, agent, sample_paper):
        text = "Q1. What is an OS? Ans: An OS manages hardware.\n\nQ2. Explain deadlock Ans: Deadlock is..."
        env = await agent.process((text, sample_paper))
        assert env.status == PipelineStatus.SUCCESS
        assert len(env.payload) == 2

    @pytest.mark.asyncio
    async def test_empty_text_raises(self, agent):
        env = await agent.process(("", None))
        assert env.status == PipelineStatus.ERROR
        assert env.error.code == "SPLIT_FAILED"


class TestAggregatorAgent:
    """Aggregator agent tests - deterministic."""

    @pytest.fixture
    def agent(self):
        return AggregatorAgent()

    @pytest.fixture
    def sample_evals(self):
        from schemas import EvaluationResult, KeyPointScore
        return [
            EvaluationResult(
                question_number=1,
                marks_awarded=8.0,
                max_marks=10,
                confidence=0.9,
                reasoning=["Good"],
                key_point_scores=[KeyPointScore(concept="A", awarded_weight=0.8, reasoning="ok")],
            ),
            EvaluationResult(
                question_number=2,
                marks_awarded=12.0,
                max_marks=15,
                confidence=0.85,
                reasoning=["Okay"],
                key_point_scores=[KeyPointScore(concept="B", awarded_weight=0.8, reasoning="ok")],
            ),
        ]

    @pytest.fixture
    def sample_feedbacks(self):
        from schemas import FeedbackResult
        return [
            FeedbackResult(question_number=1, student_feedback="Good", examiner_notes="ok",
                          strengths=["clear"], improvements=["add example"]),
            FeedbackResult(question_number=2, student_feedback="Okay", examiner_notes="ok",
                          strengths=["correct"], improvements=["expand"]),
        ]

    @pytest.fixture
    def student_meta(self):
        return StudentMeta(student_id="S1", exam_id="E1", subject="OS", total_max_marks=25)

    @pytest.mark.asyncio
    async def test_aggregate_basic(self, agent, sample_evals, sample_feedbacks, student_meta):
        env = await agent.process((sample_evals, sample_feedbacks, student_meta))
        assert env.status == PipelineStatus.SUCCESS
        report = env.payload
        assert report.total_marks == 20.0
        assert report.total_max_marks == 25
        assert report.percentage == 80.0
        assert len(report.per_question) == 2

    @pytest.mark.asyncio
    async def test_confidence_weighted(self, agent, sample_evals, sample_feedbacks, student_meta):
        env = await agent.process((sample_evals, sample_feedbacks, student_meta))
        report = env.payload
        # Weighted: (0.9*10 + 0.85*15) / 25 = 0.87
        assert abs(report.confidence_score - 0.87) < 0.01


class TestEvaluationAgentMocked:
    """Evaluation agent with mocked LLM."""

    @pytest.fixture
    def agent(self):
        with patch("agents.evaluation_agent.genai.Client") as mock_client:
            yield EvaluationAgent(api_key="test-key")

    @pytest.fixture
    def packet(self):
        return QuestionPacket(
            question_number=1,
            question_text="What is an OS?",
            max_marks=10,
            student_answer="An OS manages hardware and software resources.",
        )

    @pytest.fixture
    def rubric(self):
        return Rubric(
            model_answer="An operating system manages hardware and software resources...",
            key_points=[
                KeyPoint(concept="manages hardware", weight=0.5),
                KeyPoint(concept="manages software", weight=0.5),
            ],
        )

    @pytest.mark.asyncio
    async def test_evaluate_success(self, agent, packet, rubric):
        # Mock the LLM response
        mock_response = MagicMock()
        mock_response.text = '''
        {
            "question_number": 1,
            "marks_awarded": 8.0,
            "max_marks": 10,
            "confidence": 0.9,
            "reasoning": ["Correctly identifies hardware management", "Mentions software resources"],
            "key_point_scores": [
                {"concept": "manages hardware", "awarded_weight": 0.5, "reasoning": "explicitly mentioned"},
                {"concept": "manages software", "awarded_weight": 0.3, "reasoning": "partially covered"}
            ]
        }
        '''
        agent.client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        env = await agent.process((packet, rubric))
        assert env.status == PipelineStatus.SUCCESS
        assert env.payload.marks_awarded == 8.0
        assert len(env.payload.key_point_scores) == 2


class TestFeedbackAgentMocked:
    """Feedback agent with mocked LLM."""

    @pytest.fixture
    def agent(self):
        with patch("agents.feedback_agent.genai.Client") as mock_client:
            yield FeedbackAgent(api_key="test-key")

    @pytest.fixture
    def packet(self):
        return QuestionPacket(
            question_number=1,
            question_text="What is an OS?",
            max_marks=10,
            student_answer="An OS manages hardware.",
        )

    @pytest.fixture
    def evaluation(self):
        from schemas import EvaluationResult, KeyPointScore
        return EvaluationResult(
            question_number=1,
            marks_awarded=7.0,
            max_marks=10,
            confidence=0.85,
            reasoning=["Good hardware mention", "Missing software"],
            key_point_scores=[
                KeyPointScore(concept="hardware", awarded_weight=0.5, reasoning="covered"),
                KeyPointScore(concept="software", awarded_weight=0.2, reasoning="missing"),
            ],
        )

    @pytest.mark.asyncio
    async def test_feedback_success(self, agent, packet, evaluation):
        mock_response = MagicMock()
        mock_response.text = '''
        {
            "question_number": 1,
            "student_feedback": "Good job identifying hardware management. To improve, discuss software resource management.",
            "examiner_notes": "Student covered hardware but missed software.",
            "strengths": ["Clear hardware explanation"],
            "improvements": ["Add software management", "Include examples"],
            "exemplar_snippet": "A complete answer would mention both hardware and software..."
        }
        '''
        agent.client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        env = await agent.process((packet, evaluation))
        assert env.status == PipelineStatus.SUCCESS
        assert "hardware" in env.payload.student_feedback.lower()
        assert len(env.payload.strengths) >= 1


class TestOCRAgentMocked:
    """OCR agent with mocked LLM."""

    @pytest.fixture
    def agent(self):
        with patch("agents.ocr_agent.genai.Client") as mock_client:
            yield OCRAgent(api_key="test-key")

    @pytest.mark.asyncio
    async def test_pdf_text_extraction(self, agent):
        # Test pypdf path (no LLM call)
        import io
        from pypdf import PdfWriter

        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        pdf_bytes = io.BytesIO()
        writer.write(pdf_bytes)

        # This blank PDF won't have extractable text, so it'll fall through to Gemini
        # For a real test, we'd need a PDF with text or mock pypdf
        pass  # Skipped - requires test PDF fixture


# Fixtures for pytest-asyncio
pytest_plugins = ["pytest_asyncio"]