from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class SubscriptionFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"

class LanguageMode(str, Enum):
    HAKKA = "hakka"
    BILINGUAL = "bilingual"

class ToneStyle(str, Enum):
    CASUAL = "casual"
    EDUCATIONAL = "educational"
    STORYTELLING = "storytelling"
    INTERVIEW = "interview"

class SubscriptionPreferences(BaseModel):
    delivery_time: str  # "08:00" format
    delivery_days: Optional[List[int]] = None  # 0-6, Sunday=0, only for weekly
    max_duration: int = 10  # minutes
    include_transcript: bool = True
    include_romanization: bool = False
    notification_email: bool = True

class SubscriptionCreate(BaseModel):
    email: EmailStr
    frequency: SubscriptionFrequency
    topics: List[str]
    language: LanguageMode
    tone: ToneStyle
    preferences: SubscriptionPreferences

class SubscriptionUpdate(BaseModel):
    frequency: Optional[SubscriptionFrequency] = None
    topics: Optional[List[str]] = None
    language: Optional[LanguageMode] = None
    tone: Optional[ToneStyle] = None
    preferences: Optional[SubscriptionPreferences] = None
    is_active: Optional[bool] = None

class Subscription(BaseModel):
    id: str
    email: EmailStr
    frequency: SubscriptionFrequency
    topics: List[str]
    language: LanguageMode
    tone: ToneStyle
    is_active: bool = True
    created_at: datetime
    last_sent: Optional[datetime] = None
    preferences: SubscriptionPreferences
    rss_token: str  # For RSS feed authentication

class PodcastEpisode(BaseModel):
    id: str
    title: str
    description: str
    audio_url: str
    published_at: datetime
    duration: int  # seconds
    topics: List[str]
    hakka_content: str
    chinese_content: str
    romanization: Optional[str] = None

class PodcastFeed(BaseModel):
    title: str
    description: str
    episodes: List[PodcastEpisode]
    last_updated: datetime
    language: str
    author: str = "Hakkast AI"

class EmailTemplate(BaseModel):
    subject: str
    html_content: str
    text_content: str
    podcast_url: str
    unsubscribe_url: str