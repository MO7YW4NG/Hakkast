from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import logging
from pathlib import Path

from app.models.podcast import PodcastGenerationRequest, PodcastResponse
from app.models.crawler import CrawledContent
from app.services.podcast_service import PodcastService
from app.services.ai_service import AIService
from app.services.translation_service import TranslationService
from app.services.tts_service import TTSService
from app.services.crawl4ai_service import crawl_news

logger = logging.getLogger(__name__)

router = APIRouter()

# Enhanced Request/Response Models
class PipelineGenerationRequest(BaseModel):
    urls: List[str] = Field(..., description="List of URLs to crawl for content")
    max_minutes: int = Field(default=25, description="Maximum podcast duration in minutes")
    hosts: List[str] = Field(default=["佳昀", "敏權"], description="Host names")
    dialect: str = Field(default="sihxian", description="Hakka dialect")
    speaker_mapping: Dict[str, str] = Field(default={}, description="Speaker to voice model mapping")
    merge_audio: bool = Field(default=True, description="Whether to merge audio files")

class TopicPipelineRequest(BaseModel):
    topic: str = Field(..., description="Topic to crawl for content (e.g., 'technology_news', 'research_deep_learning')")
    max_articles: int = Field(default=5, ge=1, le=20, description="Maximum articles to crawl")
    max_minutes: int = Field(default=25, description="Maximum podcast duration in minutes")
    hosts: List[str] = Field(default=["佳昀", "敏權"], description="Host names")
    dialect: str = Field(default="sihxian", description="Hakka dialect")
    speaker_mapping: Dict[str, str] = Field(default={}, description="Speaker to voice model mapping")
    merge_audio: bool = Field(default=True, description="Whether to merge audio files")

class ScriptGenerationRequest(BaseModel):
    script_content: Dict[str, Any] = Field(..., description="Pre-generated script content")
    script_name: str = Field(default="custom_script", description="Script name for file organization")
    dialect: str = Field(default="sihxian", description="Hakka dialect")
    speaker_mapping: Dict[str, str] = Field(default={}, description="Speaker to voice model mapping")
    merge_audio: bool = Field(default=True, description="Whether to merge audio files")

class PipelineResponse(BaseModel):
    success: bool
    podcast_id: str
    script_name: str
    audio_files: List[str]
    merged_audio_url: Optional[str]
    total_duration: int
    error_message: Optional[str] = None

class ConfigResponse(BaseModel):
    dialects: List[Dict[str, str]]
    topics: List[str]
    crawl_topics: List[str]
    default_hosts: List[str]
    available_speakers: List[Dict[str, str]]

# Dependencies
def get_podcast_service() -> PodcastService:
    return PodcastService()

def get_ai_service() -> AIService:
    return AIService()

def get_translation_service() -> TranslationService:
    return TranslationService()

def get_tts_service() -> TTSService:
    return TTSService()

# Helper function to crawl URLs using crawl4ai_service
async def crawl_urls_for_content(urls: List[str]) -> List[CrawledContent]:
    """Crawl multiple URLs and return content using crawl4ai"""
    try:
        from crawl4ai import AsyncWebCrawler
        from app.services.crawl4ai_service import clean_content, extract_published_date
        from datetime import datetime
        
        articles = []
        
        async with AsyncWebCrawler() as crawler:
            for url in urls:
                try:
                    result = await crawler.arun(url)
                    
                    title = result.metadata.get("title", "No title")
                    content = getattr(result, "content", "")
                    
                    if not content or len(content.strip()) < 50:
                        logger.warning(f"Insufficient content from {url}")
                        continue
                    
                    # Clean content
                    cleaned_content = clean_content(content)
                    published_time = extract_published_date(url)
                    
                    article = CrawledContent(
                        id=url,
                        title=title,
                        content=cleaned_content,
                        summary=cleaned_content[:300] if cleaned_content else "",
                        url=url,
                        source="crawl4ai",
                        published_at=published_time,
                        crawled_at=datetime.now(),
                        content_type="news",
                        topic="general",
                        keywords=[],
                        relevance_score=0.0
                    )
                    articles.append(article)
                    
                except Exception as e:
                    logger.warning(f"Failed to crawl {url}: {e}")
        
        return articles
        
    except Exception as e:
        logger.error(f"Batch crawling failed: {e}")
        return []

