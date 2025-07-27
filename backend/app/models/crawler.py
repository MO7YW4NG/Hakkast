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

class CrawlerSource(BaseModel):
    name: str
    base_url: HttpUrl
    content_type: ContentType
    selectors: Dict[str, str]  # CSS selectors for extracting content
    headers: Optional[Dict[str, str]] = None
    rate_limit: float = 1.0  # Seconds between requests
    max_pages: int = 5
    keywords: List[str] = []

class TopicCrawlerConfig(BaseModel):
    topic: str
    sources: List[CrawlerSource]
    keywords: List[str]
    exclude_keywords: List[str] = []
    max_articles: int = 10
    freshness_hours: int = 24  # Only fetch content newer than this

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

class CrawlerResult(BaseModel):
    topic: str
    total_found: int
    content_items: List[CrawledContent]
    crawl_duration: float
    sources_used: List[str]
    error_count: int = 0
    errors: List[str] = []

# Predefined crawler configurations for different topics
CRAWLER_CONFIGS = {
    "gaming_news": TopicCrawlerConfig(
        topic="gaming_news",
        keywords=["gaming", "video games", "esports", "game review", "gaming industry", "indie games", "AAA games"],
        exclude_keywords=["gambling", "casino"],
        sources=[
            CrawlerSource(
                name="IGN",
                base_url="https://www.ign.com/articles",
                content_type=ContentType.NEWS,
                selectors={
                    "title": "h1.article-headline",
                    "content": ".article-content",
                    "published": "time.publish-date"
                },
                keywords=["game", "gaming", "review"]
            ),
            CrawlerSource(
                name="GameSpot",
                base_url="https://www.gamespot.com/articles/",
                content_type=ContentType.NEWS,
                selectors={
                    "title": "h1.news-title",
                    "content": ".js-content-entity-body",
                    "published": "time"
                },
                keywords=["game", "gaming"]
            ),
            CrawlerSource(
                name="PC Gamer",
                base_url="https://www.pcgamer.com/news/",
                content_type=ContentType.NEWS,
                selectors={
                    "title": "h1",
                    "content": ".article-content",
                    "published": "time"
                },
                keywords=["pc gaming", "gaming news"]
            )
        ]
    ),
    
    "research_deep_learning": TopicCrawlerConfig(
        topic="research_deep_learning",
        keywords=["deep learning", "neural networks", "machine learning", "AI research", "artificial intelligence", "transformer", "computer vision", "NLP"],
        exclude_keywords=["cryptocurrency", "trading"],
        sources=[
            CrawlerSource(
                name="arXiv",
                base_url="https://arxiv.org/list/cs.LG/recent",
                content_type=ContentType.RESEARCH,
                selectors={
                    "title": ".list-title",
                    "content": ".abstract",
                    "published": ".list-dateline"
                },
                keywords=["deep learning", "machine learning"]
            ),
            CrawlerSource(
                name="Papers with Code",
                base_url="https://paperswithcode.com/latest",
                content_type=ContentType.RESEARCH,
                selectors={
                    "title": ".paper-title",
                    "content": ".paper-abstract",
                    "published": ".item-strip-date"
                },
                keywords=["deep learning", "AI"]
            ),
            CrawlerSource(
                name="Towards Data Science",
                base_url="https://towardsdatascience.com/latest",
                content_type=ContentType.BLOG,
                selectors={
                    "title": "h1",
                    "content": ".pw-post-body-paragraph",
                    "published": "time"
                },
                keywords=["machine learning", "deep learning"]
            )
        ]
    ),
    
    "technology_news": TopicCrawlerConfig(
        topic="technology_news",
        keywords=["technology", "tech news", "startup", "innovation", "AI", "blockchain", "cloud computing", "cybersecurity"],
        sources=[
            CrawlerSource(
                name="TechCrunch",
                base_url="https://techcrunch.com/category/artificial-intelligence/",
                content_type=ContentType.NEWS,
                selectors={
                    "title": "h1.article__title",
                    "content": ".article-content",
                    "published": "time.article__date"
                },
                keywords=["tech", "technology", "startup"]
            ),
            CrawlerSource(
                name="The Verge",
                base_url="https://www.theverge.com/tech",
                content_type=ContentType.NEWS,
                selectors={
                    "title": "h1.duet--article--headline",
                    "content": ".duet--article--article-body",
                    "published": "time"
                },
                keywords=["technology", "tech news"]
            )
        ]
    ),
    
    "health_wellness": TopicCrawlerConfig(
        topic="health_wellness",
        keywords=["health", "wellness", "nutrition", "fitness", "mental health", "medical research"],
        sources=[
            CrawlerSource(
                name="Healthline",
                base_url="https://www.healthline.com/health-news",
                content_type=ContentType.NEWS,
                selectors={
                    "title": "h1",
                    "content": ".article-body",
                    "published": "time"
                },
                keywords=["health", "wellness"]
            )
        ]
    ),
    
    "climate_environment": TopicCrawlerConfig(
        topic="climate_environment",
        keywords=["climate change", "environment", "sustainability", "renewable energy", "carbon", "global warming"],
        sources=[
            CrawlerSource(
                name="Climate Central",
                base_url="https://www.climatecentral.org/news",
                content_type=ContentType.NEWS,
                selectors={
                    "title": "h1",
                    "content": ".field-item",
                    "published": "time"
                },
                keywords=["climate", "environment"]
            )
        ]
    ),
    
    "finance_economics": TopicCrawlerConfig(
        topic="finance_economics",
        keywords=["finance", "economics", "stock market", "cryptocurrency", "investment", "banking"],
        sources=[
            CrawlerSource(
                name="Financial Times",
                base_url="https://www.ft.com/technology",
                content_type=ContentType.NEWS,
                selectors={
                    "title": "h1.headline",
                    "content": ".article__content-body",
                    "published": "time"
                },
                keywords=["finance", "economics"]
            )
        ]
    )
}