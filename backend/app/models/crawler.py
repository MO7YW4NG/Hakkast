from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class ContentType(str, Enum):
    NEWS = "news"
    RESEARCH = "research"
    BLOG = "blog"
    SOCIAL = "social"
    VIDEO = "video"

class CrawledContent(BaseModel):
    id: str
    title: str
    content: str
    summary: str
    url: HttpUrl
    source: str
    published_at: Optional[datetime] = None
    crawled_at: datetime
    content_type: ContentType
    topic: str
    keywords: List[str]
    relevance_score: float = 0.0
    #cc
    license_url: str = ""
    license_type: str = ""
