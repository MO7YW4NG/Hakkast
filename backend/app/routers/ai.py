from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import logging

from app.services.ai_service import AIService, AgentService
from app.models.crawler import CrawledContent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])

# Request/Response Models
class ScriptGenerationRequest(BaseModel):
    articles: List[Dict[str, Any]] = Field(..., description="List of crawled articles")
    max_minutes: int = Field(default=25, description="Maximum duration in minutes")
    hosts: List[str] = Field(default=["佳昀", "敏權"], description="Host names")

class ScriptGenerationResponse(BaseModel):
    original_script: Dict[str, Any]
    tts_ready_script: Dict[str, Any]
    total_characters: int
    estimated_duration: int
    hosts: List[str]
    success: bool

class EnglishTranslationRequest(BaseModel):
    text: str = Field(..., description="Text containing English to translate")

class EnglishTranslationResponse(BaseModel):
    original_texts: List[str]
    translated_texts: List[str]
    processed_content: str
    translation_count: int
    success: bool

class DialogueRequest(BaseModel):
    prompt: str = Field(..., description="Prompt for generating dialogue")
    context: Optional[str] = Field(None, description="Optional context")

class DialogueResponse(BaseModel):
    response: str
    model_used: str
    success: bool

# Dependencies
def get_ai_service() -> AIService:
    return AIService()

def get_agent_service() -> AgentService:
    return AgentService()

