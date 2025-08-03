#!/usr/bin/env python3
"""
測試播放列表生成功能
展示動態標題和羅馬拼音記錄功能
"""

import asyncio
import json
from pathlib import Path
from app.podcast_audio_manager import PodcastAudioManager

async def test_playlist_structure():
    """測試播放列表生成結構"""
    
    # 模擬腳本數據
    script_data = {
        "title": "Hakkast 哈客播新聞討論",
        "hosts": ["佳昀", "敏權"],
        "content": [
            {
                "speaker": "佳昀",
                "text": "大家好，我是佳昀。",
                "hakka_text": "大家好，𠊎係佳昀。",
                "romanization": "tai55 ga24 ho31, ngai11 he55 ga24 iun11."
            },
            {
                "speaker": "敏權", 
                "text": "我是敏權，歡迎收聽Hakkast 哈客播。",
                "hakka_text": "𠊎係敏權，歡迎收聽 Hakkast 哈客播。",
                "romanization": "ngai11 he55 men31 kien11, fon24 ngiang11 su24 tang24 ha24 ka24 si24 te24 ha24 hag2 bo24."
            }
        ]
    }
    
    # 模擬 TTS 結果數據（假設已經生成了音檔）
    mock_results = [
        {
            'speaker': '佳昀',
            'text_type': '客語文本',
            'segments': [
                {
                    'audio_id': 'test_SXF_101',
                    'audio_path': '/path/to/audio/test_SXF_101.wav',
                    'duration': 10,
                    'text': '大家好，𠊎係佳昀。',
                    'romanization': 'tai55 ga24 ho31, ngai11 he55 ga24 iun11.',
                    'voice_model': 'broncitts/hak-xi-TW-vs2-F01'
                }
            ]
        },
        {
            'speaker': '敏權',
            'text_type': '客語文本', 
            'segments': [
                {
                    'audio_id': 'test_SXM_201',
                    'audio_path': '/path/to/audio/test_SXM_201.wav',
                    'duration': 15,
                    'text': '𠊎係敏權，歡迎收聽 Hakkast 哈客播。',
                    'romanization': 'ngai11 he55 men31 kien11, fon24 ngiang11 su24 tang24 ha24 ka24 si24 te24 ha24 hag2 bo24.',
                    'voice_model': 'broncitts/hak-xi-TW-vs2-M01'
                }
            ]
        }
    ]
    
    # 生成播放列表結構（模擬修改後的邏輯）
    podcast_title = script_data.get('title', '客語播客')
    total_duration = sum(
        seg.get('duration', 0) 
        for result in mock_results 
        for seg in result['segments'] 
        if seg.get('audio_id')
    )
    
    playlist_data = {
        'title': podcast_title,
        'total_duration': total_duration,
        'segments': []
    }
    
    for result in mock_results:
        segment_info = {
            'speaker': result['speaker'],
            'text_type': result['text_type'],
            'audio_files': []
        }
        
        for seg in result['segments']:
            if seg.get('audio_id'):
                audio_file_info = {
                    'file': f"/static/audio/{Path(seg['audio_path']).name}",
                    'duration': seg.get('duration', 0),
                    'text': seg.get('text', ''),
                }
                
                # 添加羅馬拼音資訊（如果有的話）
                if seg.get('romanization'):
                    audio_file_info['romanization'] = seg.get('romanization')
                
                # 添加語音模型資訊
                if seg.get('voice_model'):
                    audio_file_info['voice_model'] = seg.get('voice_model')
                    
                segment_info['audio_files'].append(audio_file_info)
        
        if segment_info['audio_files']:  # 只添加有音檔的段落
            playlist_data['segments'].append(segment_info)
    
    # 輸出結果
    print("=== 更新後的播放列表結構 ===")
    print(json.dumps(playlist_data, ensure_ascii=False, indent=2))
    
    # 保存測試結果
    test_file = Path(__file__).parent / "static" / "audio" / "test_podcast_playlist.json"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(playlist_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 測試播放列表已保存至: {test_file}")
    
    # 對比說明
    print("\n=== 功能改進說明 ===")
    print("✅ 動態標題: 從腳本中讀取標題，不再寫死")
    print("✅ 羅馬拼音: 記錄每個音檔的羅馬拼音資訊")
    print("✅ 語音模型: 記錄使用的語音模型資訊")
    print("✅ 資料完整性: 只包含成功生成音檔的段落")

if __name__ == "__main__":
    asyncio.run(test_playlist_structure())
