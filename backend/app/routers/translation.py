from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from pydantic import BaseModel, Field
import logging

from app.services.translation_service import TranslationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/translation", tags=["translation"])

# Request/Response Models
class TranslationRequest(BaseModel):
    text: str = Field(..., description="Chinese text to translate")
    dialect: str = Field(default="sihxian", description="Hakka dialect: 'sihxian' or 'hailu'")

class TranslationResponse(BaseModel):
    original_text: str
    hakka_text: str
    romanization: str
    romanization_tone: str
    dialect: str
    success: bool

class BatchTranslationRequest(BaseModel):
    texts: List[str] = Field(..., description="List of Chinese texts to translate")
    dialect: str = Field(default="sihxian", description="Hakka dialect: 'sihxian' or 'hailu'")

class BatchTranslationResponse(BaseModel):
    results: List[TranslationResponse]
    total_processed: int
    success_count: int
    error_count: int

# Dependency
def get_translation_service() -> TranslationService:
    return TranslationService()

@router.post("/chinese-to-hakka", response_model=TranslationResponse)
async def translate_chinese_to_hakka(
    request: TranslationRequest,
    service: TranslationService = Depends(get_translation_service)
):
    """Translate Chinese text to Hakka language"""
    try:
        # Login to translation service
        if not service.headers:
            await service.login()
        
        result = await service.translate_chinese_to_hakka(
            chinese_text=request.text,
            dialect=request.dialect
        )
        
        return TranslationResponse(
            original_text=request.text,
            hakka_text=result.get("hakka_text", ""),
            romanization=result.get("romanization", ""),
            romanization_tone=result.get("romanization_tone", ""),
            dialect=request.dialect,
            success=bool(result.get("hakka_text"))
        )
        
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Translation failed: {str(e)}"
        )
    finally:
        await service.close()

@router.post("/batch", response_model=BatchTranslationResponse)
async def batch_translate(
    request: BatchTranslationRequest,
    service: TranslationService = Depends(get_translation_service)
):
    """Batch translate multiple Chinese texts to Hakka"""
    try:
        # Login to translation service
        if not service.headers:
            await service.login()
        
        results = []
        success_count = 0
        error_count = 0
        
        for text in request.texts:
            try:
                result = await service.translate_chinese_to_hakka(
                    chinese_text=text,
                    dialect=request.dialect
                )
                
                translation_result = TranslationResponse(
                    original_text=text,
                    hakka_text=result.get("hakka_text", ""),
                    romanization=result.get("romanization", ""),
                    romanization_tone=result.get("romanization_tone", ""),
                    dialect=request.dialect,
                    success=bool(result.get("hakka_text"))
                )
                
                results.append(translation_result)
                if translation_result.success:
                    success_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                logger.warning(f"Failed to translate text: {text[:50]}... Error: {e}")
                results.append(TranslationResponse(
                    original_text=text,
                    hakka_text="",
                    romanization="",
                    romanization_tone="",
                    dialect=request.dialect,
                    success=False
                ))
                error_count += 1
        
        return BatchTranslationResponse(
            results=results,
            total_processed=len(request.texts),
            success_count=success_count,
            error_count=error_count
        )
        
    except Exception as e:
        logger.error(f"Batch translation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Batch translation failed: {str(e)}"
        )
    finally:
        await service.close()

@router.get("/dialects")
async def get_supported_dialects():
    """Get list of supported Hakka dialects"""
    return {
        "dialects": [
            {
                "code": "sihxian",
                "name": "四縣腔",
                "english_name": "Sixian"
            },
            {
                "code": "hailu",
                "name": "海陸腔",
                "english_name": "Hailu"
            }
        ]
    }

@router.post("/test")
async def test_translation_service(
    dialect: str = "sihxian",
    service: TranslationService = Depends(get_translation_service)
):
    """Test translation service with sample text"""
    try:
        test_text = "歡迎收聽客家播客節目"
        
        # Login to translation service
        if not service.headers:
            await service.login()
        
        result = await service.translate_chinese_to_hakka(
            chinese_text=test_text,
            dialect=dialect
        )
        
        return {
            "test_text": test_text,
            "dialect": dialect,
            "result": result,
            "service_status": "working" if result.get("hakka_text") else "error"
        }
        
    except Exception as e:
        logger.error(f"Translation service test failed: {e}")
        return {
            "test_text": test_text,
            "dialect": dialect,
            "error": str(e),
            "service_status": "error"
        }
    finally:
        await service.close()