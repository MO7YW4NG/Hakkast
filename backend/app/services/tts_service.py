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
    
    async def get_text_type_options(self) -> Optional[Dict[str, Any]]:
        """Get available text type options for TTS"""
        try:
            if not self.headers:
                await self.login()
                
            if not self.headers:
                return None
                
            response = await self.client.get(
                f'{self.base_url}/api/v1/tts/synthesize/text-type-options',
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Available text types: {data}")
                return data
                
        except Exception as e:
            logger.error(f"Failed to get text type options: {e}")
            
        return None

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
    
    def _clean_hakka_text(self, text: str) -> str:
        """清理客語文本中的特殊字符"""
        # 常見的客語特殊字符替換
        replacements = {
            '𠊎': '我',      # 我
            '𫣆': '會',      # 會  
            '个': '的',      # 的
            '仰般': '怎樣',   # 怎樣
            '毋': '不',      # 不
            '仰仔': '怎樣',   # 怎樣
            '敢會': '會不會', # 會不會
            '乜': '也',      # 也
            '摎': '和',      # 和
            '罅': '夠',      # 夠
            '吔': '了',      # 了
            '當': '很',      # 很
            '無毋著': '沒錯', # 沒錯
        }
        
        cleaned_text = text
        for old, new in replacements.items():
            cleaned_text = cleaned_text.replace(old, new)
        
        # 移除或替換英文字母和數字，因為TTS API不支援
        import re
        
        # 移除羅馬拼音標調符號 (¹²³⁴⁵⁶⁷⁸⁰)
        cleaned_text = re.sub(r'[¹²³⁴⁵⁶⁷⁸⁰]', '', cleaned_text)
        
        # 替換常見的英文詞彙和主持人名稱
        english_replacements = {
            '主持人A': '主持人佳芸',
            '主持人 A': '主持人佳芸',
            'A': '佳芸',
            '主持人B': '主持人敏權',
            '主持人 B': '主持人敏權', 
            'B': '敏權',
            'AI': '人工智慧',
            'NHS': '英國國民健保',
            'Hakkast': '哈客播',
            'TTS': '語音合成',
        }
        
        for eng, chi in english_replacements.items():
            cleaned_text = cleaned_text.replace(eng, chi)
        
        # 移除羅馬拼音字母和數字
        # 這會移除所有英文字母，包括羅馬拼音
        cleaned_text = re.sub(r'[a-zA-Z0-9]+', '', cleaned_text)
        
        # 清理多餘的空格和標點
        cleaned_text = re.sub(r'\s+', '', cleaned_text)  # 移除所有空格
        cleaned_text = cleaned_text.replace('  ', '')    # 移除多餘空格
        
        # 只保留中文字符、常見標點符號
        cleaned_text = re.sub(r'[^\u4e00-\u9fff，。？！；：「」『』（）]', '', cleaned_text)
        
        # 限制文本長度，避免TTS API超時
        if len(cleaned_text) > 150:
            cleaned_text = cleaned_text[:150] + "..."
            logger.warning(f"Text truncated to 150 chars to avoid TTS timeout")
        
        return cleaned_text

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
            
            # 清理客語文本中的特殊字符
            # cleaned_text = self._clean_hakka_text(hakka_text)  # 暫時停用清理函數
            cleaned_text = hakka_text  # 直接使用原始文本
            logger.info(f"Original text: {hakka_text}")
            logger.info(f"Cleaned text: {cleaned_text}")
            
            # Prepare TTS request
            audio_id = str(uuid.uuid4())
            audio_filename = f"{audio_id}.wav"
            audio_path = self.audio_dir / audio_filename
            
            # Get available models (use first available Hakka model)
            models = await self.get_models()
            voice_model = "broncitts"  # default model name
            speaker_id = "hak-xi-TW-vs2-F01"  # 四縣女聲
            language_id = "hak-xi-TW"  # 四縣
            
            if models and 'data' in models:
                # Use the first available model data
                model_data = models['data'][0]
                voice_model = model_data.get('name', 'broncitts')
                # Use first available speaker (四縣女聲優先)
                if 'spk2id' in model_data and model_data['spk2id']:
                    available_speakers = model_data['spk2id']
                    # 優先選擇四縣女聲
                    if 'hak-xi-TW-vs2-F01' in available_speakers:
                        speaker_id = 'hak-xi-TW-vs2-F01'
                        language_id = 'hak-xi-TW'
                    else:
                        speaker_id = available_speakers[0]
                        # 根據 speaker_id 推斷 language_id
                        if 'hoi' in speaker_id:
                            language_id = 'hak-hoi-TW'
                        elif 'thai' in speaker_id:
                            language_id = 'hak-thai-TW'
                        else:
                            language_id = 'hak-xi-TW'
            
            # 智能選擇 textType
            # 根據測試結果，roma 格式實際不支援，只有 common 和 characters 有效
            text_type = "common"  # 預設使用中文格式
            
            # 檢查文本內容決定使用哪種格式
            import re
            if re.search(r'[a-zA-Z]', cleaned_text):
                # 如果包含英文字母，可能是羅馬拼音，但API不支援
                logger.warning(f"Text contains romanization but API doesn't support 'roma' textType. Using 'common' instead.")
                text_type = "common"
            elif re.search(r'[\u4e00-\u9fff]', cleaned_text):
                # 包含中文字符，使用 common 或 characters
                # characters 和 common 都支援中文，選擇 common
                text_type = "common"
                
            logger.info(f"Selected textType: {text_type}")
            
            # Prepare synthesis payload based on API documentation
            synthesis_payload = {
                "input": {
                    "text": cleaned_text,  # 使用清理後的文本
                    "textType": text_type  # 智能選擇的格式
                },
                "voice": {
                    "model": voice_model,
                    "languageCode": language_id,
                    "name": speaker_id
                },
                "audioConfig": {
                    "speakingRate": 1.0  # 正常語速
                },
                "outputConfig": {
                    "streamMode": 0,  # 檔案模式
                    "shortPauseDuration": 150,  # 短停頓 150ms
                    "longPauseDuration": 300   # 長停頓 300ms
                }
            }
            
            logger.info(f"TTS request payload: {synthesis_payload}")
            
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
                
                logger.info(f"TTS generation successful: {audio_filename}")
                
                return {
                    "audio_id": audio_id,
                    "audio_path": str(audio_path),
                    "audio_url": f"/static/audio/{audio_filename}",
                    "duration": int(duration),
                    "text": hakka_text,
                    "romanization": romanization,
                    "voice_model": f"{voice_model}/{speaker_id}"
                }
            else:
                error_text = "Unknown error"
                try:
                    error_response = response.json()
                    error_text = error_response.get('message', error_response)
                except:
                    error_text = response.text[:200]
                
                logger.error(f"TTS API error {response.status_code}: {error_text}")
                logger.error(f"Request payload was: {synthesis_payload}")
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