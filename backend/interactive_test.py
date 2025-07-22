#!/usr/bin/env python3
"""
互動式播客生成測試工具
讓您直接輸入文本進行測試
"""

import asyncio
import sys
from pathlib import Path

# 添加項目路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.pydantic_ai_service import PydanticAIService
from app.models.podcast import PodcastGenerationRequest

async def interactive_test():
    """互動式測試"""
    print("🎙️ 客語播客生成器 - 互動式測試")
    print("=" * 50)
    
    # 初始化服務
    try:
        service = PydanticAIService(use_twcc=True)
        print("✅ TWCC AFS 服務初始化成功")
    except:
        service = PydanticAIService(use_twcc=False)
        print("✅ Gemini 服務初始化成功")
    
    while True:
        print("\n📝 請輸入播客資訊：")
        
        # 輸入主題
        topic = input("🎯 主題 (或按 'q' 退出): ").strip()
        if topic.lower() == 'q':
            print("👋 再見！")
            break
            
        if not topic:
            print("❌ 請輸入有效的主題")
            continue
        
        # 輸入風格
        print("\n🎨 選擇風格：")
        print("1. casual (輕鬆對話)")
        print("2. educational (教育知識)")
        print("3. storytelling (故事敘述)")
        print("4. interview (訪談對話)")
        
        tone_choice = input("選擇 (1-4，默認1): ").strip() or "1"
        tone_map = {
            "1": "casual",
            "2": "educational", 
            "3": "storytelling",
            "4": "interview"
        }
        tone = tone_map.get(tone_choice, "casual")
        
        # 輸入時長
        duration_input = input("⏱️  時長 (分鐘，默認10): ").strip() or "10"
        try:
            duration = int(duration_input)
        except:
            duration = 10
        
        print(f"\n🚀 正在生成播客...")
        print(f"   主題: {topic}")
        print(f"   風格: {tone}")
        print(f"   時長: {duration}分鐘")
        print("-" * 50)
        
        # 生成播客
        request = PodcastGenerationRequest(
            topic=topic,
            tone=tone,
            duration=duration
        )
        
        try:
            result = await service.generate_complete_podcast_content(request)
            
            if result.get("success"):
                script = result["structured_script"]
                print(f"\n✅ 生成成功！")
                print(f"🏷️  標題: {script['title']}")
                print(f"📊 預估時長: {script['estimated_duration_minutes']}分鐘")
                print(f"🎯 關鍵要點: {', '.join(script['key_points'])}")
                
                print(f"\n📜 完整腳本:")
                print("=" * 50)
                print(result["full_content"])
                print("=" * 50)
                
            else:
                print(f"❌ 生成失敗: {result.get('error', '未知錯誤')}")
                
        except Exception as e:
            print(f"❌ 系統錯誤: {e}")
        
        # 詢問是否繼續
        continue_test = input("\n🔄 是否繼續測試？(y/n，默認y): ").strip().lower()
        if continue_test == 'n':
            print("👋 測試結束，再見！")
            break

if __name__ == "__main__":
    asyncio.run(interactive_test())
