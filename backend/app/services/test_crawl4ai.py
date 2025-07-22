import asyncio
from app.services.crawl4ai_service import crawl_news
from app.services.pydantic_ai_service import PydanticAIService
from app.models.podcast import PodcastGenerationRequest

TOPIC_OPTIONS = {
    "1": {
        "key": "technology_news",
        "name": "科技新聞",
        "description": "最新科技趨勢、AI、雲端、數位轉型等議題"
    },
    "2": {
        "key": "finance_economics", 
        "name": "財經新聞",
        "description": "金融市場、經濟政策、投資趨勢分析"
    },
    "3": {
        "key": "research_deep_learning",
        "name": "深度學習研究",
        "description": "最新AI研究論文、機器學習技術突破"
    }
}

async def test_topic_crawling():
    """測試主題爬取和 AI 生成功能"""
    print("🎙️ Hakkast 主題爬取測試")
    print("=" * 50)
    print()
    
    # 顯示主題選項
    print("📰 可用主題：")
    for key, value in TOPIC_OPTIONS.items():
        print(f"   {key}. {value['name']} - {value['description']}")
    print()

    choice = input("請選擇主題 (1-3) 或按 Enter 測試所有主題: ").strip()

    if not choice:
        # 測試所有主題
        print("🔄 測試所有主題...")
        for key, value in TOPIC_OPTIONS.items():
            print(f"\n{'='*60}")
            print(f"測試主題: {value['name']}")
            print(f"{'='*60}")
            
            try:
                articles = await crawl_news(value['key'], max_articles=2)
                print(f"✅ {value['name']} - 成功抓取 {len(articles)} 篇文章")
                
                if articles:
                    print(f"   📄 範例文章: {articles[0].title[:50]}...")
            except Exception as e:
                print(f"❌ {value['name']} - 錯誤: {str(e)}")
    else:
        # 測試單一主題
        topic_info = TOPIC_OPTIONS.get(choice)
        if not topic_info:
            print("❌ 無效選項")
            return
            
        print(f"\n🔄 測試主題: {topic_info['name']}")
        print("-" * 50)
        
        try:
            # 爬取文章
            articles = await crawl_news(topic_info['key'], max_articles=3)
            
            if not articles:
                print("❌ 沒有抓到任何文章")
                return
                
            print(f"✅ 成功爬取 {len(articles)} 篇文章")
            
            # 顯示文章列表
            for i, article in enumerate(articles, 1):
                print(f"   {i}. {article.title}")
                print(f"      來源: {article.source} | 發布: {article.published_at.date()}")
            
            # 詢問是否生成播客
            generate = input("\n🤖 是否要生成 AI 播客腳本? (y/N): ").strip().lower()
            
            if generate in ['y', 'yes', '是']:
                print("\n🤖 正在生成播客腳本...")
                
                # 準備內容
                main_title = articles[0].title
                combined_content = "\n\n".join([
                    f"標題: {article.title}\n內容: {article.content or article.summary}"
                    for article in articles
                ])
                
                # 生成播客
                podcast_service = PydanticAIService()
                
                # 創建請求
                request = PodcastGenerationRequest(
                    topic=main_title,
                    content=combined_content,
                    tone="casual",  # 修正為有效的 tone 值
                    duration=15
                )
                
                podcast = await podcast_service.generate_podcast_script(
                    request=request,
                    crawled_content=articles
                )
                
                print("\n🎉 播客腳本生成完成！")
                print("-" * 50)
                print(f"🎙️ 標題: {podcast.title}")
                print(f"👥 主持人: {podcast.hosts}")
                print(f"⏱️ 時長: {podcast.estimated_duration_minutes} 分鐘")
                print(f"🏷️ 關鍵詞: {', '.join(podcast.key_points)}")
                print("\n💬 對話預覽:")
                print(podcast.full_dialogue[:300] + "...")
                
        except Exception as e:
            print(f"❌ 錯誤: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_topic_crawling())
