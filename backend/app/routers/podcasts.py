from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import logging

from app.models.podcast import PodcastGenerationRequest, PodcastResponse, HostConfig
from app.services.podcast_service import PodcastService

logger = logging.getLogger(__name__)

service = PodcastService()
router = APIRouter(prefix="/podcasts", tags=["podcasts"])

# Request/Response Models
class ScriptFileRequest(BaseModel):
    script_file_path: str = Field(..., description="Path to the script JSON file")
    language: str = Field(default="bilingual", description="Language mode (hakka or bilingual)")
    hosts: List[HostConfig] = Field(
        default=[
            HostConfig(name="佳昀", gender="female", dialect="sihxian", personality="理性、專業、分析"),
            HostConfig(name="敏權", gender="male", dialect="sihxian", personality="幽默、活潑、互動")
        ],
        description="List of host configurations"
    )

class AudioGenerationResponse(BaseModel):
    success: bool
    script_name: str
    total_audio_files: int
    total_duration: float
    playlist_file: Optional[str] = None
    merged_audio_file: Optional[str] = None
    error_message: Optional[str] = None

class ConfigResponse(BaseModel):
    dialects: List[Dict[str, str]]
    topics: List[str]
    crawl_topics: List[str]
    default_hosts: List[str]
    available_speakers: List[Dict[str, str]]

# Core Podcast CRUD Endpoints
@router.post("/generate", response_model=PodcastResponse)
async def generate_podcast(
    request: PodcastGenerationRequest,
):
    """Generate a new Hakka podcast"""
    try:
        result = await service.generate_podcast(request)
        return result["podcast"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate podcast: {str(e)}")

@router.post("/generate-audio-from-script-file", response_model=AudioGenerationResponse)
async def generate_audio_from_script_file(
    request: ScriptFileRequest,
):
    """Generate audio from existing script file"""
    try:
        result = await service.generate_podcast_from_script_file(
            request.script_file_path, 
            language=request.language,
            hosts=request.hosts
        )
        
        if result.get("success"):
            audio_result = result.get("audio_result", {})
            return AudioGenerationResponse(
                success=True,
                script_name=result.get("script_name", ""),
                total_audio_files=audio_result.get("total_audio_files", 0),
                total_duration=audio_result.get("total_duration", 0),
                playlist_file=audio_result.get("final_audio_file"),
                merged_audio_file=None,
                error_message=None
            )
        else:
            return AudioGenerationResponse(
                success=False,
                script_name=request.script_file_path,
                total_audio_files=0,
                total_duration=0,
                playlist_file=None,
                merged_audio_file=None,
                error_message=result.get("error", "Unknown error")
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate audio from script file: {str(e)}")

@router.get("/", response_model=List[PodcastResponse])
async def get_podcasts(
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

@router.post("/merge-audio-files", response_model=Dict[str, Any])
async def merge_audio_files(
    script_name: str = Query(..., description="Script name to merge audio files for"),
    auto_merge: bool = Query(default=False, description="Whether to automatically merge without confirmation"),
):
    """Merge audio files into complete podcast"""
    try:
        result = await service.merge_audio_files(script_name, auto_merge=auto_merge)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to merge audio files: {str(e)}")

@router.get("/audio-files/{script_name}")
async def get_audio_files(
    script_name: str,
):
    """Get audio files for a specific script"""
    try:
        # Check for available audio files
        speaker_codes = ["SXF", "SXM", "HLF", "HLM"]
        audio_files = {}
        
        for code in speaker_codes:
            files = service.audio_manager.get_organized_files(script_name, code)
            if files:
                audio_files[code] = [f.name for f in files]
        
        return {
            "script_name": script_name,
            "audio_files": audio_files,
            "total_speakers": len(audio_files),
            "total_files": sum(len(files) for files in audio_files.values())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get audio files: {str(e)}")

@router.get("/audio-info/{script_name}")
async def get_audio_info(
    script_name: str,       
):
    """Get detailed audio information for a script"""
    try:
        speaker_codes = ["SXF", "SXM", "HLF", "HLM"]
        audio_info = {}
        
        for code in speaker_codes:
            files = service.audio_manager.get_organized_files(script_name, code)
            if files:
                audio_info[code] = {
                    "file_count": len(files),
                    "files": [f.name for f in files],
                    "total_size_mb": sum(f.stat().st_size for f in files) / (1024 * 1024)
                }
        
        return {
            "script_name": script_name,
            "audio_info": audio_info,
            "summary": {
                "total_speakers": len(audio_info),
                "total_files": sum(info["file_count"] for info in audio_info.values()),
                "total_size_mb": sum(info["total_size_mb"] for info in audio_info.values())
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get audio info: {str(e)}")


