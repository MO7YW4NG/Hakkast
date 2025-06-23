from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.models.podcast import PodcastGenerationRequest, PodcastResponse
from app.services.podcast_service import PodcastService

router = APIRouter()

# Dependency to get podcast service
def get_podcast_service() -> PodcastService:
    return PodcastService()

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