@router.post("/generate-script", response_model=ScriptGenerationResponse)
async def generate_podcast_script(
    request: ScriptGenerationRequest,
    service: AIService = Depends(get_ai_service)
):
    """Generate podcast script using AI agents from crawled articles"""
    try:
        # Convert articles dict to CrawledContent objects
        articles = []
        for article_data in request.articles:
            # Handle different input formats
            if isinstance(article_data, dict):
                article = CrawledContent(
                    title=article_data.get("title", ""),
                    content=article_data.get("content", ""),
                    summary=article_data.get("summary", ""),
                    url=article_data.get("url", ""),
                    source=article_data.get("source", ""),
                    published_at=article_data.get("published_at"),
                    license_url=article_data.get("license_url", ""),
                    license_type=article_data.get("license_type", "")
                )
                articles.append(article)
        
        if not articles:
            raise HTTPException(
                status_code=400,
                detail="No valid articles provided"
            )
        
        # Generate script using AI service
        result = await service.generate_podcast_script_with_agents(
            articles=articles,
            max_minutes=request.max_minutes
        )
        
        # Handle both dict and direct script return formats
        if isinstance(result, dict):
            original_script = result.get("original_script")
            tts_ready_script = result.get("tts_ready_script")
        else:
            # Fallback for older format
            original_script = result
            tts_ready_script = result
        
        # Calculate metrics
        if hasattr(original_script, 'content'):
            total_chars = sum(len(item.text) for item in original_script.content)
        else:
            total_chars = 0
        
        estimated_duration = max(1, total_chars // 120)  # Rough estimate: 120 chars per minute
        
        return ScriptGenerationResponse(
            original_script=original_script.dict() if hasattr(original_script, 'dict') else original_script,
            tts_ready_script=tts_ready_script.dict() if hasattr(tts_ready_script, 'dict') else tts_ready_script,
            total_characters=total_chars,
            estimated_duration=estimated_duration,
            hosts=request.hosts,
            success=True
        )
        
    except Exception as e:
        logger.error(f"Script generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Script generation failed: {str(e)}"
        )

@router.post("/translate-english", response_model=EnglishTranslationResponse)
async def translate_english_to_chinese(
    request: EnglishTranslationRequest,
    service: AgentService = Depends(get_agent_service)
):
    """Translate English text to Chinese using AI service"""
    try:
        result = await service.translate_english_to_chinese(request.text)
        
        return EnglishTranslationResponse(
            original_texts=result.original_texts,
            translated_texts=result.translated_texts,
            processed_content=result.processed_content,
            translation_count=len(result.original_texts),
            success=bool(result.original_texts)
        )
        
    except Exception as e:
        logger.error(f"English translation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"English translation failed: {str(e)}"
        )

@router.post("/generate-reply", response_model=DialogueResponse)
async def generate_dialogue_reply(
    request: DialogueRequest,
    service: AgentService = Depends(get_agent_service)
):
    """Generate AI dialogue response"""
    try:
        # Combine prompt with context if provided
        full_prompt = request.prompt
        if request.context:
            full_prompt = f"Context: {request.context}\n\nPrompt: {request.prompt}"
        
        response = await service.generate_reply(full_prompt)
        
        return DialogueResponse(
            response=response,
            model_used="gemini-flash",
            success=bool(response)
        )
        
    except Exception as e:
        logger.error(f"Dialogue generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Dialogue generation failed: {str(e)}"
        )

@router.get("/models")
async def get_available_ai_models():
    """Get information about available AI models"""
    return {
        "models": [
            {
                "name": "gemini-2.5-flash",
                "type": "dialogue_generation",
                "description": "Fast response generation for podcast scripts",
                "provider": "google"
            },
            {
                "name": "gemini-2.5-pro",
                "type": "translation",
                "description": "High-quality English to Chinese translation",
                "provider": "google"
            },
            {
                "name": "twcc-llama",
                "type": "dialogue_generation",
                "description": "TWCC AFS Llama model for script generation",
                "provider": "twcc"
            }
        ]
    }

@router.post("/test-dialogue")
async def test_dialogue_generation(
    prompt: str = "請用繁體中文介紹客家文化",
    service: AgentService = Depends(get_agent_service)
):
    """Test dialogue generation with sample prompt"""
    try:
        response = await service.generate_reply(prompt)
        
        return {
            "test_prompt": prompt,
            "response": response,
            "response_length": len(response),
            "service_status": "working" if response else "error"
        }
        
    except Exception as e:
        logger.error(f"Dialogue test failed: {e}")
        return {
            "test_prompt": prompt,
            "error": str(e),
            "service_status": "error"
        }

@router.post("/test-translation")
async def test_english_translation(
    text: str = "Welcome to Hakkast podcast. This is an AI-powered system.",
    service: AgentService = Depends(get_agent_service)
):
    """Test English translation with sample text"""
    try:
        result = await service.translate_english_to_chinese(text)
        
        return {
            "test_text": text,
            "original_texts": result.original_texts,
            "translated_texts": result.translated_texts,
            "processed_content": result.processed_content,
            "translation_count": len(result.original_texts),
            "service_status": "working" if result.original_texts else "error"
        }
        
    except Exception as e:
        logger.error(f"Translation test failed: {e}")
        return {
            "test_text": text,
            "error": str(e),
            "service_status": "error"
        }

@router.get("/capabilities")
async def get_ai_capabilities():
    """Get information about AI service capabilities"""
    return {
        "capabilities": [
            {
                "name": "script_generation",
                "description": "Generate podcast scripts from news articles",
                "input": "List of crawled articles",
                "output": "Structured podcast script with multiple speakers"
            },
            {
                "name": "english_translation", 
                "description": "Translate English text to Traditional Chinese",
                "input": "Text containing English words/phrases",
                "output": "Chinese text with translation mappings"
            },
            {
                "name": "dialogue_generation",
                "description": "Generate natural dialogue responses",
                "input": "Prompt with optional context",
                "output": "AI-generated response in Traditional Chinese"
            }
        ],
        "supported_languages": ["Traditional Chinese", "English"],
        "model_providers": ["Google Gemini", "TWCC AFS"]
    }

@router.get("/stats")
async def get_ai_service_stats():
    """Get AI service usage statistics"""
    # This would typically connect to a database or metrics system
    # For now, return mock data
    return {
        "total_scripts_generated": 0,
        "total_translations": 0,
        "total_dialogue_responses": 0,
        "active_models": ["gemini-2.5-flash", "gemini-2.5-pro"],
        "last_updated": "2024-01-01T00:00:00Z"
    }