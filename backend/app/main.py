"""
Ruo Stock Module - Main Application
A stock analysis platform with AI-powered features
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os

from app.routers import api, pages

app = FastAPI(
    title="Ruo Stock - 股票智能分析平台",
    description="连板天梯、AI智能分析、市场热点追踪",
    version="1.0.0"
)

# Include routers
app.include_router(api.router, prefix="/api", tags=["API"])
app.include_router(pages.router, tags=["Pages"])

# Get port from environment or default
PORT = int(os.getenv("PORT", "8000"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
