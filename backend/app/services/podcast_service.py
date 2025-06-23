from typing import List, Optional
from datetime import datetime
from app.models.podcast import Podcast, PodcastGenerationRequest, PodcastResponse
from app.services.ai_service import AIService

class PodcastService:
    def __init__(self):
        self.ai_service = AIService()
        self.podcasts_storage: List[Podcast] = []  # In-memory storage for demo
    
    async def generate_podcast(self, request: PodcastGenerationRequest) -> PodcastResponse:
        """Generate a new podcast using AI"""
        
        # Generate content using AI service (3-step pipeline)
        ai_content = await self.ai_service.generate_hakka_podcast_content(request)
        
        # Create podcast object
        podcast = Podcast(
            title=ai_content["title"],
            chinese_content=ai_content["chinese_content"],
            hakka_content=ai_content["hakka_content"],
            romanization=ai_content.get("romanization"),
            topic=request.topic,
            tone=request.tone,
            duration=request.duration,
            language=request.language,
            interests=request.interests,
            audio_url=ai_content.get("audio_url"),
            audio_duration=ai_content.get("audio_duration")
        )
        
        # Store the podcast (in-memory for demo)
        self.podcasts_storage.append(podcast)
        
        return self._to_response(podcast)
    
    async def get_all_podcasts(self) -> List[PodcastResponse]:
        """Get all generated podcasts"""
        return [self._to_response(podcast) for podcast in self.podcasts_storage]
    
    async def get_podcast(self, podcast_id: str) -> Optional[PodcastResponse]:
        """Get a specific podcast by ID"""
        for podcast in self.podcasts_storage:
            if podcast.id == podcast_id:
                return self._to_response(podcast)
        return None
    
    async def delete_podcast(self, podcast_id: str) -> bool:
        """Delete a podcast by ID"""
        for i, podcast in enumerate(self.podcasts_storage):
            if podcast.id == podcast_id:
                del self.podcasts_storage[i]
                return True
        return False
    
    def _to_response(self, podcast: Podcast) -> PodcastResponse:
        """Convert Podcast model to PodcastResponse"""
        return PodcastResponse(
            id=podcast.id,
            title=podcast.title,
            chineseContent=podcast.chinese_content,
            hakkaContent=podcast.hakka_content,
            romanization=podcast.romanization,
            topic=podcast.topic,
            tone=podcast.tone,
            duration=podcast.duration,
            language=podcast.language,
            interests=podcast.interests,
            createdAt=podcast.created_at.isoformat(),
            audioUrl=podcast.audio_url,
            audioDuration=podcast.audio_duration
        )