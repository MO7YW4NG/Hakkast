"""
整合測試：爬蟲 + AI 播客生成完整流程
使用現有的 crawl4ai_service 抓取新聞，然後生成播客
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.crawl4ai_service import crawl_news
from app.services.pydantic_ai_service import PydanticAIService
from app.models.podcast import PodcastGenerationRequest

async def test_full_pipeline():
    """測試完整的爬蟲→AI播客生成管線"""
    
    print("🚀 開始完整管線測試")
    print("=" * 60)
    
    # Step 1: 使用爬蟲獲取新聞
    print("📰 Step 1: 爬取新聞內容...")
    try:
        # 測試抓取科技新聞
        crawled_articles = await crawl_news("technology_news", max_articles=3)
        
        if not crawled_articles:
            print("❌ 沒有抓到任何新聞，使用備用內容")
            # 如果爬蟲失敗，使用模擬內容
            from app.models.crawler import CrawledContent, ContentType
            from datetime import datetime
            
            crawled_articles = [
                CrawledContent(
                    id="test-1",
                    title="AI 技術最新突破：大型語言模型在多模態應用",
                    content="最新研究顯示，大型語言模型在結合視覺、音訊等多模態資料方面取得重大突破...",
                    summary="AI技術在多模態應用方面的最新進展",
                    url="https://example.com/ai-breakthrough",
                    source="tech_news",
                    published_at=datetime.now(),
                    crawled_at=datetime.now(),
                    content_type=ContentType.NEWS,
                    topic="technology_news",
                    keywords=["AI", "語言模型", "多模態"],
                    relevance_score=0.9
                )
            ]
        
        print(f"✅ 成功獲取 {len(crawled_articles)} 篇新聞")
        for i, article in enumerate(crawled_articles, 1):
            print(f"   {i}. {article.title}")
            print(f"      來源: {article.source}")
            print(f"      摘要: {article.summary[:100]}...")
            print()
    
    except Exception as e:
        print(f"❌ 爬蟲階段失敗: {e}")
        return
    
    # Step 2: 分析新聞內容並準備播客主題
    print("🤖 Step 2: 分析新聞並準備 AI 生成...")
    
    # 組合新聞內容為播客主題
    main_titles = [article.title for article in crawled_articles[:2]]
    combined_content = "\n\n".join([
        f"新聞 {i+1}: {article.title}\n內容: {article.content[:300]}..."
        for i, article in enumerate(crawled_articles[:3])
    ])
    
    podcast_topic = f"""
    基於以下最新科技新聞，請生成一個專業的雙主持人對話式播客腳本：

    主要新聞標題：
    {' | '.join(main_titles)}
    
    詳細新聞內容：
    {combined_content}
    
    請生成一個15-18分鐘的科技分析播客，要求：
    1. 深度分析這些科技發展的意義和影響
    2. 討論對產業和社會的潛在變化
    3. 雙主持人自然對話風格
    4. 專業但易懂的解說方式
    5. 包含未來趨勢預測
    """
    
    print("📝 準備的播客主題:")
    print(f"   主要標題: {main_titles[0] if main_titles else '無'}")
    print(f"   新聞數量: {len(crawled_articles)}")
    print()
    
    # Step 3: 使用 AI 生成播客
    print("🎙️ Step 3: AI 生成播客腳本...")
    
    try:
        # 初始化 AI 服務
        ai_service = PydanticAIService(use_twcc=True)
        
        # 創建播客請求
        request = PodcastGenerationRequest(
            topic=podcast_topic,
            tone="educational",
            duration=18
        )
        
        # 生成播客（將爬蟲內容傳給 AI）
        result = await ai_service.generate_complete_podcast_content(
            request, 
            crawled_content=crawled_articles  # 這裡傳入爬蟲獲取的內容
        )
        
        if result.get("success"):
            script = result['structured_script']
            
            print("🎉 完整管線測試成功！")
            print("=" * 60)
            print(f"🎙️ {script['title']}")
            print(f"🎧 主持人: {' 與 '.join(script['hosts'])}")
            print()
            
            # 顯示生成的對話（前500字）
            dialogue = script['full_dialogue']
            print("📜 生成的播客對話（預覽）:")
            print(dialogue[:800] + "..." if len(dialogue) > 800 else dialogue)
            
            print("\n" + "=" * 60)
            print("📊 播客資訊:")
            print(f"⏱️  預估時長: {script['estimated_duration_minutes']} 分鐘")
            print(f"🎯 關鍵議題: {', '.join(script['key_points'])}")
            print(f"📚 資料來源: {', '.join(script['sources_mentioned'])}")
            
            # 顯示使用的新聞來源
            print(f"\n📰 使用的新聞來源:")
            for article in crawled_articles:
                print(f"   • {article.title} ({article.source})")
            
            model_info = result['model_info']
            print(f"\n🤖 技術資訊:")
            print(f"   AI 提供商: {model_info['provider']}")
            print(f"   模型: {model_info['model_name']}")
            
        else:
            print(f"❌ AI 生成失敗: {result.get('error')}")
    
    except Exception as e:
        print(f"❌ AI 生成階段失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🎙️ Hakkast 爬蟲+AI 播客完整管線測試")
    print("🔗 測試流程: 新聞爬取 → 內容分析 → AI播客生成")
    print()
    asyncio.run(test_full_pipeline())
