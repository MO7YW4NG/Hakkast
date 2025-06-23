import os
import uuid
import logging
from typing import Optional, Dict, Any
import httpx
from pathlib import Path
from app.core.config import settings

logger = logging.getLogger(__name__)

class TTSService:
    """Text-to-Speech service for Hakka language using Hakka AI Hackathon API"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0, verify=False)  # SSL verification disabled
        self.audio_dir = Path("static/audio")
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        
        self.base_url = settings.HAKKA_TTS_API_URL
        self.username = settings.HAKKA_USERNAME
        self.password = settings.HAKKA_PASSWORD
        self.token = None
        self.headers = None
    
    async def login(self):
        """Authenticate and obtain bearer token for TTS API requests"""
        try:
            login_payload = {
                'username': self.username,
                'password': self.password
            }
            
            response = await self.client.post(
                f'{self.base_url}/api/v1/tts/login',
                json=login_payload
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'token' in data:
                    self.token = data['token']
                    self.headers = {'Authorization': f'Bearer {self.token}'}
                    logger.info("Successfully authenticated with Hakka TTS API")
                    return True
                    
        except Exception as e:
            logger.error(f"TTS Login failed: {e}")
            
        return False
    
    async def logout(self):
        """Logout from TTS API"""
        try:
            if self.headers:
                await self.client.post(
                    f'{self.base_url}/api/v1/tts/logout',
                    headers=self.headers
                )
                self.token = None
                self.headers = None
                logger.info("Successfully logged out from Hakka TTS API")
        except Exception as e:
            logger.error(f"TTS Logout failed: {e}")
    
    async def get_models(self) -> Optional[Dict[str, Any]]:
        """Get available TTS voice models"""
        try:
            if not self.headers:
                await self.login()
                
            if not self.headers:
                return None
                
            response = await self.client.get(
                f'{self.base_url}/api/v1/tts/models',
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
                
        except Exception as e:
            logger.error(f"Failed to get TTS models: {e}")
            
        return None
    
    async def generate_hakka_audio(self, hakka_text: str, romanization: str = "") -> Dict[str, Any]:
        """
        Generate audio from Hakka text using Hakka AI TTS service
        
        Args:
            hakka_text: Hakka text to convert to speech
            romanization: Optional romanization for pronunciation guidance
            
        Returns:
            Dict containing audio file path and metadata
        """
        try:
            # Ensure we're authenticated
            if not self.headers:
                await self.login()
            
            if not self.headers:
                logger.warning("TTS Authentication failed, using fallback")
                return await self._generate_fallback_audio(hakka_text, romanization)
            
            # Prepare TTS request
            audio_id = str(uuid.uuid4())
            audio_filename = f"{audio_id}.wav"
            audio_path = self.audio_dir / audio_filename
            
            # Get available models (use first available Hakka model)
            models = await self.get_models()
            voice_model = "default"  # fallback
            
            if models and 'models' in models:
                # Look for Hakka models in the response
                hakka_models = [m for m in models['models'] if 'hakka' in m.get('name', '').lower()]
                if hakka_models:
                    voice_model = hakka_models[0]['name']
            
            # Prepare synthesis payload
            synthesis_payload = {
                'text': hakka_text,
                'voice_model': voice_model,
                'text_type': 'text',  # or adjust based on API requirements
                'language_code': 'hak'  # Hakka language code
            }
            
            # Call TTS synthesis API
            response = await self.client.post(
                f'{self.base_url}/api/v1/tts/synthesize',
                headers=self.headers,
                json=synthesis_payload
            )
            
            if response.status_code == 200:
                # Save audio data to file
                with open(audio_path, 'wb') as f:
                    f.write(response.content)
                
                # Calculate approximate duration (rough estimate)
                duration = max(10, len(hakka_text) * 0.5)  # ~0.5 seconds per character
                
                return {
                    "audio_id": audio_id,
                    "audio_path": str(audio_path),
                    "audio_url": f"/static/audio/{audio_filename}",
                    "duration": int(duration),
                    "text": hakka_text,
                    "romanization": romanization,
                    "voice_model": voice_model
                }
            else:
                logger.error(f"TTS API error: {response.status_code}")
                return await self._generate_fallback_audio(hakka_text, romanization)
                
        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            return await self._generate_fallback_audio(hakka_text, romanization)
    
    async def _generate_fallback_audio(self, hakka_text: str, romanization: str = "") -> Dict[str, Any]:
        """Generate fallback audio when TTS API is unavailable"""
        try:
            audio_id = str(uuid.uuid4())
            audio_filename = f"{audio_id}.wav"
            audio_path = self.audio_dir / audio_filename
            
            # Create mock audio file
            await self._generate_mock_audio(hakka_text, audio_path)
            
            duration = max(10, len(hakka_text) * 0.5)
            
            return {
                "audio_id": audio_id,
                "audio_path": str(audio_path),
                "audio_url": f"/static/audio/{audio_filename}",
                "duration": int(duration),
                "text": hakka_text,
                "romanization": romanization,
                "voice_model": "fallback"
            }
            
        except Exception as e:
            logger.error(f"Fallback TTS generation failed: {e}")
            return {
                "audio_id": None,
                "audio_path": None,
                "audio_url": None,
                "duration": 0,
                "text": hakka_text,
                "romanization": romanization,
                "error": str(e)
            }
    
    async def _generate_mock_audio(self, text: str, output_path: Path):
        """
        Generate mock audio file for demo purposes
        In production, replace with actual Hakka TTS API call
        """
        # Create a simple mock audio file (silence)
        # In production, this would call actual TTS service
        
        # For now, create an empty file to represent the audio
        with open(output_path, 'wb') as f:
            # Write minimal WAV header for a silent audio file
            f.write(self._create_silent_wav(duration_seconds=60))
    
    def _create_silent_wav(self, duration_seconds: int = 60, sample_rate: int = 44100) -> bytes:
        """Create a silent WAV file"""
        import struct
        
        # Calculate the number of samples
        num_samples = duration_seconds * sample_rate
        
        # WAV header
        header = struct.pack('<4sI4s', b'RIFF', 36 + num_samples * 2, b'WAVE')
        
        # Format chunk
        fmt_chunk = struct.pack('<4sIHHIIHH', 
                               b'fmt ', 16, 1, 1, sample_rate, 
                               sample_rate * 2, 2, 16)
        
        # Data chunk header
        data_header = struct.pack('<4sI', b'data', num_samples * 2)
        
        # Silent audio data (all zeros)
        audio_data = b'\x00' * (num_samples * 2)
        
        return header + fmt_chunk + data_header + audio_data
    
    async def get_audio_info(self, audio_id: str) -> Optional[Dict[str, Any]]:
        """Get information about generated audio"""
        audio_path = self.audio_dir / f"{audio_id}.wav"
        
        if not audio_path.exists():
            return None
            
        return {
            "audio_id": audio_id,
            "audio_path": str(audio_path),
            "audio_url": f"/static/audio/{audio_id}.wav",
            "exists": True
        }
    
    async def delete_audio(self, audio_id: str) -> bool:
        """Delete generated audio file"""
        try:
            audio_path = self.audio_dir / f"{audio_id}.wav"
            if audio_path.exists():
                audio_path.unlink()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete audio {audio_id}: {e}")
            return False
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()