from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import json
import re
import subprocess
import asyncio
from app.models.podcast import Podcast, PodcastGenerationRequest, PodcastResponse, PodcastScript, PodcastScriptContent, HostConfig
from app.services.ai_service import AIService
from app.services.tts_service import TTSService
from app.services.translation_service import TranslationService
from app.services.crawl4ai_service import crawl_news

class PodcastAudioManager:
    """Audio file management for podcast generation"""
    
    def __init__(self):
        self.audio_dir = Path("static/audio").resolve()
        self.audio_dir.mkdir(parents=True, exist_ok=True)
    
    def get_organized_files(self, script_name: str, speaker_code: str) -> List[Path]:
        """Get organized audio files for a specific script and speaker"""
        pattern = f"{script_name}_{speaker_code}_*.wav"
        files = list(self.audio_dir.glob(pattern))
        return sorted(files, key=lambda x: self._extract_segment_index(x.name))
    
    def _extract_segment_index(self, filename: str) -> int:
        """Extract segment index from filename"""
        try:
            parts = filename.split('_')
            return int(parts[-1].replace('.wav', ''))
        except (ValueError, IndexError):
            return 9999
    
    def show_script_info(self, script_name: str, speaker_code: str):
        """Show information about audio files for a script"""
        files = self.get_organized_files(script_name, speaker_code)
        if files:
            print(f"  {speaker_code}: {len(files)} 個音檔")
            for f in files[:3]:  # Show first 3 files
                print(f"    - {f.name}")
            if len(files) > 3:
                print(f"    ... (還有 {len(files) - 3} 個)")
    
    def create_ffmpeg_concat_file(self, audio_files: List[Path], concat_file: Path):
        """Create FFmpeg concat file for merging audio"""
        with open(concat_file, 'w', encoding='utf-8') as f:
            for audio_file in audio_files:
                f.write(f"file '{audio_file.absolute()}'\n")
    
    def fix_wav_format(self, input_path: Path, output_path: Path, sample_rate: int = 44100) -> bool:
        """Fix WAV format using FFmpeg for better compatibility"""
        cmd = [
            "ffmpeg", "-y", "-i", str(input_path),
            "-ar", str(sample_rate), "-ac", "1", "-sample_fmt", "s16",
            str(output_path)
        ]
        print(f"執行 ffmpeg：{' '.join(cmd)}")
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if result.returncode != 0:
            print(f"ffmpeg 轉檔失敗：{input_path.name}")
            print(result.stderr.decode("utf-8"))
            return False
        else:
            print(f"ffmpeg 成功轉檔為：{output_path.name}")
            return True

