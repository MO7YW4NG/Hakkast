#!/usr/bin/env python3
"""
菲律賓總統訪美新聞 - 客語播客生成測試
使用您提供的新聞內容進行測試
"""

import asyncio
import sys
from pathlib import Path

# 添加項目路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.pydantic_ai_service import PydanticAIService
from app.models.podcast import PodcastGenerationRequest

async def test_philippines_news():
    """測試菲律賓總統訪美新聞內容"""
    print("📰 菲律賓總統訪美新聞 - 客語播客生成測試")
    print("=" * 60)
    
    # 初始化服務
    try:
        service = PydanticAIService(use_twcc=True)
        print("✅ TWCC AFS 服務初始化成功")
    except:
        try:
            service = PydanticAIService(use_twcc=False) 
            print("✅ Gemini 服務初始化成功")
        except Exception as e:
            print(f"❌ 服務初始化失敗: {e}")
            return
    
    # 基於新聞內容的播客主題
    test_topics = [
        {
            "topic": "菲律賓總統訪美：從客家人視角看亞太地緣政治變化",
            "tone": "educational",
            "duration": 15,
            "description": "教育性分析國際政治"
        },
        {
            "topic": "中美貿易關稅對客家海外商業的影響：以菲律賓為例",
            "tone": "casual",
            "duration": 12,
            "description": "輕鬆討論經濟議題"
        },
        {
            "topic": "南海爭議下的東南亞客家社群：挑戰與機遇",
            "tone": "storytelling",
            "duration": 18,
            "description": "故事式探討社群處境"
        }
    ]
    
    for i, test_data in enumerate(test_topics, 1):
        print(f"\n🎯 測試 {i}: {test_data['topic']}")
        print(f"📋 描述: {test_data['description']}")
        print(f"🎨 風格: {test_data['tone']}")
        print(f"⏱️  時長: {test_data['duration']}分鐘")
        print("-" * 60)
        
        # 創建請求
        request = PodcastGenerationRequest(
            topic=test_data['topic'],
            tone=test_data['tone'],
            duration=test_data['duration']
        )
        
        try:
            # 生成播客內容
            result = await service.generate_complete_podcast_content(request)
            
            if result.get("success"):
                script = result['structured_script']
                analysis = result['content_analysis']
                
                print("✅ 生成成功！")
                print(f"🏷️  AI生成標題: {script['title']}")
                print(f"📊 內容分析:")
                print(f"   - 類別: {analysis['topic_category']}")
                print(f"   - 複雜度: {analysis['complexity_level']}")  
                print(f"   - 目標受眾: {analysis['target_audience']}")
                print(f"   - 內容時效性: {analysis['content_freshness']}")
                
                print(f"\n🎯 關鍵要點: {', '.join(script['key_points'])}")
                print(f"📚 資料來源: {', '.join(script['sources_mentioned'])}")
                print(f"⏱️  預估時長: {script['estimated_duration_minutes']} 分鐘")
                
                # 顯示完整腳本內容
                print(f"\n� 完整播客腳本:")
                print("=" * 60)
                print(f"標題：{script['title']}")
                print(f"\n開場：")
                print(script['introduction'])
                print(f"\n主要內容：")
                print(script['main_content'])
                print(f"\n結語：")
                print(script['conclusion'])
                print("=" * 60)
                    
                print(f"\n🤖 使用模型: {result['model_info']['provider']} - {result['model_info']['model_name']}")
                print(f"🕐 生成時間: {result['generation_timestamp']}")
                
            else:
                print(f"❌ 生成失敗: {result.get('error', '未知錯誤')}")
                
        except Exception as e:
            print(f"❌ 測試過程發生錯誤: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "="*60)
        
        # 在測試間添加短暫延遲
        if i < len(test_topics):
            print("⏳ 稍等片刻，準備下一個測試...")
            await asyncio.sleep(2)
    
    print("\n🏁 所有測試完成！")
    print("💡 總結：成功將國際新聞轉化為客家文化視角的播客內容")

if __name__ == "__main__":
    asyncio.run(test_philippines_news())