@router.post("/generate", response_model=PodcastResponse)
async def generate_podcast(
    request: PodcastGenerationRequest,
    service: PodcastService = Depends(get_podcast_service)
):
    """Generate a new Hakka podcast"""
    try:
        podcast = await service.generate_podcast(request)
        return podcast
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate podcast: {str(e)}")

@router.get("/", response_model=List[PodcastResponse])
async def get_podcasts(
    service: PodcastService = Depends(get_podcast_service)
):
    """Get all generated podcasts"""
    try:
        podcasts = await service.get_all_podcasts()
        return podcasts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch podcasts: {str(e)}")

@router.get("/{podcast_id}", response_model=PodcastResponse)
async def get_podcast(
    podcast_id: str,
    service: PodcastService = Depends(get_podcast_service)
):
    """Get a specific podcast by ID"""
    try:
        podcast = await service.get_podcast(podcast_id)
        if not podcast:
            raise HTTPException(status_code=404, detail="Podcast not found")
        return podcast
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch podcast: {str(e)}")

@router.delete("/{podcast_id}")
async def delete_podcast(
    podcast_id: str,
    service: PodcastService = Depends(get_podcast_service)
):
    """Delete a podcast by ID"""
    try:
        deleted = await service.delete_podcast(podcast_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Podcast not found")
        return {"message": "Podcast deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete podcast: {str(e)}")

@router.post("/generate-with-crawling", response_model=PipelineResponse)
async def generate_podcast_with_crawling(
    request: PipelineGenerationRequest,
    ai_service: AIService = Depends(get_ai_service),
    translation_service: TranslationService = Depends(get_translation_service),
    tts_service: TTSService = Depends(get_tts_service)
):
    """Full pipeline: Crawl URLs → Generate Script → Translate → Generate Audio"""
    try:
        # Step 1: Crawl content from URLs using crawl4ai
        logger.info(f"Starting crawling for {len(request.urls)} URLs")
        articles = await crawl_urls_for_content(request.urls)
        
        if not articles:
            raise HTTPException(
                status_code=400,
                detail="No content could be crawled from provided URLs"
            )
        
        # Step 2: Generate Chinese script using AI
        logger.info(f"Generating script from {len(articles)} articles")
        script_result = await ai_service.generate_podcast_script_with_agents(
            articles=articles,
            max_minutes=request.max_minutes
        )
        
        # Extract script content
        if isinstance(script_result, dict):
            original_script = script_result.get("original_script")
        else:
            original_script = script_result
        
        if not original_script or not hasattr(original_script, 'content'):
            raise HTTPException(
                status_code=500,
                detail="Failed to generate valid script content"
            )
        
        # Step 3: Process script through translation and TTS pipeline
        return await _process_script_to_audio(
            script=original_script,
            script_name=f"crawled_{len(articles)}_articles",
            dialect=request.dialect,
            speaker_mapping=request.speaker_mapping,
            merge_audio=request.merge_audio,
            translation_service=translation_service,
            tts_service=tts_service
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Pipeline generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline generation failed: {str(e)}"
        )

@router.post("/generate-from-topic", response_model=PipelineResponse)
async def generate_podcast_from_topic(
    request: TopicPipelineRequest,
    ai_service: AIService = Depends(get_ai_service),
    translation_service: TranslationService = Depends(get_translation_service),
    tts_service: TTSService = Depends(get_tts_service)
):
    """Generate podcast from topic-based crawling using crawl4ai"""
    try:
        # Step 1: Crawl content using topic-based approach
        logger.info(f"Starting topic-based crawling for '{request.topic}' with max {request.max_articles} articles")
        
        # Use crawl4ai service for topic-based crawling
        articles = await crawl_news(request.topic, request.max_articles)
        
        if not articles:
            raise HTTPException(
                status_code=400,
                detail=f"No content could be crawled for topic '{request.topic}'"
            )
        
        # Step 2: Generate Chinese script using AI
        logger.info(f"Generating script from {len(articles)} articles for topic '{request.topic}'")
        script_result = await ai_service.generate_podcast_script_with_agents(
            articles=articles,
            max_minutes=request.max_minutes
        )
        
        # Extract script content
        if isinstance(script_result, dict):
            original_script = script_result.get("original_script")
        else:
            original_script = script_result
        
        if not original_script or not hasattr(original_script, 'content'):
            raise HTTPException(
                status_code=500,
                detail="Failed to generate valid script content"
            )
        
        # Step 3: Process script through translation and TTS pipeline
        return await _process_script_to_audio(
            script=original_script,
            script_name=f"topic_{request.topic}_{len(articles)}_articles",
            dialect=request.dialect,
            speaker_mapping=request.speaker_mapping,
            merge_audio=request.merge_audio,
            translation_service=translation_service,
            tts_service=tts_service
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Topic-based pipeline generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Topic-based pipeline generation failed: {str(e)}"
        )

@router.post("/generate-from-script", response_model=PipelineResponse)
async def generate_podcast_from_script(
    request: ScriptGenerationRequest,
    translation_service: TranslationService = Depends(get_translation_service),
    tts_service: TTSService = Depends(get_tts_service)
):
    """Generate podcast from pre-existing script content"""
    try:
        # Convert script content to expected format
        # This would need to match your script structure
        script_content = request.script_content
        
        return await _process_script_to_audio(
            script=script_content,
            script_name=request.script_name,
            dialect=request.dialect,
            speaker_mapping=request.speaker_mapping,
            merge_audio=request.merge_audio,
            translation_service=translation_service,
            tts_service=tts_service
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Script-based generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Script-based generation failed: {str(e)}"
        )

@router.get("/dialects")
async def get_podcast_dialects():
    """Get supported dialects for podcast generation"""
    return {
        "dialects": [
            {
                "code": "sihxian",
                "name": "四縣腔",
                "english_name": "Sixian",
                "speakers": ["hak-xi-TW-vs2-F01", "hak-xi-TW-vs2-M01"]
            },
            {
                "code": "hailu",
                "name": "海陸腔",
                "english_name": "Hailu",
                "speakers": ["hak-hoi-TW-vs2-F01", "hak-hoi-TW-vs2-M01"]
            }
        ]
    }

@router.get("/topics")
async def get_podcast_topics():
    """Get suggested topics for podcast generation"""
    return {
        "content_topics": [
            "客家文化",
            "傳統節慶", 
            "客家美食",
            "客家音樂",
            "客家歷史",
            "客家語言",
            "客家建築",
            "客家工藝",
            "時事新聞",
            "科技發展",
            "教育議題",
            "環境保護"
        ]
    }

@router.get("/crawl-topics")
async def get_crawl_topics():
    """Get available crawling topics from crawl4ai service"""
    try:
        from app.models.crawler import CRAWLER_CONFIGS
        
        crawl_topics = []
        for topic, config in CRAWLER_CONFIGS.items():
            crawl_topics.append({
                "name": topic,
                "keywords": config.keywords,
                "max_articles": config.max_articles,
                "sources_count": len(config.sources),
                "description": f"Crawls {len(config.sources)} sources for {topic} content"
            })
        
        return {
            "crawl_topics": crawl_topics,
            "total_topics": len(crawl_topics),
            "supported_topics": list(CRAWLER_CONFIGS.keys())
        }
        
    except Exception as e:
        logger.error(f"Failed to get crawl topics: {e}")
        return {
            "crawl_topics": [],
            "total_topics": 0,
            "supported_topics": [],
            "error": str(e)
        }

@router.get("/config", response_model=ConfigResponse)
async def get_podcast_config():
    """Get podcast generation configuration options"""
    return ConfigResponse(
        dialects=[
            {"code": "sihxian", "name": "四縣腔", "english_name": "Sixian"},
            {"code": "hailu", "name": "海陸腔", "english_name": "Hailu"}
        ],
        topics=[
            "客家文化", "傳統節慶", "客家美食", "客家音樂", "客家歷史",
            "客家語言", "客家建築", "客家工藝", "時事新聞", "科技發展"
        ],
        default_hosts=["佳昀", "敏權"],
        available_speakers=[
            {"id": "hak-xi-TW-vs2-F01", "name": "四縣腔女聲", "dialect": "sihxian", "gender": "female"},
            {"id": "hak-xi-TW-vs2-M01", "name": "四縣腔男聲", "dialect": "sihxian", "gender": "male"},
            {"id": "hak-hoi-TW-vs2-F01", "name": "海陸腔女聲", "dialect": "hailu", "gender": "female"},
            {"id": "hak-hoi-TW-vs2-M01", "name": "海陸腔男聲", "dialect": "hailu", "gender": "male"}
        ]
    )

# Helper Functions
async def _process_script_to_audio(
    script: Any,
    script_name: str,
    dialect: str,
    speaker_mapping: Dict[str, str],
    merge_audio: bool,
    translation_service: TranslationService,
    tts_service: TTSService
) -> PipelineResponse:
    """Helper function to process script through translation and TTS pipeline"""
    try:
        # Login to services
        if not translation_service.headers:
            await translation_service.login()
        if not tts_service.headers:
            await tts_service.login()
        
        audio_files = []
        total_duration = 0
        
        # Process each script segment
        if hasattr(script, 'content') and isinstance(script.content, list):
            segments = script.content
        else:
            # Handle different script formats
            segments = script if isinstance(script, list) else [script]
        
        for i, segment in enumerate(segments):
            try:
                # Extract text and speaker information
                if hasattr(segment, 'text'):
                    chinese_text = segment.text
                    speaker = getattr(segment, 'speaker', '佳昀')
                elif isinstance(segment, dict):
                    chinese_text = segment.get('text', '')
                    speaker = segment.get('speaker', '佳昀')
                else:
                    chinese_text = str(segment)
                    speaker = '佳昀'
                
                if not chinese_text.strip():
                    continue
                
                # Step 1: Translate Chinese to Hakka
                translation_result = await translation_service.translate_chinese_to_hakka(
                    chinese_text=chinese_text,
                    dialect=dialect
                )
                
                hakka_text = translation_result.get('hakka_text', '')
                romanization = translation_result.get('romanization', '')
                
                if not hakka_text:
                    logger.warning(f"Translation failed for segment {i}: {chinese_text[:50]}...")
                    continue
                
                # Step 2: Generate TTS audio
                speaker_id = speaker_mapping.get(speaker, "hak-xi-TW-vs2-F01")
                
                tts_result = await tts_service.generate_hakka_audio(
                    hakka_text=hakka_text,
                    romanization=romanization,
                    speaker=speaker_id,
                    segment_index=i + 1,
                    script_name=script_name
                )
                
                if tts_result.get('audio_path'):
                    audio_files.append(tts_result['audio_path'])
                    total_duration += tts_result.get('duration', 0)
                    logger.info(f"Generated audio for segment {i + 1}: {tts_result['audio_path']}")
                
            except Exception as e:
                logger.warning(f"Failed to process segment {i}: {e}")
        
        merged_audio_url = None
        if merge_audio and audio_files:
            try:
                # Merge audio files using FFmpeg
                merged_filename = f"{script_name}_merged.wav"
                merged_audio_url = await _merge_audio_files(audio_files, merged_filename)
            except Exception as e:
                logger.warning(f"Audio merge failed: {e}")
        
        return PipelineResponse(
            success=bool(audio_files),
            podcast_id=script_name,
            script_name=script_name,
            audio_files=[Path(f).name for f in audio_files],
            merged_audio_url=merged_audio_url,
            total_duration=total_duration,
            error_message=None if audio_files else "No audio files were generated"
        )
        
    except Exception as e:
        logger.error(f"Script processing failed: {e}")
        return PipelineResponse(
            success=False,
            podcast_id=script_name,
            script_name=script_name,
            audio_files=[],
            merged_audio_url=None,
            total_duration=0,
            error_message=str(e)
        )
    finally:
        await translation_service.close()
        await tts_service.close()

async def _merge_audio_files(audio_files: List[str], output_filename: str) -> str:
    """Helper function to merge audio files using FFmpeg"""
    import subprocess
    
    audio_dir = Path("static/audio")
    output_path = audio_dir / output_filename
    filelist_path = audio_dir / f"temp_filelist_{output_filename}.txt"
    
    try:
        # Create file list for FFmpeg
        with open(filelist_path, "w", encoding="utf-8") as f:
            for file_path in audio_files:
                f.write(f"file '{file_path}'\n")
        
        # FFmpeg command to merge files
        cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(filelist_path),
            '-ar', '44100',
            '-ac', '1',
            '-sample_fmt', 's16',
            '-y',  # Overwrite output file
            str(output_path)
        ]
        
        # Run FFmpeg
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"FFmpeg merge failed: {result.stderr}")
        
        return f"/static/audio/{output_filename}"
        
    finally:
        # Clean up temporary filelist
        if filelist_path.exists():
            filelist_path.unlink()