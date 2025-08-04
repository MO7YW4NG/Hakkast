import os
import uuid
import logging
from typing import Optional, Dict, Any
import httpx
from pathlib import Path
from app.core.config import settings
import google.genai as genai
from google.genai import types
import wave


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
            'G-Cloud': '政府雲端',
            'VIP': '貴賓',
        }
        
        # 只有在不保留羅馬拼音時才進行英文替換和移除
        if not preserve_romanization:
            for eng, chi in english_replacements.items():
                cleaned_text = cleaned_text.replace(eng, chi)
            
            # 移除羅馬拼音字母和數字
            # 這會移除所有英文字母，包括羅馬拼音
            cleaned_text = re.sub(r'[a-zA-Z0-9]+', '', cleaned_text)
            
            # 只保留中文字符、常見標點符號（包含驚嘆號和問號）
            cleaned_text = re.sub(r'[^\u4e00-\u9fff，。？！；：「」『』（）—\-]', '', cleaned_text)
        else:
            # 保留羅馬拼音時，只移除數字和特殊符號，保留英文字母
            # 清理多餘的空格和標點
            cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # 保留單個空格
        
        # 清理多餘的空格
        if not preserve_romanization:
            cleaned_text = re.sub(r'\s+', '', cleaned_text)  # 移除所有空格
        
        cleaned_text = cleaned_text.replace('  ', ' ')    # 移除多餘空格
        cleaned_text = cleaned_text.strip()
        
        # 調整文本長度限制為300字符，如果文本過長，智能分割而不是截斷
        if len(cleaned_text) > 300:
            # 嘗試在標點符號處分割
            sentences = re.split(r'([。！？])', cleaned_text)
            result = ""
            for i in range(0, len(sentences), 2):
                if i + 1 < len(sentences):
                    sentence = sentences[i] + sentences[i + 1]
                else:
                    sentence = sentences[i]
                
                if len(result + sentence) <= 300:
                    result += sentence
                else:
                    break
            
            if result:
                cleaned_text = result
                logger.info(f"Text intelligently split at sentence boundary: {len(cleaned_text)} chars")
            else:
                # 如果無法智能分割，則截斷
                cleaned_text = cleaned_text[:300]
                logger.warning(f"Text truncated to 300 chars to avoid TTS timeout")
        
        return cleaned_text

    def _clean_romanization(self, romanization: str) -> str:
        """清理羅馬拼音，使其更適合TTS API"""
        import re
        
        cleaned = romanization.strip()
        
        # 移除中文標點符號（這些不應該出現在羅馬拼音中）
        chinese_punctuation = ['「', '」', '『', '』', '（', '）', '【', '】', '〈', '〉', '《', '》']
        for punct in chinese_punctuation:
            cleaned = cleaned.replace(punct, '')
        
        # 移除其他非羅馬拼音字符，只保留英文字母、數字、空格和基本標點
        cleaned = re.sub(r'[^\w\s.,!?-]', '', cleaned)
        
        # 替換英文單詞為客語音近似詞
        english_to_hakka_replacements = {
            'Hakkast': 'ha24 ka24 su24',  # 哈客蘇 (音近似)
            'NHS': 'en24 xi24 si24',      # 恩西斯
            'AI': 'a24 i24',              # 阿伊  
            'IT': 'ai24 ti24',            # 愛帝
            'G-Cloud': 'zi24 kau24',      # 政府雲 (音近似)
            'VIP': 'vi24 ai24 pi24',      # VIP (音譯)
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
        
        # 修正有問題的音節
        cleaned = self._fix_problematic_syllables(cleaned)
        
        logger.info(f"Romanization cleaning: '{romanization[:50]}...' -> '{cleaned[:50]}...'")
        return cleaned

    def _fix_problematic_syllables(self, romanization: str) -> str:
        """修正有問題的音節，提升TTS成功率
        
        Args:
            romanization: 原始羅馬拼音
            
        Returns:
            修正後的羅馬拼音
        """
        # 已知有問題的音節 - 直接跳過這些音節
        problematic_syllables = {
            'sip2', 'ngiet8', 'ket2', 'nain55', 'dap2'
        }
        
        # 英文近似音模式 - 這些通常是人工合成的，TTS模型中沒有
        english_approximation_patterns = {
            'g24-cl24',   # G-Cloud 的近似音
            'ou24',       # Cloud 的近似音
            'd24',        # Cloud 結尾的近似音
            'hiab5',      # 協定的近似音
            'tin55',      # 進化的近似音
            'jin55',      # 進化的近似音
        }
        
        # 英文近似音的修正對應表 - 替換成正確的客語音節
        english_approximation_fixes = {
            'g24-cl24': 'zi24 kau24',     # G-Cloud -> 政府雲
            'ou24': 'iun11',              # Cloud -> 雲
            'd24': '',                    # 移除無意義的尾音
            'hiab5': 'hiab2 tin24',       # 協定 -> 協定
            'tin55': 'jin55',             # 進化 -> 進化（修正音調）
            'jin55': 'fa55',              # 進化 -> 發展（更自然的客語）
        }
        
        words = romanization.split()
        fixed_words = []
        skipped_count = 0
        
        for word in words:
            # 移除標點符號來檢查核心音節
            core_syllable = word.strip('.,!?-')
            
            # 跳過已知有問題的音節
            if core_syllable in problematic_syllables:
                skipped_count += 1
                logger.info(f"Skipped problematic syllable: '{word}' (known TTS failure)")
                continue
            
            # 替換英文近似音節
            if core_syllable in english_approximation_fixes:
                replacement = english_approximation_fixes[core_syllable]
                if replacement:  # 如果有替換值
                    fixed_words.extend(replacement.split())
                    logger.info(f"Replaced English approximation: '{word}' -> '{replacement}'")
                else:  # 如果替換值為空，表示跳過
                    skipped_count += 1
                    logger.info(f"Removed meaningless syllable: '{word}'")
                continue
            
            # 檢查包含英文近似音模式的複合音節並替換
            found_pattern = False
            for pattern in english_approximation_patterns:
                if pattern in core_syllable and pattern in english_approximation_fixes:
                    replacement = english_approximation_fixes[pattern]
                    if replacement:
                        # 替換模式部分
                        new_syllable = core_syllable.replace(pattern, replacement)
                        fixed_words.extend(new_syllable.split())
                        logger.info(f"Replaced compound approximation: '{word}' -> '{new_syllable}'")
                    else:
                        skipped_count += 1
                        logger.info(f"Removed compound with meaningless pattern: '{word}'")
                    found_pattern = True
                    break
            
            if not found_pattern:
                fixed_words.append(word)
        
        fixed_romanization = ' '.join(fixed_words)
        
        if skipped_count > 0 or len(fixed_words) != len(words):
            logger.info(f"Applied fixes: {skipped_count} syllables removed, {len(fixed_words) - len(words) + skipped_count} syllables replaced/added")
            logger.info(f"Original: {len(words)} syllables -> Fixed: {len(fixed_words)} syllables")
            logger.info("Applied English approximation replacements and removed problematic syllables")
        
        return fixed_romanization

    def _split_romanization(self, romanization: str, max_length: int = 150, max_syllables: int = 8) -> list[str]:
        """將羅馬拼音分割成多個不超過指定長度和音節數的片段
        
        Args:
            romanization: 要分割的羅馬拼音
            max_length: 每個片段的最大字符長度（備用限制）
            max_syllables: 每個片段的最大音節數（主要限制）
            
        Returns:
            羅馬拼音片段列表
        """
        words = romanization.split()
        
        # 如果音節數不超過限制，直接返回
        if len(words) <= max_syllables and len(romanization) <= max_length:
            return [romanization]
        
        segments = []
        current_segment = []
        current_length = 0
        
        for word in words:
            # 計算添加這個單詞後的長度和音節數
            word_length = len(word) + (1 if current_segment else 0)
            new_syllable_count = len(current_segment) + 1
            
            # 檢查是否超過音節數限制或字符數限制
            if (new_syllable_count <= max_syllables and 
                current_length + word_length <= max_length):
                current_segment.append(word)
                current_length += word_length
            else:
                # 如果當前片段不為空，保存它
                if current_segment:
                    segments.append(' '.join(current_segment))
                
                # 開始新的片段
                current_segment = [word]
                current_length = len(word)
        
        # 保存最後一個片段
        if current_segment:
            segments.append(' '.join(current_segment))
        
        logger.info(f"Romanization split into {len(segments)} segments by syllables (max {max_syllables})")
        logger.info(f"Segment syllable counts: {[len(s.split()) for s in segments]}")
        logger.info(f"Segment character counts: {[len(s) for s in segments]}")
        return segments



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
            if speaker in ["SXM", "SXF", "HLM", "HLF", "UNK"]:
                speaker_short = speaker
            elif "xi" in speaker.lower() and ("F01" in speaker or "f" in speaker.lower()):
                speaker_short = "SXF"
            elif "xi" in speaker.lower() and ("M01" in speaker or "m" in speaker.lower()):
                speaker_short = "SXM"
            elif "hoi" in speaker.lower() and ("F01" in speaker or "f" in speaker.lower()):
                speaker_short = "HLF"
            elif "hoi" in speaker.lower() and ("M01" in speaker or "m" in speaker.lower()):
                speaker_short = "HLM"
            elif "thai" in speaker.lower():
                speaker_short = "TPF"
            else:
                if "F" in speaker.upper():
                    speaker_short = "F"
                elif "M" in speaker.upper():
                    speaker_short = "M"
                else:
                    speaker_short = "UNK"
        
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
                cleaned_romanization = self._clean_romanization(romanization)
                
                # 檢查是否需要分段處理（按音節數限制）
                romanization_words = cleaned_romanization.split()
                if len(romanization_words) > 8 or len(cleaned_romanization) > 150:
                    logger.info(...)
                    segmented_result = await self._generate_segmented_audio(
                        hakka_text, cleaned_romanization, speaker, segment_index, script_name
                    )

                    # 加入 segment_paths 到回傳
                    if isinstance(segmented_result, dict):
                        segmented_result["segment_paths"] = segmented_result.get("segment_paths", [])

                    return segmented_result
                
                cleaned_text = cleaned_romanization
                text_type = "roma"
                logger.info(f"Using cleaned romanization for TTS: {cleaned_text}")
                logger.info(f"Original romanization: {romanization}")
                logger.info(f"Corresponding hakka text: {hakka_text}")
            else:
                # 如果沒有羅馬拼音，使用客語文本並進行清理分割
                cleaned_text = self._clean_hakka_text(hakka_text)
                text_type = "common"
                logger.info(f"No romanization provided, using cleaned hakka text: {cleaned_text}")
            
            # 生成可讀性好的檔名
            audio_filename = self._generate_readable_filename(hakka_text, speaker, None, script_name, segment_index)
            audio_id = audio_filename.replace('.wav', '')  # 用檔名作為 ID
            audio_path = self.audio_dir / audio_filename
            
            # Get available models
            models = await self.get_models()
            voice_model = "broncitts"  # default model name
            
            # 使用傳入的 speaker 參數，如果沒有則使用默認值
            if speaker and speaker.strip():
                speaker_id = speaker.strip()
                logger.info(f"Using provided speaker: {speaker_id}")
            else:
                speaker_id = "hak-xi-TW-vs2-F01"  # 默認四縣女聲
                logger.info(f"No speaker provided, using default: {speaker_id}")
            
            # 根據 speaker_id 推斷 language_id
            if 'hoi' in speaker_id.lower():
                language_id = 'hak-hoi-TW'  # 海陸腔
            elif 'thai' in speaker_id.lower():
                language_id = 'hak-thai-TW'  # 大埔腔
            else:
                language_id = 'hak-xi-TW'   # 四縣腔
            
            if models and 'data' in models:
                # Use the first available model data
                model_data = models['data'][0]
                voice_model = model_data.get('name', 'broncitts')
                
                # 驗證 speaker_id 是否在可用的說話者列表中
                if 'spk2id' in model_data and model_data['spk2id']:
                    available_speakers = model_data['spk2id']
                    
                    # 檢查指定的 speaker_id 是否可用
                    speaker_available = False
                    if isinstance(available_speakers, dict):
                        speaker_available = speaker_id in available_speakers
                    elif isinstance(available_speakers, list):
                        speaker_available = speaker_id in available_speakers
                    
                    if not speaker_available:
                        logger.warning(f"Requested speaker '{speaker_id}' not available in model.")
                        logger.info(f"Available speakers: {available_speakers}")
                        
                        # 如果指定的說話者不可用，嘗試找到同腔調的替代者
                        fallback_speaker = None
                        if isinstance(available_speakers, dict):
                            for available_speaker in available_speakers.keys():
                                if 'hoi' in speaker_id.lower() and 'hoi' in available_speaker.lower():
                                    fallback_speaker = available_speaker
                                    break
                                elif 'xi' in speaker_id.lower() and 'xi' in available_speaker.lower():
                                    fallback_speaker = available_speaker
                                    break
                            
                            if not fallback_speaker:
                                fallback_speaker = list(available_speakers.keys())[0]
                        elif isinstance(available_speakers, list):
                            for available_speaker in available_speakers:
                                if 'hoi' in speaker_id.lower() and 'hoi' in available_speaker.lower():
                                    fallback_speaker = available_speaker
                                    break
                                elif 'xi' in speaker_id.lower() and 'xi' in available_speaker.lower():
                                    fallback_speaker = available_speaker
                                    break
                            
                            if not fallback_speaker:
                                fallback_speaker = available_speakers[0]
                        
                        if fallback_speaker:
                            logger.info(f"Using fallback speaker: {fallback_speaker}")
                            speaker_id = fallback_speaker
                            
                            # 重新推斷 language_id
                            if 'hoi' in speaker_id.lower():
                                language_id = 'hak-hoi-TW'
                            elif 'thai' in speaker_id.lower():
                                language_id = 'hak-thai-TW'
                            else:
                                language_id = 'hak-xi-TW'
            
            # textType 已經在前面的邏輯中設定
            logger.info(f"Using textType: {text_type}")
                
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
    
    async def _generate_segmented_audio(self, hakka_text: str, romanization: str, speaker: str = "", segment_index: int = None, script_name: str = "") -> Dict[str, Any]:
        """處理長羅馬拼音的分段音檔生成和合併"""
        try:
            # 分割羅馬拼音（使用音節數限制）
            romanization_segments = self._split_romanization(romanization, max_length=150, max_syllables=8)
            logger.info(f"Processing {len(romanization_segments)} romanization segments")
            
            # 生成最終音檔檔名
            final_audio_filename = self._generate_readable_filename(hakka_text, speaker, None, script_name, segment_index)
            final_audio_path = self.audio_dir / final_audio_filename
            final_audio_id = final_audio_filename.replace('.wav', '')
            
            # 為每個片段生成臨時音檔
            temp_audio_paths = []
            successful_segments = 0
            
            for i, segment_romanization in enumerate(romanization_segments):
                # 生成臨時檔名
                temp_filename = f"temp_{final_audio_id}_{i:03d}.wav"
                temp_audio_path = self.audio_dir / temp_filename
                
                logger.info(f"Generating segment {i+1}/{len(romanization_segments)}: {len(segment_romanization)} chars")
                
                # 使用單個片段生成音檔
                segment_result = await self._generate_single_segment_audio(
                    segment_romanization, 
                    str(temp_audio_path), 
                    speaker
                )
                
                if segment_result:
                    temp_audio_paths.append(str(temp_audio_path))
                    successful_segments += 1
                    logger.info(f"Segment {i+1} generated successfully: {temp_audio_path}")
                    
                    # 驗證生成的音檔
                    if os.path.exists(temp_audio_path):
                        file_size = os.path.getsize(temp_audio_path)
                        logger.info(f"Segment file size: {file_size} bytes")
                        if file_size == 0:
                            logger.warning(f"Segment {i+1} generated empty file")
                    else:
                        logger.error(f"Segment {i+1} file not found: {temp_audio_path}")
                else:
                    logger.warning(f"Segment {i+1} generation failed")
            
            if successful_segments == 0:
                logger.error("All segments failed to generate, using fallback")
                return await self._generate_fallback_audio(hakka_text, romanization, speaker, segment_index, script_name)
            
            # 合併所有音檔
            if len(temp_audio_paths) == 1:
                # 只有一個片段，直接重命名
                import shutil
                try:
                    shutil.move(temp_audio_paths[0], str(final_audio_path))
                    logger.info("Single segment, renamed to final audio file")
                    merge_success = True
                except Exception as e:
                    logger.error(f"Failed to rename single segment: {e}")
                    merge_success = False
            else:
                # 多個片段，需要合併
                logger.info(f"Merging {len(temp_audio_paths)} segments into {final_audio_path}")
                merge_success = await self._merge_audio_files(temp_audio_paths, str(final_audio_path))
            
            if not merge_success:
                logger.error("Audio merging failed, using fallback")
                return await self._generate_fallback_audio(hakka_text, romanization, speaker, segment_index, script_name)
            
            # 驗證最終音檔
            if not os.path.exists(final_audio_path) or os.path.getsize(final_audio_path) == 0:
                logger.error(f"Final audio file validation failed: {final_audio_path}")
                return await self._generate_fallback_audio(hakka_text, romanization, speaker, segment_index, script_name)
            
            # 清理臨時檔案
            for temp_path in temp_audio_paths:
                try:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                        logger.debug(f"Cleaned up temp file: {temp_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temp file {temp_path}: {e}")
            
            # 計算時長
            duration = max(10, len(hakka_text) * 0.5)
            
            logger.info(f"Segmented TTS generation successful: {final_audio_filename} ({successful_segments}/{len(romanization_segments)} segments)")
            
            return {
                "audio_id": final_audio_id,
                "audio_path": str(final_audio_path),
                "audio_url": f"/static/audio/{final_audio_filename}",
                "duration": int(duration),
                "text": hakka_text,
                "romanization": romanization,
                "voice_model": f"broncitts/{speaker}",
                "segments_count": successful_segments,
                "total_segments": len(romanization_segments),
                "segment_paths": []  # 已清理，回傳空列表
            }
            
        except Exception as e:
            logger.error(f"Segmented TTS generation failed: {e}")
            return await self._generate_fallback_audio(hakka_text, romanization, speaker, segment_index, script_name)

    async def _merge_audio_files(self, audio_paths, output_path):
        """合併音檔並回傳是否成功"""
        import wave
        try:
            data = []
            params = None
            
            # 檢查所有音檔是否存在
            valid_paths = []
            for path in audio_paths:
                if not os.path.exists(path):
                    logger.warning(f"Audio file not found: {path}")
                    continue
                valid_paths.append(path)
            
            if not valid_paths:
                logger.error("沒有可合併的音檔")
                return False
            
            # 讀取並合併音檔
            for path in valid_paths:
                try:
                    with wave.open(path, 'rb') as wf:
                        if params is None:
                            params = wf.getparams()
                            logger.info(f"音檔參數: {params}")
                        
                        # 檢查音檔參數是否一致
                        current_params = wf.getparams()
                        if (current_params.nchannels != params.nchannels or 
                            current_params.sampwidth != params.sampwidth or 
                            current_params.framerate != params.framerate):
                            logger.warning(f"音檔參數不一致: {path}")
                            logger.warning(f"預期: {params}")
                            logger.warning(f"實際: {current_params}")
                        
                        frame_data = wf.readframes(wf.getnframes())
                        data.append(frame_data)
                        logger.info(f"成功讀取音檔: {path} ({len(frame_data)} bytes)")
                except Exception as e:
                    logger.error(f"讀取音檔失敗: {path}, 錯誤: {e}")
                    continue
            
            if not data:
                logger.error("沒有成功讀取任何音檔數據")
                return False
            
            # 寫入合併後的音檔
            with wave.open(output_path, 'wb') as out:
                out.setparams(params)
                total_bytes = 0
                for d in data:
                    out.writeframes(d)
                    total_bytes += len(d)
                
                logger.info(f"合併音檔成功: {output_path}")
                logger.info(f"總共寫入 {total_bytes} bytes")
            
            # 驗證輸出檔案
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info(f"合併檔案驗證成功: {output_path} ({os.path.getsize(output_path)} bytes)")
                return True
            else:
                logger.error(f"合併檔案驗證失敗: {output_path}")
                return False
                
        except Exception as e:
            logger.error(f"音檔合併過程發生錯誤: {e}")
            return False

    async def _generate_single_segment_audio(self, romanization: str, output_path: str, speaker: str = "") -> bool:
        """生成單個羅馬拼音片段的音檔
        
        Args:
            romanization: 羅馬拼音片段（已清理且長度<=150）
            output_path: 輸出音檔路徑
            speaker: 說話者ID
            
        Returns:
            是否生成成功
        """
        try:
            # 確保已認證
            if not self.headers:
                await self.login()
            
            if not self.headers:
                logger.error("TTS Authentication failed for segment generation")
                return False
            
            # 取得模型資訊
            models = await self.get_models()
            voice_model = "broncitts"
            
            # 設定說話者
            if speaker and speaker.strip():
                speaker_id = speaker.strip()
            else:
                speaker_id = "hak-xi-TW-vs2-F01"  # 默認四縣女聲
            
            # 推斷 language_id
            if 'hoi' in speaker_id.lower():
                language_id = 'hak-hoi-TW'
            elif 'thai' in speaker_id.lower():
                language_id = 'hak-thai-TW'
            else:
                language_id = 'hak-xi-TW'
            
            if models and 'data' in models:
                model_data = models['data'][0]
                voice_model = model_data.get('name', 'broncitts')
                
                # 驗證說話者
                if 'spk2id' in model_data and model_data['spk2id']:
                    available_speakers = model_data['spk2id']
                    
                    speaker_available = False
                    if isinstance(available_speakers, dict):
                        speaker_available = speaker_id in available_speakers
                    elif isinstance(available_speakers, list):
                        speaker_available = speaker_id in available_speakers
                    
                    if not speaker_available:
                        # 尋找替代說話者
                        fallback_speaker = None
                        if isinstance(available_speakers, dict):
                            for available_speaker in available_speakers.keys():
                                if 'xi' in speaker_id.lower() and 'xi' in available_speaker.lower():
                                    fallback_speaker = available_speaker
                                    break
                            if not fallback_speaker:
                                fallback_speaker = list(available_speakers.keys())[0]
                        elif isinstance(available_speakers, list):
                            for available_speaker in available_speakers:
                                if 'xi' in speaker_id.lower() and 'xi' in available_speaker.lower():
                                    fallback_speaker = available_speaker
                                    break
                            if not fallback_speaker:
                                fallback_speaker = available_speakers[0]
                        
                        if fallback_speaker:
                            speaker_id = fallback_speaker
                            # 重新推斷 language_id
                            if 'hoi' in speaker_id.lower():
                                language_id = 'hak-hoi-TW'
                            elif 'thai' in speaker_id.lower():
                                language_id = 'hak-thai-TW'
                            else:
                                language_id = 'hak-xi-TW'
            
            # 準備 API 請求
            synthesis_payload = {
                "input": {
                    "text": romanization,
                    "textType": "roma"  # 使用羅馬拼音格式
                },
                "voice": {
                    "model": voice_model,
                    "languageCode": language_id,
                    "name": speaker_id
                },
                "audioConfig": {
                    "speakingRate": 1.0
                },
                "outputConfig": {
                    "streamMode": 0,
                    "shortPauseDuration": 150,
                    "longPauseDuration": 300
                }
            }
            
            # 呼叫 TTS API
            response = await self.client.post(
                f'{self.base_url}/api/v1/tts/synthesize',
                headers=self.headers,
                json=synthesis_payload
            )
            
            # 如果 roma 格式失敗，嘗試 common 格式
            if response.status_code != 200:
                logger.warning(f"Roma textType failed for segment, trying common textType")
                synthesis_payload["input"]["textType"] = "common"
                
                response = await self.client.post(
                    f'{self.base_url}/api/v1/tts/synthesize',
                    headers=self.headers,
                    json=synthesis_payload
                )
            
            if response.status_code == 200:
                # 保存音檔
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                
                logger.debug(f"Segment audio saved: {output_path} ({len(response.content)} bytes)")
                return True
            else:
                error_text = "Unknown error"
                try:
                    error_response = response.json()
                    error_text = error_response.get('message', error_response)
                except:
                    error_text = response.text[:200]
                
                logger.error(f"Segment TTS API error {response.status_code}: {error_text}")
                return False
                
        except Exception as e:
            logger.error(f"Single segment generation failed: {e}")
            return False
    
    async def _generate_fallback_audio(self, hakka_text: str, romanization: str = "", speaker: str = "", segment_index: int = None, script_name: str = "") -> Dict[str, Any]:
        """Generate fallback audio when TTS API is unavailable"""
        try:
            # 生成可讀性好的檔名
            audio_filename = self._generate_readable_filename(hakka_text, speaker, None, script_name, segment_index)
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

    #gemini TTS
    async def generate_gemini_tts(self, text: str, output_path: str) -> str:
        api_key = getattr(settings, "GEMINI_API_KEY", None)
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not set in environment or settings")
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name="Despina"
                        )
                    )
                ),
            )
        )
        data = response.candidates[0].content.parts[0].inline_data.data
        print(f"Gemini 回傳音訊長度: {len(data)} bytes")
        # wave 包裝成 WAV 檔案
        self._pcm_to_wav(data, output_path, sample_rate=24000)
        return output_path

    def _pcm_to_wav(self, pcm_data: bytes, wav_path: str, sample_rate: int = 24000):
        import wave
        with wave.open(wav_path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(pcm_data)