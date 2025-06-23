from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import logging
import asyncio

from ..models.crawler import CrawlerResult, CrawledContent, CRAWLER_CONFIGS
from ..services.crawler_service import ContentCrawlerService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/crawler", tags=["crawler"])

@router.get("/topics", response_model=List[str])
async def get_available_crawler_topics():
    """Get list of available crawler topics"""
    return list(CRAWLER_CONFIGS.keys())

@router.get("/configs")
async def get_crawler_configs():
    """Get all crawler configurations (admin endpoint)"""
    return {
        topic: {
            "topic": config.topic,
            "keywords": config.keywords,
            "sources": [
                {
                    "name": source.name,
                    "base_url": str(source.base_url),
                    "content_type": source.content_type
                }
                for source in config.sources
            ],
            "max_articles": config.max_articles,
            "freshness_hours": config.freshness_hours
        }
        for topic, config in CRAWLER_CONFIGS.items()
    }

@router.post("/crawl/{topic}", response_model=CrawlerResult)
async def crawl_topic_content(
    topic: str,
    max_articles: int = Query(default=10, ge=1, le=50),
    timeout: int = Query(default=30, ge=10, le=120)
):
    """Crawl content for a specific topic"""
    try:
        async with ContentCrawlerService() as crawler:
            result = await crawler.crawl_topic_content(topic, max_articles)
            return result
    except Exception as e:
        logger.error(f"Failed to crawl content for topic '{topic}': {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to crawl content: {str(e)}"
        )

@router.get("/search")
async def search_topics(
    query: str = Query(..., min_length=2),
    max_articles: int = Query(default=5, ge=1, le=20)
) -> CrawlerResult:
    """Search for content based on a query string"""
    try:
        async with ContentCrawlerService() as crawler:
            # Try to find the best matching topic
            result = await crawler.crawl_topic_content(query, max_articles)
            return result
    except Exception as e:
        logger.error(f"Failed to search content for query '{query}': {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search content: {str(e)}"
        )

@router.get("/test/{source_name}")
async def test_crawler_source(source_name: str):
    """Test a specific crawler source (admin endpoint)"""
    try:
        # Find the source in configurations
        target_source = None
        source_config = None
        
        for config in CRAWLER_CONFIGS.values():
            for source in config.sources:
                if source.name.lower() == source_name.lower():
                    target_source = source
                    source_config = config
                    break
            if target_source:
                break
        
        if not target_source:
            raise HTTPException(
                status_code=404,
                detail=f"Source '{source_name}' not found"
            )
        
        async with ContentCrawlerService() as crawler:
            # Test crawling just this source
            content_items, errors = await crawler._crawl_source(
                asyncio.Semaphore(1),
                target_source,
                source_config,
                5  # Test with 5 articles
            )
            
            return {
                "source": source_name,
                "success": len(errors) == 0,
                "articles_found": len(content_items),
                "errors": errors,
                "sample_titles": [item.title for item in content_items[:3]]
            }
            
    except Exception as e:
        logger.error(f"Failed to test source '{source_name}': {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to test source: {str(e)}"
        )

@router.get("/stats")
async def get_crawler_stats():
    """Get crawler statistics and status"""
    try:
        stats = {
            "total_topics": len(CRAWLER_CONFIGS),
            "topics": {},
            "total_sources": 0
        }
        
        for topic, config in CRAWLER_CONFIGS.items():
            stats["topics"][topic] = {
                "sources_count": len(config.sources),
                "keywords": config.keywords,
                "max_articles": config.max_articles
            }
            stats["total_sources"] += len(config.sources)
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get crawler stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stats: {str(e)}"
        )