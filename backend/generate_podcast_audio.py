#!/usr/bin/env python3
"""
客語播客 TTS 優化腳本
將播客腳本的長文本分段處理，生成完整的音檔
"""

import json
import asyncio
import sys
import re
from pathlib import Path
from app.services.tts_service import TTSService
from app.core.config import settings

def split_text_by_sentences(text: str, max_length: int = 50) -> list:
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

def clean_hakka_text(text: str) -> str:
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

async def generate_podcast_audio():
    """生成播客的完整音檔"""
    
    # 載入播客腳本檔案
    script_file = Path("json/podcast_script_technology_news_3articles.json")
    
    if not script_file.exists():
        print(f"錯誤：找不到播客腳本檔案 {script_file}")
        return
    
    with open(script_file, 'r', encoding='utf-8') as f:
        podcast_data = json.load(f)
    
    print("=== 客語播客 TTS 優化測試 ===")
    
    # 初始化 TTS 服務
    tts_service = TTSService()
    
    try:
        # 登入
        print("正在登入 TTS API...")
        login_success = await tts_service.login()
        if not login_success:
            print("❌ 登入失敗")
            return
        print("✅ 登入成功")
        
        # 處理播客內容
        content = podcast_data.get('content', [])
        print(f"\n播客共有 {len(content)} 個段落")
        
        all_results = []
        total_duration = 0
        
        for i, segment in enumerate(content, 1):
            speaker = segment.get('speaker', 'Unknown')
            hakka_text = segment.get('hakka_text', '')
            original_text = segment.get('text', '')
            
            print(f"\n--- 處理段落 {i} ({speaker}) ---")
            
            # 選擇使用客語文本還是原始文本
            # 先試客語文本，如果太複雜就用原始文本
            test_texts = [
                {'name': '客語文本', 'text': hakka_text},
                {'name': '原始中文', 'text': original_text}
            ]
            
            for text_option in test_texts:
                text_to_process = text_option['text']
                if not text_to_process.strip():
                    continue
                
                print(f"\n  嘗試 {text_option['name']}...")
                print(f"  原始長度: {len(text_to_process)} 字")
                
                # 清理文本
                cleaned_text = clean_hakka_text(text_to_process)
                print(f"  清理後: {cleaned_text[:50]}..." if len(cleaned_text) > 50 else f"  清理後: {cleaned_text}")
                
                # 分段處理
                segments = split_text_by_sentences(cleaned_text, max_length=40)
                print(f"  分為 {len(segments)} 段")
                
                segment_results = []
                segment_success = 0
                
                for j, segment_text in enumerate(segments, 1):
                    print(f"    段落 {j}/{len(segments)}: {segment_text}")
                    
                    try:
                        result = await tts_service.generate_hakka_audio(
                            hakka_text=segment_text,
                            romanization=""
                        )
                        
                        if result.get('audio_id') and result.get('voice_model') != 'fallback':
                            print(f"    ✅ 合成成功 (真實 TTS)")
                            segment_success += 1
                            segment_results.append(result)
                            total_duration += result.get('duration', 0)
                        else:
                            print(f"    ⚠️  使用 Fallback")
                            segment_results.append(result)
                        
                    except Exception as e:
                        print(f"    ❌ 合成失敗: {e}")
                
                print(f"  成功率: {segment_success}/{len(segments)} ({segment_success/len(segments)*100:.1f}%)")
                
                # 如果這個選項成功率不錯，就使用它
                if segment_success / len(segments) >= 0.5:  # 至少50%成功
                    all_results.append({
                        'segment_index': i,
                        'speaker': speaker,
                        'text_type': text_option['name'],
                        'segments': segment_results,
                        'success_rate': segment_success / len(segments)
                    })
                    print(f"  ✓ 採用此文本版本")
                    break
                else:
                    print(f"  ✗ 成功率太低，嘗試下一個選項")
            else:
                print(f"  ⚠️  所有文本選項都失敗，跳過此段落")
        
        # 總結結果
        print(f"\n=== 播客音檔生成結果 ===")
        print(f"總段落數: {len(content)}")
        print(f"成功處理: {len(all_results)}")
        print(f"預估總時長: {total_duration:.1f} 秒 ({total_duration/60:.1f} 分鐘)")
        
        # 顯示詳細結果
        total_audio_files = 0
        for result in all_results:
            print(f"\n📝 段落 {result['segment_index']} ({result['speaker']}) - {result['text_type']}")
            print(f"   成功率: {result['success_rate']*100:.1f}%")
            print(f"   音檔數: {len(result['segments'])}")
            
            for j, seg in enumerate(result['segments'], 1):
                if seg.get('audio_id'):
                    print(f"     {j}. {Path(seg['audio_path']).name} ({seg.get('duration', 0)}s)")
                    total_audio_files += 1
        
        print(f"\n✅ 總共生成 {total_audio_files} 個音檔")
        
        # 生成播放列表
        playlist_file = Path("static/audio/podcast_playlist.json")
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
        
        print(f"📄 播放列表已保存至: {playlist_file}")
        
        # 登出
        await tts_service.logout()
        print("\n✅ 已登出 TTS API")
        
    except Exception as e:
        print(f"❌ 處理過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await tts_service.close()
        print("=== 處理完成 ===")

def main():
    """主函數"""
    print("客語播客 TTS 優化工具")
    print("====================")
    
    # 檢查配置
    if not settings.HAKKA_USERNAME or not settings.HAKKA_PASSWORD:
        print("❌ 錯誤：請先設定 HAKKA_USERNAME 和 HAKKA_PASSWORD 環境變數")
        sys.exit(1)
    
    # 執行異步處理
    asyncio.run(generate_podcast_audio())

if __name__ == "__main__":
    main()
