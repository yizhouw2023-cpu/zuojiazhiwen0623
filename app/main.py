"""FastAPI application entry point."""
from __future__ import annotations
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import init_db
from app.routers import upload, analyze, appreciation, wordcloud, export, history


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown events."""
    # Ensure data directories exist
    base = os.path.dirname(__file__)
    for subdir in ["uploads", "wordclouds"]:
        path = os.path.join(base, subdir)
        os.makedirs(path, exist_ok=True)

    # Create data dir for SQLite
    data_dir = os.path.join(os.path.dirname(base), "app", "data")
    os.makedirs(data_dir, exist_ok=True)

    # Init database tables
    init_db()
    yield


app = FastAPI(
    title="作家语言指纹对比分析系统",
    description="Writer Language Fingerprint Comparison Analysis System",
    version="1.0.0",
    lifespan=lifespan,
)

# Static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Templates
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

# Routers
app.include_router(upload.router)
app.include_router(analyze.router)
app.include_router(appreciation.router)
app.include_router(wordcloud.router)
app.include_router(export.router)
app.include_router(history.router)


@app.get("/")
async def index(request: Request):
    """Serve the main page."""
    return templates.TemplateResponse("index.html", {"request": request})
