"""
FastAPI Application — AgenticEval AI Service.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    # Verify config loads
    from pipeline import PipelineConfig
    try:
        PipelineConfig.load("config.yaml")
    except Exception as e:
        print(f"WARNING: Failed to load config: {e}")
    yield
    # Shutdown (cleanup if needed)


app = FastAPI(
    title="AgenticEval AI Service",
    description="Multi-agent pipeline for subjective answer sheet evaluation",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
async def root():
    return {
        "service": "AgenticEval AI",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)