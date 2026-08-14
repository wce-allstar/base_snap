"""
OCR Agent — Extract text from PDF/image using Gemini Vision.
"""

from __future__ import annotations

import io
import time
from google import genai
from google.genai.errors import APIError
from pypdf import PdfReader
from PIL import Image

from schemas import OCRResult, SourceType, ErrorCode
from agents.base import BaseAgent, AgentError, PipelineStage


class OCRAgent(BaseAgent[OCRResult]):
    """Extract text from documents using Gemini or fallback to pypdf/tesseract."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-2.0-flash",
        max_retries: int = 3,
    ):
        super().__init__(PipelineStage.OCR, max_retries=max_retries)
        self.client = genai.Client(api_key=api_key) if api_key else genai.Client()
        self.model = model

    async def _execute(self, input_data: tuple[bytes, SourceType]) -> OCRResult:
        file_bytes, source_type = input_data

        if source_type == SourceType.PDF:
            return await self._process_pdf(file_bytes)
        else:
            return await self._process_image(file_bytes)

    async def _process_pdf(self, pdf_bytes: bytes) -> OCRResult:
        # Try pypdf first for text-based PDFs (fast, no API cost)
        text = self._extract_with_pypdf(pdf_bytes)
        if text.strip():
            return OCRResult(
                raw_text=text,
                page_count=self._count_pages(pdf_bytes),
                confidence=0.95,
                metadata={"engine": "pypdf", "method": "text_extraction"},
            )

        # Fallback to Gemini Vision for scanned/image PDFs
        return await self._process_with_gemini(pdf_bytes, "pdf")

    async def _process_image(self, image_bytes: bytes) -> OCRResult:
        return await self._process_with_gemini(image_bytes, "image")

    def _extract_with_pypdf(self, pdf_bytes: bytes) -> str:
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            texts = []
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    texts.append(extracted)
            return "\n\n".join(texts)
        except Exception:
            return ""

    def _count_pages(self, pdf_bytes: bytes) -> int:
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            return len(reader.pages)
        except Exception:
            return 1

    async def _process_with_gemini(self, file_bytes: bytes, mime_hint: str) -> OCRResult:
        prompt = (
            "Extract ALL text from this document. Preserve line breaks and structure. "
            "Return ONLY the extracted text, no commentary."
        )

        if mime_hint == "pdf":
            # For PDF, send as file data
            file_data = {"mime_type": "application/pdf", "data": file_bytes}
        else:
            # For images, detect format
            img = Image.open(io.BytesIO(file_bytes))
            fmt = img.format or "PNG"
            file_data = {"mime_type": f"image/{fmt.lower()}", "data": file_bytes}

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=[prompt, file_data],
                config={"temperature": 0.0},
            )
        except APIError as e:
            raise AgentError(
                code=ErrorCode.OCR_FAILED.value,
                message=f"Gemini API error: {e}",
                details={"status_code": getattr(e, "status_code", None)},
            )

        text = response.text or ""
        if not text.strip():
            raise AgentError(
                code=ErrorCode.EMPTY_DOCUMENT.value,
                message="No text extracted from document",
                recoverable=False,
            )

        return OCRResult(
            raw_text=text.strip(),
            page_count=1,  # Gemini doesn't return page count easily
            confidence=0.9,
            metadata={"engine": "gemini", "model": self.model, "mime_hint": mime_hint},
        )