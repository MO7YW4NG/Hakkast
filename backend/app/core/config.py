import os
from typing import List
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

# 載入 .env 文件
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

class Settings(BaseModel):
    # Gemini AI Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # TWCC AFS Configuration
    TWCC_API_KEY: str = os.getenv("TWCC_API_KEY", "")
    TWCC_BASE_URL: str = os.getenv("TWCC_BASE_URL", "https://api-ams.twcc.ai/api/models")
    TWCC_MODEL_NAME: str = os.getenv("TWCC_MODEL_NAME", "llama3.3-ffm-70b-32k-chat")
    
    # Hakka AI Hackathon API Configuration (shared credentials)
    HAKKA_USERNAME: str = os.getenv("HAKKA_USERNAME", os.getenv("CREDENTIAL_USERNAME", ""))
    HAKKA_PASSWORD: str = os.getenv("HAKKA_PASSWORD", os.getenv("CREDENTIAL_PASSWORD", ""))
    HAKKA_TTS_API_URL: str = os.getenv("HAKKA_TTS_API_URL", "https://hktts.bronci.com.tw")
    HAKKA_TRANSLATE_API_URL: str = os.getenv("HAKKA_TRANSLATE_API_URL", "https://hktrans.bronci.com.tw")
    
    # Application Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8000")
    
    # Email Configuration (SMTP)
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "True").lower() == "true"
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "noreply@hakkast.com")
    
    class Config:
        env_file = Path(__file__).parent.parent.parent / ".env"

settings = Settings()