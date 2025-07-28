#!/usr/bin/env python3
"""
播客腳本翻譯器
將中文播客腳本翻譯成客語
"""

import asyncio
import sys
import json
import re
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.translation_service import TranslationService
from app.services.tts_service import TTSService

async def translate_podcast_script():
    """翻譯播客腳本"""
    
    print("🎙️ Hakkast 播客腳本翻譯器")
    print("=" * 60)
    
    # 讀取原始腳本
    script_file = Path(__file__).parent / "podcast_script_technology_news_3articles.txt"
    
    if not script_file.exists():
        print(f"❌ 找不到腳本文件: {script_file}")
        return
    
    with open(script_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"📄 讀取腳本文件: {script_file.name}")
    
    # 初始化翻譯服務
    translation_service = TranslationService()
    
    # 解析腳本內容
    lines = content.split('\n')
    translated_lines = []
    dialogue_segments = []
    
    print("\n🔄 開始翻譯...")
    
    dialogue_pattern = r'^(主持人[AB]):\s*(.+)$'
    segment_count = 0
    
    for i, line in enumerate(lines):
        print(f"處理第 {i+1}/{len(lines)} 行", end='\r')
        
        # 檢查是否為對話行
        match = re.match(dialogue_pattern, line.strip())
        
        if match:
            speaker = match.group(1)
            text = match.group(2)
            
            # 翻譯對話內容
            try:
                result = await translation_service.translate_chinese_to_hakka(text)
                
                hakka_text = result['hakka_text']
                romanization = result['romanization']
                
                # 創建翻譯後的行
                translated_line = f"{speaker}: {hakka_text}"
                translated_lines.append(translated_line)
                
                # 保存對話段落資訊
                segment_count += 1
                dialogue_segments.append({
                    "segment_id": segment_count,
                    "speaker": speaker,
                    "original_text": text,
                    "hakka_text": hakka_text,
                    "romanization": romanization,
                    "estimated_duration": result['estimated_speech_duration'],
                    "line_number": i + 1
                })
                
            except Exception as e:
                print(f"\n❌ 翻譯失敗 (第 {i+1} 行): {e}")
                translated_lines.append(line)  # 保留原文
        else:
            # 非對話行直接保留
            translated_lines.append(line)
    
    print(f"\n✅ 翻譯完成！共處理 {segment_count} 段對話")
    
    # 生成翻譯後的腳本文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. 完整客語腳本
    hakka_script_file = Path(__file__).parent / f"podcast_script_hakka_{timestamp}.txt"
    with open(hakka_script_file, 'w', encoding='utf-8') as f:
        f.write("Hakkast 客語播客腳本\n")
        f.write("=" * 60 + "\n\n")
        f.write("翻譯時間: " + datetime.now().strftime("%Y年%m月%d日 %H:%M:%S") + "\n")
        f.write("原始腳本: podcast_script_technology_news_3articles.txt\n\n")
        f.write("=" * 60 + "\n")
        f.write("完整客語對話內容:\n\n")
        f.write('\n'.join(translated_lines))
    
    print(f"💾 客語腳本已保存: {hakka_script_file.name}")
    
    # 2. 詳細對話資訊 (JSON格式)
    dialogue_json_file = Path(__file__).parent / f"podcast_dialogue_hakka_{timestamp}.json"
    with open(dialogue_json_file, 'w', encoding='utf-8') as f:
        json.dump({
            "metadata": {
                "translation_time": datetime.now().isoformat(),
                "original_script": "podcast_script_technology_news_3articles.txt",
                "total_segments": len(dialogue_segments),
                "total_estimated_duration": sum(seg['estimated_duration'] for seg in dialogue_segments)
            },
            "dialogue_segments": dialogue_segments
        }, f, ensure_ascii=False, indent=2)
    
    print(f"💾 對話資訊已保存: {dialogue_json_file.name}")
    
    # 3. 拼音對照表
    romanization_file = Path(__file__).parent / f"podcast_romanization_{timestamp}.txt"
    with open(romanization_file, 'w', encoding='utf-8') as f:
        f.write("Hakkast 播客客語拼音對照表\n")
        f.write("=" * 60 + "\n\n")
        f.write("拼音系統: 四縣腔數字標調法\n")
        f.write("翻譯時間: " + datetime.now().strftime("%Y年%m月%d日 %H:%M:%S") + "\n\n")
        f.write("=" * 60 + "\n\n")
        
        for segment in dialogue_segments:
            f.write(f"【{segment['speaker']}】\n")
            f.write(f"原文: {segment['original_text']}\n")
            f.write(f"客語: {segment['hakka_text']}\n")
            f.write(f"拼音: {segment['romanization']}\n")
            f.write(f"預估語音時長: {segment['estimated_duration']:.1f}秒\n")
            f.write("-" * 40 + "\n\n")
    
    print(f"💾 拼音對照表已保存: {romanization_file.name}")
    
    # 統計資訊
    total_duration = sum(seg['estimated_duration'] for seg in dialogue_segments)
    print(f"\n📊 翻譯統計:")
    print(f"   對話段落: {len(dialogue_segments)} 段")
    print(f"   預估總時長: {total_duration:.1f}秒 ({total_duration/60:.1f}分鐘)")
    print(f"   平均每段時長: {total_duration/len(dialogue_segments):.1f}秒")
    
    # 顯示前幾段翻譯示例
    print(f"\n🎭 翻譯示例 (前5段):")
    for i, segment in enumerate(dialogue_segments[:5], 1):
        print(f"\n{i}. 【{segment['speaker']}】")
        print(f"   原文: {segment['original_text'][:80]}{'...' if len(segment['original_text']) > 80 else ''}")
        print(f"   客語: {segment['hakka_text'][:80]}{'...' if len(segment['hakka_text']) > 80 else ''}")
    
    await translation_service.close()
    
    return {
        "hakka_script_file": hakka_script_file,
        "dialogue_json_file": dialogue_json_file,
        "romanization_file": romanization_file,
        "total_segments": len(dialogue_segments),
        "total_duration": total_duration
    }

