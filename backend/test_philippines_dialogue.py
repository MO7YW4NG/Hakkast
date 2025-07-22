"""
測試菲律賓總統訪美新聞的對話式播客生成
基於用戶提供的具體新聞內容，生成雙主持人對話式播客腳本
"""
import asyncio
import os
import sys

# 添加app目錄到Python路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.pydantic_ai_service import PydanticAIService
from app.models.podcast import PodcastGenerationRequest

async def test_dialogue_podcast():
    """測試菲律賓總統訪美新聞的對話式播客生成"""
    
    print("🎙️ 測試對話式播客腳本生成")
    print("=" * 60)
    
    # 菲律賓總統訪美新聞內容 - 更詳細的資料
    news_content = """
    根據美聯社報導，菲律賓總統馬科斯訪問白宮，與美國總統特朗普會談。
    這是馬科斯任內首次訪美，也是特朗普第二任期內首位會見的東南亞領袖。
    
    會談重點包括：
    1. 南海爭議：中國海警頻繁用水炮攻擊菲律賓船隻，中方指責菲方「非法入侵」
    2. 軍事合作：美方強調「透過實力實現和平」，討論防禦保證
    3. 經貿關係：特朗普威脅對菲律賓商品課徵20%關稅，菲律賓財政部長表態願意零關稅
    4. 高層會談：馬科斯會見美國國務卿盧比奧、國防部長赫格塞斯
    5. 地緣戰略：菲律賓在美中角力中的定位和選擇
    
    美菲是最老的條約盟國之一，雙邊防禦保證被視為關係基石。
    美中雙方也在嘗試管控分歧，盧比奧最近與中國外長王毅會面。
    """
    
    try:
        # 初始化服務
        service = PydanticAIService(use_twcc=True)
        print("✅ 成功初始化 TWCC AFS 服務")
        
        # 創建測試請求
        test_request = PodcastGenerationRequest(
            topic=f"深度分析：菲律賓總統馬科斯訪美的地緣政治意義。背景資料：{news_content}",
            tone="educational",  # 教育性風格
            duration=18  # 18分鐘，更長的深度分析
        )
        
        print(f"📋 主題: 菲律賓總統馬科斯訪美會談分析")
        print(f"📋 風格: 新聞分析對話")
        print(f"📋 時長: 15 分鐘")
        print("\n🔄 正在生成對話式播客腳本...")
        
        # 生成完整播客內容
        result = await service.generate_complete_podcast_content(test_request)
        
        if result.get("success"):
            print("✅ 成功生成對話式播客腳本！")
            print("=" * 60)
            
            # 顯示完整的對話腳本
            script = result['structured_script']
            print(f"🎙️Podcast 標題：{script['title']}")
            print(f"🎧主持人：{' 與 '.join(script['hosts'])}")
            print()
            print(script['full_dialogue'])
            
            print("\n" + "=" * 60)
            print("� 腳本資訊:")
            print(f"⏱️  預估時長: {script['estimated_duration_minutes']} 分鐘")
            print(f"🎯 關鍵要點:")
            for point in script['key_points']:
                print(f"   • {point}")
            print(f"📚 資料來源: {', '.join(script['sources_mentioned'])}")
            
            print(f"\n🤖 模型資訊:")
            model_info = result['model_info']
            print(f"   提供商: {model_info['provider']}")
            print(f"   模型: {model_info['model_name']}")
            
        else:
            print(f"❌ 生成失敗: {result.get('error', 'Unknown error')}")
            if 'fallback_content' in result:
                print("🔄 使用備用腳本:")
                print(result['fallback_content'])
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_dialogue_podcast())
