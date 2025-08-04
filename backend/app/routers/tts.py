from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import logging
from pathlib import Path

from app.services.tts_service import TTSService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tts", tags=["tts"])

# Request/Response Models
class TTSRequest(BaseModel):
    hakka_text: str = Field(..., description="Hakka text to convert to speech")
    romanization: str = Field(default="", description="Hakka romanization for pronunciation guidance")
    speaker: str = Field(default="hak-xi-TW-vs2-F01", description="Speaker/voice model ID")
    script_name: str = Field(default="audio", description="Script name for file organization")
    segment_index: int = Field(default=1, description="Segment index for ordering")

class TTSResponse(BaseModel):
    audio_id: str
    audio_url: str
    audio_path: str
    duration: int
    text: str
    romanization: str
    voice_model: str
    success: bool

class BatchTTSRequest(BaseModel):
    segments: List[Dict[str, Any]] = Field(..., description="List of TTS segments")
    script_name: str = Field(default="batch_audio", description="Script name for file organization")
    speaker_mapping: Dict[str, str] = Field(default={}, description="Speaker name to voice model mapping")

class BatchTTSResponse(BaseModel):
    results: List[TTSResponse]
    total_segments: int
    success_count: int
    error_count: int
    total_duration: int

class GeminiTTSRequest(BaseModel):
    text: str = Field(..., description="Text to convert to speech using Gemini TTS")
    output_filename: str = Field(default="", description="Custom output filename")

class SpeakerInfo(BaseModel):
    speaker_id: str
    dialect: str
    gender: str
    description: str

# Dependency
def get_tts_service() -> TTSService:
    return TTSService()

@router.post("/generate", response_model=TTSResponse)
async def generate_hakka_audio(
    request: TTSRequest,
    service: TTSService = Depends(get_tts_service)
):
    """Generate Hakka audio from text and romanization"""
    try:
        result = await service.generate_hakka_audio(
            hakka_text=request.hakka_text,
            romanization=request.romanization,
            speaker=request.speaker,
            segment_index=request.segment_index,
            script_name=request.script_name
        )
        
        return TTSResponse(
            audio_id=result.get("audio_id", ""),
            audio_url=result.get("audio_url", ""),
            audio_path=result.get("audio_path", ""),
            duration=result.get("duration", 0),
            text=result.get("text", request.hakka_text),
            romanization=result.get("romanization", request.romanization),
            voice_model=result.get("voice_model", request.speaker),
            success=bool(result.get("audio_id"))
        )
        
    except Exception as e:
        logger.error(f"TTS generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"TTS generation failed: {str(e)}"
        )
    finally:
        await service.close()

@router.post("/generate-gemini", response_model=TTSResponse)
async def generate_gemini_audio(
    request: GeminiTTSRequest,
    service: TTSService = Depends(get_tts_service)
):
    """Generate audio using Gemini TTS service"""
    try:
        # Generate output path
        audio_dir = Path("static/audio")
        audio_dir.mkdir(parents=True, exist_ok=True)
        
        if request.output_filename:
            output_path = str(audio_dir / request.output_filename)
        else:
            output_path = str(audio_dir / "gemini_audio.wav")
        
        result_path = await service.generate_gemini_tts(
            text=request.text,
            output_path=output_path
        )
        
        # Calculate duration (rough estimate)
        duration = max(10, len(request.text) * 0.5)
        
        return TTSResponse(
            audio_id=Path(result_path).stem,
            audio_url=f"/static/audio/{Path(result_path).name}",
            audio_path=result_path,
            duration=int(duration),
            text=request.text,
            romanization="",
            voice_model="gemini",
            success=True
        )
        
    except Exception as e:
        logger.error(f"Gemini TTS generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Gemini TTS generation failed: {str(e)}"
        )

