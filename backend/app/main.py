from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv

from app.core.config import settings
from app.routes import podcasts
from app.routers import subscription, crawler

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Hakka AI Podcast Generator",
    description="AI-powered personalized Hakka podcast generator with 3-step pipeline: Chinese generation → Hakka translation → TTS",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for audio
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(podcasts.router, prefix="/api/podcasts", tags=["podcasts"])
app.include_router(subscription.router, prefix="/api", tags=["subscription"])
app.include_router(crawler.router, prefix="/api", tags=["crawler"])

@app.get("/")
async def root():
    return {
        "message": "Hakka AI Podcast Generator API",
        "pipeline": [
            "1. Generate Traditional Chinese script using Gemini AI",
            "2. Translate Chinese to Hakka using translation service",
            "3. Generate Hakka audio using TTS service"
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)