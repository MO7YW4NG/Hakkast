#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys
import os
from pathlib import Path

# 添加項目根目錄到 Python 路徑
sys.path.append(str(Path(__file__).parent.parent))

def create_correct_playlist():
    """根據原始腳本和現有音檔重新生成正確的播放列表"""
    
    # 載入原始腳本
    script_path = Path(__file__).parent.parent / "json" / "podcast_script_technology_news_3articles.json"
    with open(script_path, 'r', encoding='utf-8') as f:
        script_data = json.load(f)
    
    # 音檔目錄
    audio_dir = Path(__file__).parent.parent / "static" / "audio"
    
    # 創建播放列表結構
    playlist_data = {
        'title': 'Hakkast 哈客播新聞討論',
        'total_duration': 0,
        'segments': []
    }
    
    # 處理每個內容段落
    for i, content_item in enumerate(script_data['content'], 1):
        speaker = content_item.get('speaker', 'Unknown')
        hakka_text = content_item.get('hakka_text', '')
        romanization = content_item.get('romanization', '')
        
        # 確定說話者代碼
        if speaker == "佳昀":
            speaker_code = "SXF"
        elif speaker == "敏權":
            speaker_code = "SXM"
        else:
            speaker_code = "SXF"  # 默認
        
        # 查找對應的音檔 - 使用更精確的模式
        audio_pattern = f"podcast_script_technology_news_3articles_{speaker_code}_{i}*.wav"
        audio_files = list(audio_dir.glob(audio_pattern))
        
        # 如果沒找到，嘗試其他可能的模式
        if not audio_files:
            # 嘗試百位數格式：101, 201, etc.
            audio_pattern = f"podcast_script_technology_news_3articles_{speaker_code}_{i}*1.wav"
            audio_files = list(audio_dir.glob(audio_pattern))
        
        if not audio_files:
            print(f"警告：找不到說話者 {speaker} 段落 {i} 的音檔")
            continue
        
        # 按檔名中的數字排序
        def extract_segment_number(filepath):
            try:
                name = filepath.stem
                # 提取最後的數字部分，例如：SXF_1101 -> 1101
                parts = name.split('_')
                return int(parts[-1])
            except (ValueError, IndexError):
                return 0
        
        audio_files.sort(key=extract_segment_number)
        
        print(f"處理 {speaker} 段落 {i}，找到 {len(audio_files)} 個音檔")
        
        # 智能分割文本和羅馬拼音
        text_segments = []
        rom_segments = []
        
        if hakka_text:
            # 按標點符號分割文本
            import re
            # 更仔細的分割，保留標點符號
            text_parts = re.split(r'([。！？；，])', hakka_text)
            # 重新組合，每兩個部分為一段（文字+標點）
            combined_parts = []
            for j in range(0, len(text_parts) - 1, 2):
                if j + 1 < len(text_parts):
                    combined_parts.append(text_parts[j] + text_parts[j + 1])
                else:
                    combined_parts.append(text_parts[j])
            
            # 如果沒有標點符號，按字數分割
            if len(combined_parts) <= 1:
                text_len = len(hakka_text)
                chars_per_segment = max(1, text_len // len(audio_files))
                combined_parts = []
                for j in range(0, text_len, chars_per_segment):
                    combined_parts.append(hakka_text[j:j + chars_per_segment])
            
            text_segments = [part.strip() for part in combined_parts if part.strip()]
        
        if romanization:
            # 分割羅馬拼音
            rom_words = romanization.split()
            if len(rom_words) > 0 and len(audio_files) > 0:
                words_per_segment = max(1, len(rom_words) // len(audio_files))
                for j in range(len(audio_files)):
                    start_idx = j * words_per_segment
                    if j == len(audio_files) - 1:  # 最後一段取剩下的所有
                        rom_segments.append(' '.join(rom_words[start_idx:]))
                    else:
                        end_idx = start_idx + words_per_segment
                        rom_segments.append(' '.join(rom_words[start_idx:end_idx]))
        
        # 確保段落數量匹配音檔數量
        while len(text_segments) < len(audio_files):
            if text_segments:
                text_segments.append("")
            else:
                text_segments.append(hakka_text)  # 如果沒有分段，全部用原文
        
        while len(rom_segments) < len(audio_files):
            if rom_segments:
                rom_segments.append("")
            else:
                rom_segments.append(romanization)  # 如果沒有分段，全部用原羅馬拼音
        
        # 創建段落資訊
        segment_info = {
            'speaker': speaker,
            'text_type': '客語文本',
            'audio_files': []
        }
        
        # 處理每個音檔
        for j, audio_file in enumerate(audio_files):
            # 獲取音檔時長（模擬）
            file_size = audio_file.stat().st_size
            estimated_duration = max(5, int(file_size / 80000))  # 調整估算公式
            
            # 獲取對應的文本和羅馬拼音
            text = text_segments[j] if j < len(text_segments) else ''
            rom = rom_segments[j] if j < len(rom_segments) else ''
            
            audio_file_info = {
                'file': f"/static/audio/{audio_file.name}",
                'duration': estimated_duration,
                'text': text,
                'romanization': rom,
                'voice_model': f"broncitts/hak-xi-TW-vs2-{'F01' if speaker_code == 'SXF' else 'M01'}"
            }
            
            segment_info['audio_files'].append(audio_file_info)
            playlist_data['total_duration'] += estimated_duration
        
        if segment_info['audio_files']:
            playlist_data['segments'].append(segment_info)
    
    # 保存播放列表
    playlist_path = audio_dir / "podcast_playlist.json"
    with open(playlist_path, 'w', encoding='utf-8') as f:
        json.dump(playlist_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 播放列表已生成： {playlist_path}")
    print(f"📊 總時長： {playlist_data['total_duration']} 秒")
    print(f"🎵 總段落數： {len(playlist_data['segments'])}")
    
    # 顯示前幾個段落的預覽
    print("\n📋 播放列表預覽：")
    for i, segment in enumerate(playlist_data['segments'][:3]):
        print(f"段落 {i+1} - {segment['speaker']}:")
        for j, audio in enumerate(segment['audio_files'][:2]):
            print(f"  音檔 {j+1}: {Path(audio['file']).name}")
            print(f"    文字: {audio['text'][:30]}...")
            print(f"    羅馬拼音: {audio['romanization'][:40]}...")
    
    return playlist_data

if __name__ == "__main__":
    create_correct_playlist()