class PodcastService:
    def __init__(self):
        self.ai_service = AIService()
        self.tts_service = TTSService()
        self.translation_service = TranslationService()
        self.audio_manager = PodcastAudioManager()
        self.podcasts_storage: List[Podcast] = []  # In-memory storage for demo
    
    # 說話者配置常量
    SPEAKER_MAPPING = {
        "gemini": {
            "male": "gemini_puck",
            "female": "gemini_zephyr"
        },
        "hakka": {
            "sihxian": {
                "male": "hak-xi-TW-vs2-M01",
                "female": "hak-xi-TW-vs2-F01"
            },
            "hailu": {
                "male": "hak-hoi-TW-vs2-M01", 
                "female": "hak-hoi-TW-vs2-F01"
            }
        }
    }
    
    def _get_hakka_speaker(self, dialect: str, gender: str) -> str:
        """根據腔調和性別獲取客語說話者ID"""
        dialect = dialect.lower() if dialect else "sihxian"
        gender = gender.lower() if gender else "male"
        
        # 獲取指定腔調的說話者映射
        dialect_speakers = self.SPEAKER_MAPPING["hakka"].get(dialect, self.SPEAKER_MAPPING["hakka"]["sihxian"])
        
        # 返回指定性別的說話者，默認使用男性
        return dialect_speakers.get(gender, dialect_speakers["male"])
    
    def _get_gemini_speaker(self, gender: str) -> str:
        """根據性別獲取Gemini說話者ID"""
        gender = gender.lower() if gender else "female"
        return self.SPEAKER_MAPPING["gemini"].get(gender, self.SPEAKER_MAPPING["gemini"]["female"])
    
    def get_speaker_config(self, hosts: List[HostConfig], language: str = "bilingual") -> Dict[str, str]:
        """Get speaker configuration based on host configs and language mode"""
        speaker_map = {}
        for i, host in enumerate(hosts):
            if language == "bilingual":
                # 雙語模式：第一個主持人使用Gemini，其他使用客語TTS
                if i == 0:  # 第一個主持人
                    speaker_map[host.name] = self._get_gemini_speaker(host.gender)
                else:  # 其他主持人
                    speaker_map[host.name] = self._get_hakka_speaker(host.dialect, host.gender)
            else:  # 純客語模式
                # 所有主持人都使用客語TTS
                speaker_map[host.name] = self._get_hakka_speaker(host.dialect, host.gender)
        
        return speaker_map
    
    def get_speaker_code(self, hosts: List[HostConfig]) -> Dict[str, str]:
        """Get speaker codes for audio file naming"""
        speaker_code = {}
        for i, host in enumerate(hosts):
            if i == 0:  # First host
                speaker_code[host.name] = "UNK"
            else:  # Second host
                speaker_code[host.name] = "SXM"
        return speaker_code
    
    async def generate_podcast(self, request: PodcastGenerationRequest, dialect: str = "sihxian") -> Dict[str, Any]:
        """Generate podcast with full audio pipeline including TTS generation"""
        
        # Step 1: Generate podcast script using AI with configurable hosts
        print(f"Generating podcast script with hosts: {[host.name for host in request.hosts]}...")
        result = await self.ai_service.generate_podcast_script_with_agents(
            await crawl_news(request.topic), 
            max_minutes=request.duration,
            hosts=request.hosts
        )
        podcast_script = result["tts_ready_script"]
        
        # Step 2: Add Hakka translation
        print("Adding Hakka translation...")
        podcast_script = await self.add_hakka_translation_to_script(podcast_script, dialect=dialect)
        
        import os
        script_name = f"podcast_{request.topic.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        json_dir = "json"
        os.makedirs(json_dir, exist_ok=True)
        
        filepath = os.path.join(json_dir, script_name)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(podcast_script.model_dump_json(indent=2))
        print(f"腳本已保存至: {filepath}")
        
        # Step 3: Generate audio files
        print("Generating audio files...")
        audio_result = await self.generate_podcast_audio_with_voices(podcast_script, script_name.replace(".json", ""), request.language, request.hosts)
        
        # Create podcast object with audio information
        podcast = Podcast(
            title=podcast_script.title,
            chinese_content="\n".join([item.text for item in podcast_script.content]),
            hakka_content="\n".join([item.hakka_text for item in podcast_script.content if item.hakka_text]),
            romanization="\n".join([item.romanization for item in podcast_script.content if item.romanization]),
            topic=request.topic,
            duration=request.duration,
            language=request.language,
            hosts=request.hosts,
            interests=request.interests,
            audio_url=audio_result.get("final_audio_file"),
            audio_duration=audio_result.get("total_duration")
        )
        
        # Store the podcast
        self.podcasts_storage.append(podcast)
        
        return {
            "podcast": self._to_response(podcast),
            "audio_result": audio_result,
            "script": podcast_script.model_dump()
        }
    
    async def add_hakka_translation_to_script(self, podcast_script: PodcastScript, dialect: str = "sihxian") -> PodcastScript:
        """Add Hakka translation to podcast script content"""
        if not self.translation_service.headers:
            await self.translation_service.login()
        
        for item in podcast_script.content:
            print(f"[Processing] {item.speaker}: {item.text}")
            result = await self.translation_service.translate_chinese_to_hakka(item.text, dialect=dialect)
            item.hakka_text = result.get("hakka_text", "")
            item.romanization = result.get("romanization", "")
            item.romanization_tone = result.get("romanization_tone", "")
        
        await self.translation_service.close()
        return podcast_script
    
    async def generate_podcast_audio_with_voices(self, podcast_script: PodcastScript, script_name: str, language: str = "bilingual", hosts: List[HostConfig] = None) -> Dict[str, Any]:
        """Generate audio files for podcast with TTS based on language setting"""
        
        if not hosts:
            hosts = [
                HostConfig(name="佳昀", gender="female", dialect="sihxian", personality="理性、專業、分析"),
                HostConfig(name="敏權", gender="male", dialect="sihxian", personality="幽默、活潑、互動")
            ]

        print(f"=== Starting audio generation (language: {language}) ===")
        
        try:
            # Login to TTS API for Hakka TTS (needed for both language modes)
            print("Logging into TTS API...")
            login_success = await self.tts_service.login()
            if not login_success:
                print("❌ TTS API login failed, will use fallback mode")
            else:
                print("✅ TTS API login successful")
            
            # Process each dialogue segment
            fixed_audio_paths = []
            total_duration = 0
            successful_segments = 0
            
            # Get speaker configuration and codes based on hosts
            speaker_config = self.get_speaker_config(hosts, language)
            speaker_code = self.get_speaker_code(hosts)
            
            for idx, content_item in enumerate(podcast_script.content):
                speaker_name = content_item.speaker
                hakka_text = content_item.hakka_text
                romanization = content_item.romanization
                original_text = content_item.text
                
                print(f"\n--- Processing segment {idx+1}: {speaker_name} ---")
                print(f"Original: {original_text[:50]}...")
                print(f"Hakka: {hakka_text[:50]}...")
                
                # Generate audio based on language setting and speaker
                if language == "bilingual":
                    # Bilingual mode: Use Gemini for first host, Hakka TTS for second host
                    if speaker_name == hosts[0].name:  # First host (traditionally 佳昀)
                        # Use Gemini TTS for Chinese text
                        print(f"呼叫 Gemini TTS for {speaker_name} (bilingual mode)")
                        try:
                            # Generate filename
                            filename = self.tts_service._generate_readable_filename(
                                original_text, 
                                speaker_code.get(speaker_name, speaker_name), 
                                idx, 
                                script_name, 
                                idx
                            )
                            output_path = self.audio_manager.audio_dir / filename
                            
                            # Get Gemini voice based on gender
                            gemini_voice = speaker_config[speaker_name]
                            
                            # Call Gemini TTS with appropriate voice
                            await self.tts_service.generate_gemini_tts(original_text, str(output_path), gemini_voice)
                            
                            if not output_path.exists() or output_path.stat().st_size == 0:
                                print(f"Gemini 產生的音檔無效：{output_path}")
                                continue
                            
                            # Create fixed version
                            fixed_path = output_path.parent / (output_path.stem + "_fixed.wav")
                            if self.audio_manager.fix_wav_format(output_path, fixed_path):
                                print(f"Gemini 音檔產生成功: {fixed_path}")
                                fixed_audio_paths.append(str(fixed_path))
                                successful_segments += 1
                                
                                # Delete original file, keep only fixed version
                                try:
                                    output_path.unlink()
                                except:
                                    pass
                            else:
                                print(f"Gemini 音檔格式修復失敗")
                                continue
                                
                        except Exception as e:
                            print(f"Gemini 音檔產生失敗: {e}")
                            continue
                    
                    elif speaker_name == hosts[1].name:  # Second host (traditionally 敏權)
                        # Use TWCC TTS for Hakka text
                        speaker_id = speaker_config[speaker_name]
                        print(f"🎤 呼叫 TWCC TTS：speaker_id={speaker_id} (bilingual mode)")
                        try:
                            # Generate Hakka audio
                            result = await self.tts_service.generate_hakka_audio(
                                hakka_text=hakka_text,
                                romanization=romanization,
                                speaker=speaker_id,
                                segment_index=idx,
                                script_name=script_name
                            )
                            
                            if not isinstance(result, dict) or "audio_path" not in result or not result["audio_path"]:
                                print(f"TWCC 回傳格式錯誤：{result}")
                                continue
                            
                            output_path = Path(result["audio_path"])
                            
                            if not output_path.exists() or output_path.stat().st_size == 0:
                                print(f"TWCC 產生的音檔無效：{output_path}")
                                continue
                            
                            # Create fixed version
                            fixed_path = output_path.parent / (output_path.stem + "_fixed.wav")
                            if self.audio_manager.fix_wav_format(output_path, fixed_path):
                                print(f"TWCC 音檔產生成功: {fixed_path}")
                                fixed_audio_paths.append(str(fixed_path))
                                successful_segments += 1
                                
                                # Delete original file, keep only fixed version
                                try:
                                    output_path.unlink()
                                except:
                                    pass
                            else:
                                print(f"TWCC 音檔格式修復失敗")
                                continue
                            
                        except Exception as e:
                            print(f"TWCC 音檔產生失敗: {e}")
                            continue
                
                elif language == "hakka":
                    # Hakka-only mode: Use Hakka TTS for both speakers
                    if speaker_name == hosts[0].name:  # First host
                        # Use Hakka TTS for first host (convert Chinese to Hakka if needed)
                        if not hakka_text.strip():
                            print(f"{speaker_name}第 {idx} 段沒有 hakka_text，跳過")
                            continue
                        
                        speaker_id = speaker_config[speaker_name]
                        print(f"🎤 呼叫 TWCC TTS for {speaker_name}：speaker_id={speaker_id} (hakka-only mode)")
                        try:
                            # Generate Hakka audio for first host
                            result = await self.tts_service.generate_hakka_audio(
                                hakka_text=hakka_text,
                                romanization=romanization,
                                speaker=speaker_id,
                                segment_index=idx,
                                script_name=script_name
                            )
                            
                            if not isinstance(result, dict) or "audio_path" not in result or not result["audio_path"]:
                                print(f"TWCC 回傳格式錯誤：{result}")
                                continue
                            
                            output_path = Path(result["audio_path"])
                            
                            if not output_path.exists() or output_path.stat().st_size == 0:
                                print(f"TWCC 產生的音檔無效：{output_path}")
                                continue
                            
                            # Create fixed version
                            fixed_path = output_path.parent / (output_path.stem + "_fixed.wav")
                            if self.audio_manager.fix_wav_format(output_path, fixed_path):
                                print(f"TWCC 音檔產生成功: {fixed_path}")
                                fixed_audio_paths.append(str(fixed_path))
                                successful_segments += 1
                                
                                # Delete original file, keep only fixed version
                                try:
                                    output_path.unlink()
                                except:
                                    pass
                            else:
                                print(f"TWCC 音檔格式修復失敗")
                                continue
                            
                        except Exception as e:
                            print(f"TWCC 音檔產生失敗: {e}")
                            continue
                    
                    elif speaker_name == hosts[1].name:  # Second host
                        # Use TWCC TTS for second host (same as bilingual mode)
                        speaker_id = speaker_config[speaker_name]
                        print(f"🎤 呼叫 TWCC TTS：speaker_id={speaker_id} (hakka-only mode)")
                        try:
                            # Generate Hakka audio
                            result = await self.tts_service.generate_hakka_audio(
                                hakka_text=hakka_text,
                                romanization=romanization,
                                speaker=speaker_id,
                                segment_index=idx,
                                script_name=script_name
                            )
                            
                            if not isinstance(result, dict) or "audio_path" not in result or not result["audio_path"]:
                                print(f"TWCC 回傳格式錯誤：{result}")
                                continue
                            
                            output_path = Path(result["audio_path"])
                            
                            if not output_path.exists() or output_path.stat().st_size == 0:
                                print(f"TWCC 產生的音檔無效：{output_path}")
                                continue
                            
                            # Create fixed version
                            fixed_path = output_path.parent / (output_path.stem + "_fixed.wav")
                            if self.audio_manager.fix_wav_format(output_path, fixed_path):
                                print(f"TWCC 音檔產生成功: {fixed_path}")
                                fixed_audio_paths.append(str(fixed_path))
                                successful_segments += 1
                                
                                # Delete original file, keep only fixed version
                                try:
                                    output_path.unlink()
                                except:
                                    pass
                            else:
                                print(f"TWCC 音檔格式修復失敗")
                                continue
                            
                        except Exception as e:
                            print(f"TWCC 音檔產生失敗: {e}")
                            continue
                
                else:
                    print(f"未知說話者: {speaker_name}，跳過")
                    continue
            
            # Merge all fixed audio files
            if not fixed_audio_paths:
                print("沒有任何成功產生的音檔，無法合併")
                return {"success": False, "error": "No audio files generated"}
            
            print(f"\n=== 開始合併最終 Podcast ===")
            print(f"共有 {len(fixed_audio_paths)} 個音檔要合併：")
            for i, path in enumerate(fixed_audio_paths):
                file_size = Path(path).stat().st_size if Path(path).exists() else 0
                print(f"  {i+1}. {Path(path).name} ({file_size} bytes)")
            
            # Create merge file list
            filelist_txt = self.audio_manager.audio_dir / "filelist.txt"
            with open(filelist_txt, "w", encoding="utf-8") as f:
                for path in fixed_audio_paths:
                    f.write(f"file '{Path(path).resolve().as_posix()}'\n")
            
            # Execute final merge
            final_path = self.audio_manager.audio_dir / f"{script_name}_final.wav"
            cmd = [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", str(filelist_txt),
                "-ar", "44100", "-ac", "1", "-sample_fmt", "s16",
                str(final_path)
            ]
            
            print(f"執行最終合併：{' '.join(cmd)}")
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            if final_path.exists() and final_path.stat().st_size > 0:
                print(f"✅ Podcast 音檔已產生：{final_path}")
                total_duration = final_path.stat().st_size / (44100 * 2)  # Rough duration estimate
                
                # Clean up temporary files
                try:
                    filelist_txt.unlink()
                except:
                    pass
                
                return {
                    "success": True,
                    "total_audio_files": len(fixed_audio_paths),
                    "total_duration": total_duration,
                    "final_audio_file": str(final_path),
                    "fixed_audio_paths": fixed_audio_paths,
                    "successful_segments": successful_segments,
                    "language_mode": language
                }
            else:
                print("❌ Podcast 最終合併失敗")
                return {"success": False, "error": "Final merge failed"}
            
        except Exception as e:
            print(f"❌ Audio generation process error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
        
        finally:
            await self.tts_service.close()
            print("TTS service closed")
    
    def split_long_text(self, hakka_text: str, romanization: str, max_length: int = 60) -> List[tuple]:
        """Split long text for processing to avoid TTS timeout"""
        if len(hakka_text) <= max_length:
            return [(hakka_text, romanization)]
        
        # Split by punctuation
        sentences = re.split(r'([。！？；，])', hakka_text)
        romanization_sentences = re.split(r'([。！？；，])', romanization) if romanization else [''] * len(sentences)
        
        # Ensure lists have same length
        while len(romanization_sentences) < len(sentences):
            romanization_sentences.append('')
        
        segments = []
        current_hakka = ""
        current_romanization = ""
        
        for i in range(0, len(sentences), 2):
            sentence = sentences[i] if i < len(sentences) else ''
            punctuation = sentences[i + 1] if i + 1 < len(sentences) else ''
            
            rom_sentence = romanization_sentences[i] if i < len(romanization_sentences) else ''
            rom_punctuation = romanization_sentences[i + 1] if i + 1 < len(romanization_sentences) else ''
            
            full_sentence = sentence + punctuation
            full_rom_sentence = rom_sentence + rom_punctuation
            
            if len(current_hakka + full_sentence) <= max_length:
                current_hakka += full_sentence
                current_romanization += full_rom_sentence
            else:
                if current_hakka.strip():
                    segments.append((current_hakka.strip(), current_romanization.strip()))
                
                current_hakka = full_sentence
                current_romanization = full_rom_sentence
        
        if current_hakka.strip():
            segments.append((current_hakka.strip(), current_romanization.strip()))
        
        return segments if segments else [(hakka_text, romanization)]
    
    async def merge_audio_files(self, script_name: str, auto_merge: bool = False) -> Dict[str, Any]:
        """Merge audio files into complete podcast"""
        try:
            # Check for available audio files
            speaker_codes = ["SXF", "SXM", "HLF", "HLM"]
            available_speakers = []
            
            for code in speaker_codes:
                files = self.audio_manager.get_organized_files(script_name, code)
                if files:
                    available_speakers.append((code, len(files)))
                    print(f"Found {code} speaker audio files: {len(files)}")
            
            if not available_speakers:
                return {"success": False, "error": "No audio files found for merging"}
            
            # Collect all audio files sorted by segment index
            all_files = []
            for code, count in available_speakers:
                files = self.audio_manager.get_organized_files(script_name, code)
                for file in files:
                    try:
                        name_parts = file.stem.split('_')
                        segment_index = int(name_parts[-1])
                        all_files.append((segment_index, file))
                    except (ValueError, IndexError):
                        all_files.append((9999, file))
            
            all_files.sort(key=lambda x: x[0])
            sorted_files = [file for _, file in all_files]
            
            print(f"Preparing to merge {len(sorted_files)} audio files...")
            
            # Create merge files
            concat_file = self.audio_manager.audio_dir / f"{script_name}_all_speakers_concat.txt"
            output_file = self.audio_manager.audio_dir / f"{script_name}_complete_all_speakers.wav"
            
            self.audio_manager.create_ffmpeg_concat_file(sorted_files, concat_file)
            
            # Check FFmpeg availability
            try:
                subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                return {"success": False, "error": "FFmpeg not installed"}
            
            # Execute FFmpeg merge
            cmd = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', str(concat_file),
                '-c', 'copy',
                '-y',
                str(output_file)
            ]
            
            print("Executing multi-speaker audio merge...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                concat_file.unlink(missing_ok=True)
                
                if output_file.exists():
                    file_size = output_file.stat().st_size
                    return {
                        "success": True,
                        "output_file": str(output_file),
                        "file_size_mb": file_size / 1024 / 1024,
                        "total_files": len(sorted_files)
                    }
                else:
                    return {"success": False, "error": "Merge completed but output file not found"}
            else:
                return {
                    "success": False, 
                    "error": f"FFmpeg merge failed: {result.stderr}"
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def generate_podcast_from_script_file(self, script_file_path: str, language: str = "bilingual", hosts: List[HostConfig] = []) -> Dict[str, Any]:
        """Generate podcast audio from existing script file"""
        if not hosts:
            hosts = [
                HostConfig(name="佳昀", gender="female", dialect="sihxian", personality="理性、專業、分析"),
                HostConfig(name="敏權", gender="male", dialect="sihxian", personality="幽默、活潑、互動")
            ]
        
        try:
            # Load script file
            with open(script_file_path, 'r', encoding='utf-8') as f:
                script_data = json.load(f)
            
            # Rebuild script object
            segments = []
            for item in script_data['content']:
                segment = PodcastScriptContent(
                    speaker=item['speaker'],
                    text=item['text'],
                    hakka_text=item.get('hakka_text', ''),
                    romanization=item.get('romanization', ''),
                    romanization_tone=item.get('romanization_tone', '')
                )
                segments.append(segment)
            
            podcast_script = PodcastScript(
                title=script_data.get('title', 'Hakka Podcast'),
                hosts=hosts,
                content=segments
            )
            
            # Extract script name
            script_name = Path(script_file_path).stem
            
            # Generate audio
            audio_result = await self.generate_podcast_audio_with_voices(podcast_script, script_name, language, hosts)
            
            return {
                "success": audio_result.get("success", False),
                "script_name": script_name,
                "audio_result": audio_result,
                "script": podcast_script.model_dump()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
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
            duration=podcast.duration,
            language=podcast.language,
            hosts=podcast.hosts,
            interests=podcast.interests,
            createdAt=podcast.created_at.isoformat(),
            audioUrl=podcast.audio_url,
            audioDuration=podcast.audio_duration
        )