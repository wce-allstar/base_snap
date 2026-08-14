# AI Service

This directory is dedicated to the AI part of the project. It will handle the agentic pipelines, prompts, OCR extraction, and evaluation logic.

## Recommended Tech Stack
- **Framework**: FastAPI (for lightweight, fast API endpoints) or Flask
- **Libraries**:
  - `google-genai` (for Gemini API calls)
  - `pypdf` (for processing PDFs)
  - `pillow` (for processing images)

## How to run locally (FastAPI example)
1. Navigate to this directory:
   ```bash
   cd ai
   ```
2. Set up a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r ../requirements.txt
   ```
3. Run the service:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
