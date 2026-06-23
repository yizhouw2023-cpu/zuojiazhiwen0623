"""FastAPI application entry point."""
from __future__ import annotations
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

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

# Templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Routers
app.include_router(upload.router)
app.include_router(analyze.router)
app.include_router(appreciation.router)
app.include_router(wordcloud.router)
app.include_router(export.router)
app.include_router(history.router)

# Static files — mount AFTER routers to avoid intercepting API routes
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def index(request: Request):
    """Serve the main page."""
    return templates.TemplateResponse("index.html", {"request": request})
