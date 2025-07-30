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
    
    def _clean_hakka_text(self, text: str, preserve_romanization: bool = False) -> str:
        """清理客語文本中的特殊字符
        
        Args:
            text: 要清理的文本
            preserve_romanization: 是否保留羅馬拼音（英文字母）
        """
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
        
        import re
        
        # 移除羅馬拼音標調符號 (¹²³⁴⁵⁶⁷⁸⁰)
        cleaned_text = re.sub(r'[¹²³⁴⁵⁶⁷⁸⁰]', '', cleaned_text)
        
        # 替換常見的英文詞彙和主持人名稱
        english_replacements = {
            '主持人A': '主持人佳昀',
            '主持人 A': '主持人佳昀',
            'A': '佳昀',
            '主持人B': '主持人敏權',
            '主持人 B': '主持人敏權', 
            'B': '敏權',
            'AI': '人工智慧',
            'NHS': '英國國民健保',
            'Hakkast': '哈客播',
            'TTS': '語音合成',
        }
        
        # 只有在不保留羅馬拼音時才進行英文替換和移除
        if not preserve_romanization:
            for eng, chi in english_replacements.items():
                cleaned_text = cleaned_text.replace(eng, chi)
            
            # 移除羅馬拼音字母和數字
            # 這會移除所有英文字母，包括羅馬拼音
            cleaned_text = re.sub(r'[a-zA-Z0-9]+', '', cleaned_text)
            
            # 只保留中文字符、常見標點符號
            cleaned_text = re.sub(r'[^\u4e00-\u9fff，。？！；：「」『』（）]', '', cleaned_text)
        else:
            # 保留羅馬拼音時，只移除數字和特殊符號，保留英文字母
            # 清理多餘的空格和標點
            cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # 保留單個空格
        
        # 清理多餘的空格
        if not preserve_romanization:
            cleaned_text = re.sub(r'\s+', '', cleaned_text)  # 移除所有空格
        
        cleaned_text = cleaned_text.replace('  ', ' ')    # 移除多餘空格
        cleaned_text = cleaned_text.strip()
        
        # 限制文本長度，避免TTS API超時
        if len(cleaned_text) > 150:
            cleaned_text = cleaned_text[:150] + "..."
            logger.warning(f"Text truncated to 150 chars to avoid TTS timeout")
        
        return cleaned_text

    def _clean_romanization(self, romanization: str) -> str:
        """清理羅馬拼音，使其更適合TTS API"""
        import re
        
        cleaned = romanization.strip()
        
        # 替換英文單詞為客語音近似詞
        english_to_hakka_replacements = {
            'Hakkast': 'ha24 ka24 su24',  # 哈客蘇 (音近似)
            'NHS': 'en24 xi24 si24',      # 恩西斯
            'AI': 'a24 i24',              # 阿伊  
            'IT': 'ai24 ti24',            # 愛帝
        }
        
        for eng, hakka_approx in english_to_hakka_replacements.items():
            if eng in cleaned:
                cleaned = cleaned.replace(eng, hakka_approx)
                logger.info(f"Replaced English word: '{eng}' -> '{hakka_approx}'")
        
        # 檢查是否所有單詞都有數字聲調，如果沒有就添加默認聲調
        words = cleaned.split()
        processed_words = []
        
        for word in words:
            # 移除標點符號來檢查核心單詞
            punctuation = re.findall(r'[^\w]', word)  # 保存標點符號
            clean_word = re.sub(r'[^\w]', '', word)   # 移除標點符號
            
            if clean_word:
                # 檢查單詞是否已經有數字聲調
                if not re.search(r'\d', clean_word):
                    # 如果沒有數字，添加默認聲調24
                    new_clean_word = clean_word + '24'
                    # 重新組合單詞和標點符號
                    if punctuation:
                        processed_word = word.replace(clean_word, new_clean_word)
                    else:
                        processed_word = new_clean_word
                    processed_words.append(processed_word)
                    logger.info(f"Added default tone to word: '{word}' -> '{processed_word}'")
                else:
                    # 已經有數字聲調，保持原樣
                    processed_words.append(word)
            else:
                # 空單詞或只有標點符號，保持原樣
                processed_words.append(word)
        
        cleaned = ' '.join(processed_words)
        
        # 清理多餘的空格
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # 限制長度，避免TTS超時
        if len(cleaned) > 120:
            cleaned = cleaned[:120].strip()
            logger.warning(f"Romanization truncated to 120 chars to avoid TTS timeout")
        
        logger.info(f"Romanization cleaning: '{romanization}' -> '{cleaned}'")
        return cleaned

    def _generate_readable_filename(self, text: str, speaker: str = "", index: int = None, script_name: str = "", segment_index: int = None) -> str:
        """生成可讀性好的音檔檔名
        
        Args:
            text: 要合成的文本
            speaker: 說話者ID
            index: 全局索引（棄用，改用segment_index）
            script_name: 腳本名稱（用於識別同一個腳本）
            segment_index: 段落索引（同一腳本內的序號）
        """
        import re
        from datetime import datetime
        
        # 如果沒有提供腳本名稱，嘗試從文本推斷
        if not script_name:
            if "科技新聞" in text or "technology" in text.lower():
                script_name = "tech_news"
            elif "播客" in text or "podcast" in text.lower():
                script_name = "podcast"
            else:
                script_name = "hakka_audio"
        
        # 清理腳本名稱，只保留英文數字和底線
        clean_script_name = re.sub(r'[^\w]', '_', script_name)
        
        # 說話者簡寫
        speaker_short = ""
        if speaker:
            if "F01" in speaker:
                speaker_short = "SXF"  # 四縣女聲
            elif "M01" in speaker:
                speaker_short = "SXM"  # 四縣男聲
            elif "hoi" in speaker.lower() and "F" in speaker:
                speaker_short = "HLF"  # 海陸女聲
            elif "hoi" in speaker.lower() and "M" in speaker:
                speaker_short = "HLM"  # 海陸男聲
            elif "thai" in speaker.lower():
                speaker_short = "TPF"  # 大埔女聲
            else:
                speaker_short = "UNK"  # 未知說話者
        
        # 生成序號：腳本序號_段落序號
        if segment_index is not None:
            sequence_str = f"{segment_index:03d}"
        elif index is not None:
            sequence_str = f"{index:03d}"
        else:
            sequence_str = "000"
        
        # 生成檔名：腳本名_說話者_序號.wav
        # 例如：tech_news_SXF_001.wav
        filename = f"{clean_script_name}_{speaker_short}_{sequence_str}.wav"
        
        return filename

    async def generate_hakka_audio(self, hakka_text: str, romanization: str = "", speaker: str = "", segment_index: int = None, script_name: str = "") -> Dict[str, Any]:
        """
        Generate audio from Hakka text using Hakka AI TTS service
        
        Args:
            hakka_text: Hakka text to convert to speech
            romanization: Optional romanization for pronunciation guidance  
            speaker: Speaker ID for filename generation
            segment_index: Segment index within the script for filename ordering
            script_name: Script name for grouping related audio files
            
        Returns:
            Dict containing audio file path and metadata
        """
        try:
            # Ensure we're authenticated
            if not self.headers:
                await self.login()
            
            if not self.headers:
                logger.warning("TTS Authentication failed, using fallback")
                return await self._generate_fallback_audio(hakka_text, romanization, speaker, segment_index, script_name)
            
            # 優先使用羅馬拼音，因為客語TTS引擎對羅馬拼音支持更好
            if romanization and romanization.strip():
                # 清理和預處理羅馬拼音
                cleaned_text = self._clean_romanization(romanization)
                logger.info(f"Using cleaned romanization for TTS: {cleaned_text}")
                logger.info(f"Original romanization: {romanization}")
                logger.info(f"Original hakka text: {hakka_text}")
            else:
                # 如果沒有羅馬拼音，使用原始客語文本，但不進行過度清理
                cleaned_text = hakka_text
                logger.info(f"No romanization provided, using hakka text: {cleaned_text}")
            
            # 生成可讀性好的檔名
            audio_filename = self._generate_readable_filename(hakka_text, speaker, segment_index, script_name, segment_index)
            audio_id = audio_filename.replace('.wav', '')  # 用檔名作為 ID
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
                    if isinstance(available_speakers, dict):
                        if 'hak-xi-TW-vs2-F01' in available_speakers:
                            speaker_id = 'hak-xi-TW-vs2-F01'
                            language_id = 'hak-xi-TW'
                        else:
                            speaker_id = list(available_speakers.keys())[0]
                    elif isinstance(available_speakers, list):
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
            
            # 智能選擇 textType - 優先使用羅馬拼音格式
            import re
            
            if romanization and romanization.strip():
                # 如果有羅馬拼音，嘗試使用 roma 格式
                text_type = "roma"
                logger.info(f"Using 'roma' textType for romanization input")
            elif re.search(r'[a-zA-Z]', cleaned_text):
                # 如果文本包含英文字母，可能是羅馬拼音
                text_type = "roma"
                logger.info(f"Text contains romanization, using 'roma' textType")
            elif re.search(r'[\u4e00-\u9fff]', cleaned_text):
                # 包含中文字符，使用 common 格式
                text_type = "common"
                logger.info(f"Text contains Chinese characters, using 'common' textType")
            else:
                # 預設使用 roma 格式
                text_type = "roma"
                logger.info(f"Default to 'roma' textType")
                
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
            
            # Call TTS synthesis API with retry logic for textType
            response = await self.client.post(
                f'{self.base_url}/api/v1/tts/synthesize',
                headers=self.headers,
                json=synthesis_payload
            )
            
            # If roma textType failed, retry with common textType but keep using romanization
            if response.status_code != 200 and text_type == "roma":
                logger.warning(f"TTS with 'roma' textType failed (status {response.status_code}), retrying with 'common' textType but keeping romanization")
                synthesis_payload["input"]["textType"] = "common"
                
                # Keep using the cleaned romanization instead of falling back to hakka_text
                # synthesis_payload["input"]["text"] stays the same (cleaned romanization)
                logger.info(f"Retrying with 'common' textType using romanization: {cleaned_text}")
                
                response = await self.client.post(
                    f'{self.base_url}/api/v1/tts/synthesize',
                    headers=self.headers,
                    json=synthesis_payload
                )
                
                # If romanization with common textType also fails, then try hakka_text
                if response.status_code != 200 and romanization and romanization.strip():
                    logger.warning(f"Romanization with 'common' textType also failed (status {response.status_code}), trying hakka_text as last resort")
                    synthesis_payload["input"]["text"] = hakka_text
                    logger.info(f"Final fallback to hakka text: {hakka_text}")
                    
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
                return await self._generate_fallback_audio(hakka_text, romanization, speaker, segment_index, script_name)
                
        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            return await self._generate_fallback_audio(hakka_text, romanization, speaker, segment_index, script_name)
    
    async def _generate_fallback_audio(self, hakka_text: str, romanization: str = "", speaker: str = "", segment_index: int = None, script_name: str = "") -> Dict[str, Any]:
        """Generate fallback audio when TTS API is unavailable"""
        try:
            # 生成可讀性好的檔名
            audio_filename = self._generate_readable_filename(hakka_text, speaker, segment_index, script_name, segment_index)
            audio_id = audio_filename.replace('.wav', '')  # 用檔名作為 ID
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