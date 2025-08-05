from pydantic import BaseModel, Field
from typing import Optional, Literal, List
from datetime import datetime
import uuid
from enum import Enum

class HostConfig(BaseModel):
    name: str = Field(..., description="Host name")
    gender: Literal["male", "female"] = Field(..., description="Host gender for TTS voice selection")
    dialect: Optional[Literal["sihxian", "hailu"]] = Field(None, description="Hakka dialect for this host (required for bilingual mode)")
    personality: Optional[str] = Field(
        default="理性、專業、分析", 
        description="Host personality traits for AI script generation (e.g., '理性、專業、分析', '幽默、活潑、互動')"
    )

class Topic(Enum):
    research_deep_learning = "research_deep_learning"
    technology_news = "technology_news"
    finance_economics = "finance_economics"

class PodcastGenerationRequest(BaseModel):
    topic: Topic = Field(..., description="The topic for the podcast")
    duration: int = Field(..., ge=3, le=60, description="Duration in minutes")
    language: Literal["hakka", "bilingual"] = Field(
        "hakka", description="Language mix for the podcast"
    )
    hosts: List[HostConfig] = Field(
        default=[
            HostConfig(name="佳昀", gender="female", dialect="sihxian", personality="理性、專業、分析"),
            HostConfig(name="敏權", gender="male", dialect="sihxian", personality="幽默、活潑、互動")
        ], 
        min_items=1, 
        max_items=2, 
        description="List of host configurations"
    )
    interests: Optional[str] = Field(None, description="Personal interests for personalization")

class Podcast(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    chinese_content: str
    hakka_content: str
    romanization: Optional[str] = None
    topic: str
    duration: int
    language: Literal["hakka", "bilingual"]
    hosts: List[HostConfig] = Field(default=[
        HostConfig(name="佳昀", gender="female", dialect="sihxian", personality="理性、專業、分析"),
        HostConfig(name="敏權", gender="male", dialect="sihxian", personality="幽默、活潑、互動")
    ])
    interests: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    audio_url: Optional[str] = None
    audio_duration: Optional[int] = None

class PodcastResponse(BaseModel):
    id: str
    title: str
    chineseContent: str
    hakkaContent: str
    romanization: Optional[str] = None
    topic: str
    duration: int
    language: str
    hosts: List[HostConfig] = Field(default=[
        HostConfig(name="佳昀", gender="female", dialect="sihxian", personality="理性、專業、分析"),
        HostConfig(name="敏權", gender="male", dialect="sihxian", personality="幽默、活潑、互動")
    ])
    interests: Optional[str] = None
    createdAt: str
    audioUrl: Optional[str] = None
    audioDuration: Optional[int] = None


class PodcastScriptContent(BaseModel):
    speaker: str
    text: str
    hakka_text: Optional[str] = None # 客語漢字
    romanization: Optional[str] = None # 數字調
    romanization_tone: Optional[str] = None  # 調型符號

class PodcastScript(BaseModel):
    title: str
    hosts: List[HostConfig]
    content: List[PodcastScriptContent]


# class PydanticPodcastScript(BaseModel):
#     title: str
#     hosts: List[str]  
#     full_dialogue: str  
#     estimated_duration_minutes: int
#     key_points: List[str]
#     sources_mentioned: List[str]

class EnglishTranslationResult(BaseModel):
    """英文翻譯結果模型"""
    original_texts: List[str]  # 翻譯前的英文文本列表
    translated_texts: List[str]  # 翻譯後的中文文本列表
    processed_content: str  # 替換英文後的完整文本