async def create_tts_ready_segments():
    """創建適合TTS的分段文件"""
    
    print("\n🎤 創建TTS就緒分段...")
    
    # 查找最新的對話JSON文件
    json_files = list(Path(__file__).parent.glob("podcast_dialogue_hakka_*.json"))
    if not json_files:
        print("❌ 找不到對話JSON文件")
        return
    
    latest_json = sorted(json_files)[-1]
    
    with open(latest_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    dialogue_segments = data['dialogue_segments']
    
    # 創建TTS分段文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tts_file = Path(__file__).parent / f"tts_segments_{timestamp}.json"
    
    tts_segments = []
    for segment in dialogue_segments:
        tts_segments.append({
            "id": f"seg_{segment['segment_id']:03d}",
            "speaker": segment['speaker'],
            "text": segment['hakka_text'],
            "romanization": segment['romanization'],
            "duration": segment['estimated_duration'],
            "voice_settings": {
                "language": "hakka",
                "dialect": "sixian",
                "speed": "normal",
                "pitch": "natural"
            }
        })
    
    tts_data = {
        "podcast_info": {
            "title": "Hakkast 科技新聞播客",
            "episode": "3篇科技新聞討論",
            "total_segments": len(tts_segments),
            "estimated_total_duration": sum(seg['duration'] for seg in tts_segments),
            "created_at": datetime.now().isoformat()
        },
        "tts_segments": tts_segments
    }
    
    with open(tts_file, 'w', encoding='utf-8') as f:
        json.dump(tts_data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 TTS分段文件已保存: {tts_file.name}")
    print(f"   總分段數: {len(tts_segments)}")
    print(f"   預估總時長: {tts_data['podcast_info']['estimated_total_duration']:.1f}秒")
    
    return tts_file

async def test_tts_generation():
    """測試TTS生成功能"""
    
    print("\n🎤 開始TTS語音生成測試...")
    
    # 查找最新的對話JSON文件
    json_files = list(Path(__file__).parent.glob("podcast_dialogue_hakka_*.json"))
    if not json_files:
        print("❌ 找不到對話JSON文件，請先運行翻譯功能")
        return
    
    latest_json = sorted(json_files)[-1]
    print(f"📁 使用對話文件: {latest_json.name}")
    
    with open(latest_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    dialogue_segments = data['dialogue_segments']
    
    # 初始化TTS服務
    tts_service = TTSService()
    
    try:
        # 登入TTS服務
        print("🔐 正在登入TTS服務...")
        login_success = await tts_service.login()
        
        if not login_success:
            print("⚠️  TTS服務登入失敗，將使用模擬模式")
        else:
            print("✅ TTS服務登入成功")
        
        # 測試前3段對話
        test_segments = dialogue_segments[:3]  # 只測試前3段
        generated_audio = []
        
        print(f"\n🎵 開始生成語音 (測試 {len(test_segments)} 段)...")
        
        for i, segment in enumerate(test_segments, 1):
            print(f"\n處理第 {i} 段: 【{segment['speaker']}】")
            print(f"客語文本: {segment['hakka_text'][:60]}...")
            
            try:
                # 生成語音
                audio_result = await tts_service.generate_hakka_audio(
                    hakka_text=segment['hakka_text'],
                    romanization=segment['romanization']
                )
                
                if audio_result.get('audio_path'):
                    print(f"✅ 語音生成成功: {audio_result['audio_url']}")
                    print(f"   預估時長: {audio_result['duration']}秒")
                    print(f"   使用模型: {audio_result['voice_model']}")
                    
                    generated_audio.append({
                        **segment,
                        "audio_info": audio_result
                    })
                else:
                    print(f"❌ 語音生成失敗: {audio_result.get('error', '未知錯誤')}")
                    
            except Exception as e:
                print(f"❌ 處理第 {i} 段時發生錯誤: {e}")
        
        # 保存測試結果
        if generated_audio:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            test_result_file = Path(__file__).parent / f"tts_test_result_{timestamp}.json"
            
            test_data = {
                "test_info": {
                    "test_time": datetime.now().isoformat(),
                    "source_file": latest_json.name,
                    "total_tested": len(test_segments),
                    "successful_generated": len(generated_audio),
                    "login_success": login_success
                },
                "generated_audio": generated_audio
            }
            
            with open(test_result_file, 'w', encoding='utf-8') as f:
                json.dump(test_data, f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 測試結果已保存: {test_result_file.name}")
            
            # 顯示生成的音頻文件列表
            print(f"\n🎵 生成的音頻文件:")
            for i, audio in enumerate(generated_audio, 1):
                audio_info = audio['audio_info']
                print(f"   {i}. 【{audio['speaker']}】 - {audio_info['audio_url']}")
                print(f"      文本: {audio['hakka_text'][:40]}...")
                print(f"      時長: {audio_info['duration']}秒")
        
        print(f"\n📊 TTS測試統計:")
        print(f"   測試段落: {len(test_segments)} 段")
        print(f"   成功生成: {len(generated_audio)} 段")
        print(f"   成功率: {len(generated_audio)/len(test_segments)*100:.1f}%")
        
    finally:
        # 登出並關閉服務
        await tts_service.logout()
        await tts_service.close()
        print("🔓 TTS服務已登出")
    
    return generated_audio

async def test_tts_only():
    """僅測試TTS功能（不進行翻譯）"""
    
    print("🎤 TTS獨立測試模式")
    print("=" * 50)
    
    try:
        generated_audio = await test_tts_generation()
        
        if generated_audio:
            print(f"\n🎉 TTS測試完成! 生成了 {len(generated_audio)} 個音頻文件")
            
            # 播放建議
            print(f"\n💡 播放建議:")
            print(f"   1. 音頻文件位於: backend/static/audio/")
            print(f"   2. 可使用瀏覽器訪問: http://localhost:8000/static/audio/[文件名]")
            print(f"   3. 或直接用音頻播放器打開文件")
        else:
            print(f"\n❌ TTS測試失敗，請檢查:")
            print(f"   1. TTS服務配置是否正確")
            print(f"   2. 是否存在翻譯後的對話文件")
            print(f"   3. 網絡連接是否正常")
            
    except Exception as e:
        print(f"❌ TTS測試失敗: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """主要執行函數"""
    
    print("🎙️ Hakkast 播客腳本翻譯與TTS測試系統")
    print("=" * 70)
    
    try:
        # 翻譯播客腳本
        print("第1步: 翻譯播客腳本")
        result = await translate_podcast_script()
        
        if result:
            # 創建TTS就緒文件
            print("\n第2步: 創建TTS分段文件")
            await create_tts_ready_segments()
            
            # 測試TTS語音生成
            print("\n第3步: 測試TTS語音生成")
            generated_audio = await test_tts_generation()
            
            print(f"\n🎉 全部完成！")
            print(f"📁 生成的文件:")
            print(f"   📄 客語腳本: {result['hakka_script_file'].name}")
            print(f"   📋 對話資訊: {result['dialogue_json_file'].name}")
            print(f"   🔤 拼音對照: {result['romanization_file'].name}")
            print(f"   🎤 TTS分段: tts_segments_*.json")
            print(f"   🎵 測試結果: tts_test_result_*.json")
            
            if generated_audio:
                print(f"\n🎵 TTS測試成功! 生成了 {len(generated_audio)} 個音頻文件")
                print("💡 你可以在 static/audio/ 目錄中找到生成的音頻文件")
            else:
                print(f"\n⚠️  TTS測試未生成音頻文件，請檢查TTS服務配置")
            
    except Exception as e:
        print(f"❌ 執行失敗: {e}")
        import traceback
        print("詳細錯誤資訊:")
        traceback.print_exc()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Hakkast 播客腳本翻譯與TTS測試系統")
    parser.add_argument('--tts-only', action='store_true', 
                       help='只運行TTS測試，不進行翻譯')
    
    args = parser.parse_args()
    
    if args.tts_only:
        asyncio.run(test_tts_only())
    else:
        asyncio.run(main())
