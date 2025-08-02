from pydantic import BaseModel, Field
from typing import Optional, Literal, List
from datetime import datetime
import uuid

class PodcastGenerationRequest(BaseModel):
    topic: str = Field(..., description="The topic for the podcast")
    tone: Literal["casual", "educational", "storytelling", "interview"] = Field(
        "casual", description="The tone and style of the podcast"
    )
    duration: int = Field(..., ge=5, le=60, description="Duration in minutes")
    language: Literal["hakka", "mixed", "bilingual"] = Field(
        "mixed", description="Language mix for the podcast"
    )
    interests: Optional[str] = Field(None, description="Personal interests for personalization")

class Podcast(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    chinese_content: str
    hakka_content: str
    romanization: Optional[str] = None
    topic: str
    tone: Literal["casual", "educational", "storytelling", "interview"]
    duration: int
    language: Literal["hakka", "mixed", "bilingual"]
    interests: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    audio_url: Optional[str] = None
    audio_duration: Optional[int] = None

class PodcastResponse(BaseModel):
    id: str
    title: str
    chineseContent: str
    hakkaContent: str
    romanization: Optional[str] = None
    topic: str
    tone: str
    duration: int
    language: str
    interests: Optional[str] = None
    createdAt: str
    audioUrl: Optional[str] = None
    audioDuration: Optional[int] = None

#class PodcastScript(BaseModel):
#   title: str
#   hosts: list[str]
#    content: str
class PodcastScriptContent(BaseModel):
    speaker: str
    text: str
    hakka_text: Optional[str] = None # 客語漢字
    romanization: Optional[str] = None # 數字調
    romanization_tone: Optional[str] = None  # 調型符號

class PodcastScript(BaseModel):
    title: str
    hosts: List[str]
    content: List[PodcastScriptContent]

# 別名，為了向後兼容
PodcastSegment = PodcastScriptContent