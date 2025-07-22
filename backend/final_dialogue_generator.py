"""
最終版本：菲律賓總統訪美新聞對話式播客生成器
生成符合用戶要求的完整雙主持人深度對話播客腳本
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.pydantic_ai_service import PydanticAIService
from app.models.podcast import PodcastGenerationRequest

async def generate_final_dialogue_podcast():
    """生成最終版本的菲律賓總統訪美對話式播客"""
    
    print("🎙️ 生成完整對話式播客腳本")
    print("🎯 目標：雙主持人深度對話分析")
    print("=" * 70)
    
    # 詳細的新聞內容和分析要求
    news_topic = """
    基於美聯社報導的菲律賓總統馬科斯訪美新聞，請生成一個專業的雙主持人對話式播客腳本。
    
    新聞重點：
    - 馬科斯首次訪美，特朗普第二任期首位東南亞領袖會談
    - 南海爭議：中國海警水炮攻擊vs菲律賓船隻「非法入侵」指控
    - 軍事合作：美方「透過實力實現和平」，討論防禦保證條約
    - 經貿談判：特朗普威脅20%關稅vs菲律賓願意零關稅回應
    - 高層外交：會見盧比奧、赫格塞斯等關鍵官員
    - 地緣戰略：美中角力下的菲律賓定位選擇
    
    請生成一個18-20分鐘的深度對話播客，要求：
    1. 完整的開場、深度分析、總結結尾
    2. 自然流暢的雙主持人對話
    3. 深入分析地緣政治和經濟影響
    4. 專業但易懂的分析風格
    5. 包含具體事實和背景解釋
    """
    
    try:
        # 嘗試使用 TWCC，失敗則使用 Gemini
        try:
            service = PydanticAIService(use_twcc=True)
            print("✅ 使用 TWCC AFS 服務")
        except Exception as e:
            print(f"⚠️  TWCC 不可用，切換至 Gemini: {e}")
            service = PydanticAIService(use_twcc=False)
            print("✅ 使用 Google Gemini 服務")
        
        # 創建播客生成請求
        request = PodcastGenerationRequest(
            topic=news_topic,
            tone="educational",  # 教育性深度分析
            duration=20  # 20分鐘深度內容
        )
        
        print("🔄 開始生成對話式播客腳本...")
        print("📊 預期長度：20分鐘深度對話")
        print("🎭 風格：專業新聞分析對話")
        
        # 生成完整播客內容
        result = await service.generate_complete_podcast_content(request)
        
        if result.get("success"):
            script = result['structured_script']
            
            print("\n" + "🎉 生成成功！" + "🎉")
            print("=" * 70)
            
            # 顯示標題和主持人
            print(f"🎙️ {script['title']}")
            print(f"🎧 主持人：{' 與 '.join(script['hosts'])}")
            print()
            
            # 顯示完整對話腳本
            dialogue_lines = script['full_dialogue'].split('\n')
            for line in dialogue_lines:
                if line.strip():
                    print(line)
            
            # 顯示腳本資訊
            print("\n" + "=" * 70)
            print("📊 播客資訊：")
            print(f"⏱️  預估時長：{script['estimated_duration_minutes']} 分鐘")
            print(f"🎯 關鍵議題：")
            for point in script['key_points']:
                print(f"   • {point}")
            print(f"📚 資料來源：{', '.join(script['sources_mentioned'])}")
            
            # 顯示技術資訊
            model_info = result['model_info']
            print(f"\n🤖 生成資訊：")
            print(f"   AI提供商：{model_info['provider']}")
            print(f"   使用模型：{model_info['model_name']}")
            print(f"   生成時間：{result['generation_timestamp']}")
            
        else:
            print("❌ 主要生成失敗，使用備用方案")
            if 'fallback_content' in result:
                fallback = result['fallback_content']
                print(f"🏷️  備用標題：{fallback['title']}")
                print(f"📝 備用腳本：")
                print(fallback['full_dialogue'])
            print(f"錯誤原因：{result.get('error', '未知錯誤')}")
        
    except Exception as e:
        print(f"❌ 系統錯誤：{e}")
        print("請檢查網路連接和API設定")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🎙️ Hakkast 播客生成系統")
    print("📰 專案：菲律賓總統訪美新聞分析")
    asyncio.run(generate_final_dialogue_podcast())