@router.post("/batch", response_model=BatchTTSResponse)
async def batch_generate_audio(
    request: BatchTTSRequest,
    service: TTSService = Depends(get_tts_service)
):
    """Generate audio for multiple segments"""
    try:
        results = []
        success_count = 0
        error_count = 0
        total_duration = 0
        
        for i, segment in enumerate(request.segments):
            try:
                # Determine speaker
                speaker_name = segment.get("speaker", "")
                speaker_id = request.speaker_mapping.get(speaker_name, "hak-xi-TW-vs2-F01")
                
                result = await service.generate_hakka_audio(
                    hakka_text=segment.get("hakka_text", ""),
                    romanization=segment.get("romanization", ""),
                    speaker=speaker_id,
                    segment_index=i + 1,
                    script_name=request.script_name
                )
                
                tts_response = TTSResponse(
                    audio_id=result.get("audio_id", ""),
                    audio_url=result.get("audio_url", ""),
                    audio_path=result.get("audio_path", ""),
                    duration=result.get("duration", 0),
                    text=result.get("text", segment.get("hakka_text", "")),
                    romanization=result.get("romanization", segment.get("romanization", "")),
                    voice_model=result.get("voice_model", speaker_id),
                    success=bool(result.get("audio_id"))
                )
                
                results.append(tts_response)
                if tts_response.success:
                    success_count += 1
                    total_duration += tts_response.duration
                else:
                    error_count += 1
                    
            except Exception as e:
                logger.warning(f"Failed to generate audio for segment {i}: {e}")
                results.append(TTSResponse(
                    audio_id="",
                    audio_url="",
                    audio_path="",
                    duration=0,
                    text=segment.get("hakka_text", ""),
                    romanization=segment.get("romanization", ""),
                    voice_model="error",
                    success=False
                ))
                error_count += 1
        
        return BatchTTSResponse(
            results=results,
            total_segments=len(request.segments),
            success_count=success_count,
            error_count=error_count,
            total_duration=total_duration
        )
        
    except Exception as e:
        logger.error(f"Batch TTS generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Batch TTS generation failed: {str(e)}"
        )
    finally:
        await service.close()

@router.get("/speakers", response_model=List[SpeakerInfo])
async def get_available_speakers(
    service: TTSService = Depends(get_tts_service)
):
    """Get list of available TTS speakers/models"""
    try:
        # Login to get models
        if not service.headers:
            await service.login()
        
        models_info = await service.get_models()
        
        # Default speakers based on script analysis
        default_speakers = [
            SpeakerInfo(
                speaker_id="hak-xi-TW-vs2-F01",
                dialect="sihxian",
                gender="female",
                description="四縣腔女聲"
            ),
            SpeakerInfo(
                speaker_id="hak-xi-TW-vs2-M01",
                dialect="sihxian", 
                gender="male",
                description="四縣腔男聲"
            ),
            SpeakerInfo(
                speaker_id="hak-hoi-TW-vs2-F01",
                dialect="hailu",
                gender="female",
                description="海陸腔女聲"
            ),
            SpeakerInfo(
                speaker_id="hak-hoi-TW-vs2-M01",
                dialect="hailu",
                gender="male",
                description="海陸腔男聲"
            ),
            SpeakerInfo(
                speaker_id="gemini",
                dialect="general",
                gender="neutral",
                description="Gemini TTS (Universal)"
            )
        ]
        
        return default_speakers
        
    except Exception as e:
        logger.error(f"Failed to get speakers: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get speakers: {str(e)}"
        )
    finally:
        await service.close()

@router.post("/test")
async def test_tts_service(
    text: str = "歡迎收聽客家播客",
    speaker: str = "hak-xi-TW-vs2-F01",
    service: TTSService = Depends(get_tts_service)
):
    """Test TTS service with sample text"""
    try:
        result = await service.generate_hakka_audio(
            hakka_text=text,
            romanization="",
            speaker=speaker,
            segment_index=999,  # Test segment
            script_name="test"
        )
        
        return {
            "test_text": text,
            "speaker": speaker,
            "result": result,
            "service_status": "working" if result.get("audio_id") else "error"
        }
        
    except Exception as e:
        logger.error(f"TTS service test failed: {e}")
        return {
            "test_text": text,
            "speaker": speaker,
            "error": str(e),
            "service_status": "error"
        }
    finally:
        await service.close()

@router.get("/dialects")
async def get_tts_dialects():
    """Get supported dialects for TTS"""
    return {
        "dialects": [
            {
                "code": "sihxian",
                "name": "四縣腔",
                "speakers": ["hak-xi-TW-vs2-F01", "hak-xi-TW-vs2-M01"]
            },
            {
                "code": "hailu", 
                "name": "海陸腔",
                "speakers": ["hak-hoi-TW-vs2-F01", "hak-hoi-TW-vs2-M01"]
            },
            {
                "code": "general",
                "name": "通用",
                "speakers": ["gemini"]
            }
        ]
    }