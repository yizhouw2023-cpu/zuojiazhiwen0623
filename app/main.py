"""FastAPI application entry point."""
from __future__ import annotations
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.database import init_db
from app.routers import upload, analyze, appreciation, wordcloud, export, history

# Resolve absolute paths from this file's location
APP_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(APP_DIR, "static")
TEMPLATES_DIR = os.path.join(APP_DIR, "templates")
UPLOADS_DIR = os.path.join(APP_DIR, "uploads")
WORDCLOUDS_DIR = os.path.join(APP_DIR, "wordclouds")
DATA_DIR = os.path.join(APP_DIR, "data")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown events."""
    for d in [UPLOADS_DIR, WORDCLOUDS_DIR, DATA_DIR]:
        os.makedirs(d, exist_ok=True)
    init_db()
    yield


app = FastAPI(
    title="作家语言指纹对比分析系统",
    description="Writer Language Fingerprint Comparison Analysis System",
    version="1.0.0",
    lifespan=lifespan,
)

# Routers — register BEFORE static mount
app.include_router(upload.router)
app.include_router(analyze.router)
app.include_router(appreciation.router)
app.include_router(wordcloud.router)
app.include_router(export.router)
app.include_router(history.router)

# Static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def index():
    """Serve the main page as static HTML (avoids Jinja2 caching bug on Python 3.14)."""
    return FileResponse(os.path.join(TEMPLATES_DIR, "index.html"))
