#!/usr/bin/env python3
"""
客語播客音檔管理工具
整合了 TTS 生成和音檔合併功能
"""

import json
import asyncio
import sys
import re
import os
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.services.tts_service import TTSService
from app.core.config import settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PodcastAudioManager:
    """客語播客音檔管理器 - 整合 TTS 生成和音檔合併"""
    
    def __init__(self, audio_dir: str = "../static/audio"):
        # 從 app 目錄向上一層到 backend 目錄
        self.audio_dir = Path(__file__).parent.parent / "static" / "audio"
        self.tts_service = TTSService()
        
    def split_text_by_sentences(self, text: str, max_length: int = 50) -> List[str]:
        """將文本按句子分割，每段不超過指定長度"""
        # 按標點符號分句
        sentences = re.split(r'[。！？；]', text)
        
        segments = []
        current_segment = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # 如果當前段落加上新句子不會超過長度限制
            if len(current_segment + sentence) <= max_length:
                current_segment += sentence
                if sentence != sentences[-1]:  # 不是最後一句的話加標點
                    current_segment += "。"
            else:
                # 保存當前段落
                if current_segment:
                    segments.append(current_segment.strip())
                
                # 開始新段落
                current_segment = sentence
                if sentence != sentences[-1]:
                    current_segment += "。"
        
        # 添加最後一段
        if current_segment:
            segments.append(current_segment.strip())
        
        return segments

    def clean_hakka_text(self, text: str) -> str:
        """清理客語文本，替換特殊字符"""
        replacements = {
            '𠊎': '我',
            '𫣆': '會', 
            '个': '的',
            '仰般': '怎樣',
            '毋': '不',
            '仰仔': '怎樣',
            '敢會': '會不會',
            '乜': '也',
            '摎': '和',
            '罅': '夠',
            '吔': '了',
            '當': '很',
            'NHS': '英國國民健保',
            'AI': '人工智慧',
            'IT': '資訊科技',
            'Hakkast': '哈客播',
        }
        
        cleaned_text = text
        for old, new in replacements.items():
            cleaned_text = cleaned_text.replace(old, new)
        
        # 移除或替換英文字母和數字
        cleaned_text = re.sub(r'[a-zA-Z0-9]+', '', cleaned_text)
        cleaned_text = re.sub(r'\s+', '', cleaned_text)
        
        return cleaned_text

    async def generate_podcast_audio(self, script_file: str = None) -> Dict[str, Any]:
        """生成播客的完整音檔"""
        
        # 載入播客腳本檔案 (使用絕對路徑)
        if not script_file:
            script_file = Path(__file__).parent.parent / "json" / "podcast_script_technology_news_3articles.json"
        else:
            script_file = Path(script_file)
        
        script_path = script_file
        
        if not script_path.exists():
            logger.error(f"找不到播客腳本檔案 {script_path}")
            return {'success': False, 'error': f'找不到腳本檔案: {script_path}'}
        
        with open(script_path, 'r', encoding='utf-8') as f:
            podcast_data = json.load(f)
        
        logger.info("=== 客語播客 TTS 音檔生成 ===")
        
        try:
            # 登入
            logger.info("正在登入 TTS API...")
            login_success = await self.tts_service.login()
            if not login_success:
                logger.error("❌ 登入失敗")
                return {'success': False, 'error': '登入失敗'}
            logger.info("✅ 登入成功")
            
            # 處理播客內容
            content = podcast_data.get('content', [])
            logger.info(f"播客共有 {len(content)} 個段落")
            
            all_results = []
            total_duration = 0
            
            for i, segment in enumerate(content, 1):
                speaker = segment.get('speaker', 'Unknown')
                hakka_text = segment.get('hakka_text', '')
                original_text = segment.get('text', '')
                
                logger.info(f"--- 處理段落 {i} ({speaker}) ---")
                
                # 選擇使用客語文本還是原始文本
                test_texts = [
                    {'name': '客語文本', 'text': hakka_text},
                    {'name': '原始中文', 'text': original_text}
                ]
                
                for text_option in test_texts:
                    text_to_process = text_option['text']
                    if not text_to_process.strip():
                        continue
                    
                    logger.info(f"  嘗試 {text_option['name']}...")
                    logger.info(f"  原始長度: {len(text_to_process)} 字")
                    
                    # 清理文本
                    cleaned_text = self.clean_hakka_text(text_to_process)
                    logger.info(f"  清理後: {cleaned_text[:50]}..." if len(cleaned_text) > 50 else f"  清理後: {cleaned_text}")
                    
                    # 分段處理
                    segments = self.split_text_by_sentences(cleaned_text, max_length=40)
                    logger.info(f"  分為 {len(segments)} 段")
                    
                    segment_results = []
                    segment_success = 0
                    
                    for j, segment_text in enumerate(segments, 1):
                        logger.info(f"    段落 {j}/{len(segments)}: {segment_text}")
                        
                        try:
                            result = await self.tts_service.generate_hakka_audio(
                                hakka_text=segment_text,
                                romanization=""
                            )
                            
                            if result.get('audio_id') and result.get('voice_model') != 'fallback':
                                logger.info(f"    ✅ 合成成功 (真實 TTS)")
                                segment_success += 1
                                segment_results.append(result)
                                total_duration += result.get('duration', 0)
                            else:
                                logger.info(f"    ⚠️  使用 Fallback")
                                segment_results.append(result)
                            
                        except Exception as e:
                            logger.error(f"    ❌ 合成失敗: {e}")
                    
                    logger.info(f"  成功率: {segment_success}/{len(segments)} ({segment_success/len(segments)*100:.1f}%)")
                    
                    # 如果這個選項成功率不錯，就使用它
                    if segment_success / len(segments) >= 0.5:  # 至少50%成功
                        all_results.append({
                            'segment_index': i,
                            'speaker': speaker,
                            'text_type': text_option['name'],
                            'segments': segment_results,
                            'success_rate': segment_success / len(segments)
                        })
                        logger.info(f"  ✓ 採用此文本版本")
                        break
                    else:
                        logger.info(f"  ✗ 成功率太低，嘗試下一個選項")
                else:
                    logger.warning(f"  ⚠️  所有文本選項都失敗，跳過此段落")
            
            # 總結結果
            logger.info(f"\n=== 播客音檔生成結果 ===")
            logger.info(f"總段落數: {len(content)}")
            logger.info(f"成功處理: {len(all_results)}")
            logger.info(f"預估總時長: {total_duration:.1f} 秒 ({total_duration/60:.1f} 分鐘)")
            
            # 顯示詳細結果
            total_audio_files = 0
            for result in all_results:
                logger.info(f"\n📝 段落 {result['segment_index']} ({result['speaker']}) - {result['text_type']}")
                logger.info(f"   成功率: {result['success_rate']*100:.1f}%")
                logger.info(f"   音檔數: {len(result['segments'])}")
                
                for j, seg in enumerate(result['segments'], 1):
                    if seg.get('audio_id'):
                        logger.info(f"     {j}. {Path(seg['audio_path']).name} ({seg.get('duration', 0)}s)")
                        total_audio_files += 1
            
            logger.info(f"\n✅ 總共生成 {total_audio_files} 個音檔")
            
            # 生成播放列表 (使用絕對路徑)
            playlist_file = Path(__file__).parent.parent / "static" / "audio" / "podcast_playlist.json"
            playlist_data = {
                'title': '客語播客 - 科技新聞',
                'total_duration': total_duration,
                'segments': []
            }
            
            for result in all_results:
                segment_info = {
                    'speaker': result['speaker'],
                    'text_type': result['text_type'],
                    'audio_files': []
                }
                
                for seg in result['segments']:
                    if seg.get('audio_id'):
                        segment_info['audio_files'].append({
                            'file': f"/static/audio/{Path(seg['audio_path']).name}",
                            'duration': seg.get('duration', 0),
                            'text': seg.get('text', '')
                        })
                
                playlist_data['segments'].append(segment_info)
            
            with open(playlist_file, 'w', encoding='utf-8') as f:
                json.dump(playlist_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"📄 播放列表已保存至: {playlist_file}")
            
            # 登出
            await self.tts_service.logout()
            logger.info("✅ 已登出 TTS API")
            
            return {
                'success': True,
                'total_segments': len(content),
                'processed_segments': len(all_results),
                'total_audio_files': total_audio_files,
                'total_duration': total_duration,
                'playlist_file': str(playlist_file),
                'results': all_results
            }
            
        except Exception as e:
            logger.error(f"❌ 處理過程發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
            
        finally:
            await self.tts_service.close()
    
    def get_organized_files(self, script_name: str, speaker: str = "SXF") -> List[Path]:
        """獲取指定腳本的所有音檔，按序號排序"""
        pattern = f"{script_name}_{speaker}_*.wav"
        files = list(self.audio_dir.glob(pattern))
        
        # 按序號排序
        def extract_number(filepath):
            try:
                # 從檔名中提取序號，例如：tech_news_3articles_SXF_101.wav -> 101
                name = filepath.stem
                parts = name.split('_')
                return int(parts[-1])  # 最後一部分是序號
            except (ValueError, IndexError):
                return 0
        
        files.sort(key=extract_number)
        return files
    
    def create_ffmpeg_concat_file(self, files: List[Path], concat_file: Path):
        """創建 FFmpeg 串接檔案列表"""
        with open(concat_file, 'w', encoding='utf-8') as f:
            for file in files:
                # FFmpeg 需要相對路徑或絕對路徑
                abs_path = file.resolve()
                f.write(f"file '{abs_path}'\n")
    
    def merge_audio_files(self, script_name: str, output_filename: str = None, speaker: str = "SXF") -> bool:
        """合併指定腳本的所有音檔"""
        try:
            # 獲取音檔列表
            files = self.get_organized_files(script_name, speaker)
            
            if not files:
                logger.error(f"找不到腳本 '{script_name}' 的音檔")
                return False
            
            logger.info(f"找到 {len(files)} 個音檔要合併")
            
            # 顯示前10個檔案作為預覽
            logger.info("音檔列表（前10個）:")
            for i, file in enumerate(files[:10]):
                logger.info(f"  {i+1:3d}. {file.name}")
            if len(files) > 10:
                logger.info(f"  ... 還有 {len(files) - 10} 個檔案")
            
            # 創建輸出檔名
            if not output_filename:
                output_filename = f"{script_name}_complete_{speaker}.wav"
            
            output_path = self.audio_dir / output_filename
            concat_file = self.audio_dir / f"{script_name}_concat_list.txt"
            
            # 創建 FFmpeg 串接清單
            self.create_ffmpeg_concat_file(files, concat_file)
            
            # 檢查是否安裝了 FFmpeg
            try:
                subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.error("FFmpeg 未安裝。請先安裝 FFmpeg 來合併音檔")
                logger.info("安裝方法：")
                logger.info("1. 下載 FFmpeg: https://ffmpeg.org/download.html")
                logger.info("2. 或使用 Chocolatey: choco install ffmpeg")
                logger.info("3. 或使用 winget: winget install Gyan.FFmpeg")
                return False
            
            # 使用 FFmpeg 合併音檔
            cmd = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', str(concat_file),
                '-c', 'copy',
                '-y',  # 覆蓋輸出檔案
                str(output_path)
            ]
            
            logger.info(f"開始合併音檔...")
            logger.info(f"FFmpeg 命令: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # 清理臨時檔案
                concat_file.unlink(missing_ok=True)
                
                # 檢查輸出檔案
                if output_path.exists():
                    file_size = output_path.stat().st_size
                    logger.info(f"✅ 合併完成！")
                    logger.info(f"📁 輸出檔案: {output_path}")
                    logger.info(f"📊 檔案大小: {file_size / 1024 / 1024:.2f} MB")
                    return True
                else:
                    logger.error("合併完成但找不到輸出檔案")
                    return False
            else:
                logger.error(f"FFmpeg 合併失敗:")
                logger.error(f"stdout: {result.stdout}")
                logger.error(f"stderr: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"合併過程中發生錯誤: {e}")
            return False
    
    def show_script_info(self, script_name: str, speaker: str = "SXF"):
        """顯示腳本的音檔資訊"""
        files = self.get_organized_files(script_name, speaker)
        
        if not files:
            logger.info(f"找不到腳本 '{script_name}' 的音檔")
            return
        
        logger.info(f"\n📋 腳本資訊: {script_name}")
        logger.info(f"🎤 說話者: {speaker}")
        logger.info(f"📁 音檔數量: {len(files)}")
        
        total_size = sum(f.stat().st_size for f in files if f.exists())
        logger.info(f"💾 總大小: {total_size / 1024 / 1024:.2f} MB")
        
        # 顯示序號範圍
        numbers = []
        for file in files:
            try:
                name = file.stem
                parts = name.split('_')
                numbers.append(int(parts[-1]))
            except (ValueError, IndexError):
                pass
        
        if numbers:
            logger.info(f"🔢 序號範圍: {min(numbers)} - {max(numbers)}")
        
        # 顯示檔案列表示例
        logger.info("\n📝 檔案列表示例:")
        for i, file in enumerate(files[:5]):
            size = file.stat().st_size if file.exists() else 0
            logger.info(f"  {file.name} ({size/1024:.1f} KB)")
        
        if len(files) > 5:
            logger.info(f"  ... 還有 {len(files) - 5} 個檔案")

    async def generate_and_merge_podcast(
        self, 
        script_file: str = None, 
        script_name: str = "tech_news_3articles",
        speaker: str = "SXF",
        auto_merge: bool = False
    ) -> Dict[str, Any]:
        """完整的播客製作流程：生成音檔 -> 合併音檔"""
        
        logger.info("=== 開始完整播客製作流程 ===")
        
        # 步驟1: 生成音檔
        logger.info("步驟1: 生成播客音檔...")
        generation_result = await self.generate_podcast_audio(script_file)
        
        if not generation_result.get('success'):
            return generation_result
        
        logger.info(f"✅ 音檔生成完成！共生成 {generation_result['total_audio_files']} 個音檔")
        
        # 步驟2: 顯示音檔資訊
        logger.info("\n步驟2: 檢查生成的音檔...")
        self.show_script_info(script_name, speaker)
        
        # 步驟3: 合併音檔
        should_merge = auto_merge
        if not auto_merge:
            try:
                response = input("\n步驟3: 是否要合併這些音檔成完整播客？(y/N): ").strip().lower()
                should_merge = response in ['y', 'yes', '是']
            except KeyboardInterrupt:
                logger.info("\n操作已取消")
                return {'success': False, 'error': '用戶取消操作'}
        
        if should_merge:
            logger.info("步驟3: 合併音檔...")
            merge_success = self.merge_audio_files(script_name, speaker=speaker)
            
            if merge_success:
                logger.info("🎉 完整播客製作完成！")
                return {
                    'success': True,
                    'generation_result': generation_result,
                    'merge_success': True,
                    'message': '播客製作完成，包括音檔生成和合併'
                }
            else:
                logger.warning("⚠️ 音檔生成成功，但合併失敗")
                return {
                    'success': True,
                    'generation_result': generation_result,
                    'merge_success': False,
                    'message': '音檔生成成功，但合併失敗'
                }
        else:
            logger.info("跳過合併步驟")
            return {
                'success': True,
                'generation_result': generation_result,
                'merge_success': None,
                'message': '僅完成音檔生成，未進行合併'
            }

async def main():
    """主程式"""
    print("客語播客音檔管理工具")
    print("===================")
    
    # 檢查配置
    if not settings.HAKKA_USERNAME or not settings.HAKKA_PASSWORD:
        print("❌ 錯誤：請先設定 HAKKA_USERNAME 和 HAKKA_PASSWORD 環境變數")
        sys.exit(1)
    
    manager = PodcastAudioManager()
    
    try:
        # 選擇操作模式
        print("\n請選擇操作模式：")
        print("1. 僅生成音檔")
        print("2. 僅合併現有音檔")
        print("3. 完整流程（生成 + 合併）")
        print("4. 查看音檔資訊")
        
        try:
            choice = input("\n請輸入選項 (1-4): ").strip()
        except KeyboardInterrupt:
            print("\n操作已取消")
            return
        
        script_name = "tech_news_3articles"
        speaker = "SXF"
        
        if choice == "1":
            # 僅生成音檔
            result = await manager.generate_podcast_audio()
            if result.get('success'):
                print(f"✅ 音檔生成完成！")
            else:
                print(f"❌ 音檔生成失敗: {result.get('error')}")
                
        elif choice == "2":
            # 僅合併音檔
            manager.show_script_info(script_name, speaker)
            try:
                response = input("\n是否要合併這些音檔？(y/N): ").strip().lower()
                if response in ['y', 'yes', '是']:
                    success = manager.merge_audio_files(script_name, speaker=speaker)
                    if success:
                        print("✅ 音檔合併完成！")
                    else:
                        print("❌ 音檔合併失敗")
                else:
                    print("取消合併操作")
            except KeyboardInterrupt:
                print("\n操作已取消")
                
        elif choice == "3":
            # 完整流程
            result = await manager.generate_and_merge_podcast(
                script_name=script_name,
                speaker=speaker,
                auto_merge=False
            )
            if result.get('success'):
                print(f"✅ {result.get('message')}")
            else:
                print(f"❌ 操作失敗: {result.get('error')}")
                
        elif choice == "4":
            # 查看音檔資訊
            manager.show_script_info(script_name, speaker)
            
        else:
            print("無效的選項")
            
    except Exception as e:
        logger.error(f"執行過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())