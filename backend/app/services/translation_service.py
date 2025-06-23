import httpx
import logging
from typing import Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class TranslationService:
    """Service for translating Traditional Chinese to Hakka using Hakka AI Hackathon API"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0, verify=False)  # SSL verification disabled
        self.base_url = settings.HAKKA_TRANSLATE_API_URL
        self.username = settings.HAKKA_USERNAME
        self.password = settings.HAKKA_PASSWORD
        self.token = None
        self.headers = None
    
    async def login(self):
        """Authenticate and obtain bearer token for API requests"""
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
                    logger.info("Successfully authenticated with Hakka translation API")
                    return True
                    
        except Exception as e:
            logger.error(f"Login failed: {e}")
            
        return False
    
    async def translate_chinese_to_hakka(self, chinese_text: str) -> Dict[str, Any]:
        """
        Translate Traditional Chinese text to Hakka using Hakka AI API
        
        Args:
            chinese_text: Traditional Chinese text to translate
            
        Returns:
            Dict containing hakka_text and romanization
        """
        try:
            # Ensure we're authenticated
            if not self.headers:
                await self.login()
            
            if not self.headers:
                logger.warning("Authentication failed, using fallback translation")
                return self._get_fallback_translation(chinese_text)
            
            # Call the translation API
            payload = {'input': chinese_text}
            
            response = await self.client.post(
                f'{self.base_url}/MT/translate/hakka_zh_hk',
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract translation result based on API response format
                hakka_text = result.get('output', chinese_text)  # Adjust key based on actual API
                
                return {
                    "hakka_text": hakka_text,
                    "romanization": self._generate_romanization(hakka_text),
                    "original_chinese": chinese_text
                }
            else:
                logger.error(f"Translation API error: {response.status_code}")
                return self._get_fallback_translation(chinese_text)
                
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return self._get_fallback_translation(chinese_text)
    
    def _get_fallback_translation(self, chinese_text: str) -> Dict[str, Any]:
        """Fallback translation when API is unavailable"""
        hakka_text = self._mock_translate_to_hakka(chinese_text)
        return {
            "hakka_text": hakka_text,
            "romanization": self._generate_romanization(hakka_text),
            "original_chinese": chinese_text
        }
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()