"""
優化後的菲律賓總統訪美新聞對話式播客生成
針對用戶需求，生成更豐富詳細的雙主持人深度對話腳本
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.pydantic_ai_service import PydanticAIService
from app.models.podcast import PodcastGenerationRequest

async def generate_detailed_dialogue_podcast():
    """生成詳細的菲律賓總統訪美對話式播客"""
    
    print("🎙️ 生成詳細對話式播客腳本")
    print("=" * 70)
    
    # 詳細的新聞背景和分析要點
    comprehensive_prompt = """
    請基於以下新聞內容生成一個專業的雙主持人對話式播客腳本：

    【新聞背景】
    菲律賓總統馬科斯訪問白宮，與美國總統特朗普會談。這是馬科斯任內首次訪美，
    也是特朗普第二任期內首位會見的東南亞領袖。

    【關鍵議題】
    1. 南海爭議：中國海警頻繁用水炮攻擊菲律賓船隻，中方指責菲方「非法入侵」
    2. 軍事合作：美方強調「透過實力實現和平」，討論防禦保證條約
    3. 經貿摩擦：特朗普威脅8月1日對菲律賓商品課徵20%關稅，菲律賓財政部長願意零關稅回應
    4. 高層外交：馬科斯會見國務卿盧比奧、國防部長赫格塞斯
    5. 地緣平衡：菲律賓在美中角力中尋找定位，美中也嘗試管控分歧

    【分析要點】
    - 美菲是最老的條約盟國關係，防禦保證是基石
    - 這次訪問反映東南亞國家在大國博弈中的選擇壓力
    - 經貿談判背後的戰略考量
    - 南海局勢對區域穩定的影響
    - 多極博弈時代的外交平衡術

    請生成一個15-20分鐘的深度對話播客腳本，要求內容豐富、分析深入、對話自然。
    """
    
    try:
        service = PydanticAIService(use_twcc=True)
        print("✅ 初始化 TWCC AFS 服務成功")
        
        test_request = PodcastGenerationRequest(
            topic=comprehensive_prompt,
            tone="educational",
            duration=20
        )
        
        print("🔄 正在生成詳細對話式播客腳本...")
        print("📋 目標長度: 20分鐘深度分析")
        
        result = await service.generate_complete_podcast_content(test_request)
        
        if result.get("success"):
            script = result['structured_script']
            
            print("✅ 生成成功！")
            print("=" * 70)
            print(f"🎙️ {script['title']}")
            print(f"🎧 主持人：{' 與 '.join(script['hosts'])}")
            print()
            print(script['full_dialogue'])
            
            print("\n" + "=" * 70)
            print(f"⏱️  預估播放時長: {script['estimated_duration_minutes']} 分鐘")
            print(f"🎯 討論重點: {', '.join(script['key_points'])}")
            print(f"📚 參考資料: {', '.join(script['sources_mentioned'])}")
            
        else:
            print(f"❌ 生成失敗: {result.get('error')}")
            if 'fallback_content' in result:
                print("🔄 備用腳本:")
                fallback = result['fallback_content']
                print(f"標題: {fallback['title']}")
                print(fallback['full_dialogue'])
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(generate_detailed_dialogue_podcast())
