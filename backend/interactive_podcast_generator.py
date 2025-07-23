#!/usr/bin/env python3
"""
Hakkast 互動式播客生成系统
用戶可選擇主題 → 爬取相關文章 → AI生成播客腳本
"""

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

async def interactive_podcast_generator():
    """
    互動式播客生成主程式
    """
    print("🎙️ " + "="*60)
    print("🎙️  歡迎使用 Hakkast 客家播客生成系統")
    print("🎙️ " + "="*60)
    print()
    
    # 顯示主題選項
    print("📰 請選擇你想要的播客主題：")
    print()
    for key, value in TOPIC_OPTIONS.items():
        print(f"   {key}. {value['name']}")
        print(f"      {value['description']}")
        print()
    
    # 用戶選擇
    while True:
        choice = input("請輸入選項 (1-3) 或 'q' 退出: ").strip()
        
        if choice.lower() == 'q':
            print("👋 感謝使用 Hakkast！再見！")
            return
        
        if choice in TOPIC_OPTIONS:
            selected_topic = TOPIC_OPTIONS[choice]
            break
        else:
            print("❌ 無效選項，請輸入 1、2、3 或 'q'")
            continue
    
    print()
    print("🔄 " + "="*60)
    print(f"🔄  已選擇主題: {selected_topic['name']}")
    print("🔄 " + "="*60)
    print()
    
    # 設定爬取文章數量
    while True:
        try:
            max_articles = input("📊 要爬取幾篇文章？(預設3篇，按Enter跳過): ").strip()
            if not max_articles:
                max_articles = 3
                break
            max_articles = int(max_articles)
            if 1 <= max_articles <= 10:
                break
            else:
                print("❌ 請輸入 1-10 之間的數字")
        except ValueError:
            print("❌ 請輸入有效數字")
    
    topic_key = selected_topic['key']
    
    print()
    print("🕷️ " + "="*60)
    print(f"🕷️  開始爬取 {selected_topic['name']} 相關文章...")
    print("🕷️ " + "="*60)
    print()
    
    # 爬取新聞
    try:
        crawled_articles = await crawl_news(topic_key, max_articles)
        
        if not crawled_articles:
            print("❌ 沒有抓到任何文章，請稍後再試")
            return
        
        print()
        print("✅ " + "="*60)
        print(f"✅  成功爬取 {len(crawled_articles)} 篇文章！")
        print("✅ " + "="*60)
        print()
        
        # 顯示爬取結果
        for i, article in enumerate(crawled_articles, 1):
            print(f"📄 {i}. {article.title}")
            print(f"   🌐 來源: {article.source}")
            print(f"   📅 發布: {article.published_at.strftime('%Y-%m-%d')}")
            print(f"   📝 摘要: {article.summary[:100]}...")
            print()
        
        # 確認是否繼續生成播客
        continue_choice = input("🤖 是否要繼續生成 AI 播客腳本？(y/N): ").strip().lower()
        
        if continue_choice not in ['y', 'yes', '是']:
            print("👋 任務完成！")
            return
        
        print()
        print("🤖 " + "="*60)
        print("🤖  開始生成 AI 播客腳本...")
        print("🤖 " + "="*60)
        print()
        
        # 準備播客內容
        # 使用第一篇文章的標題作為主標題
        main_title = crawled_articles[0].title
        
        # 合併所有文章內容
        combined_content = "\n\n".join([
            f"標題: {article.title}\n內容: {article.content or article.summary}\n來源: {article.url}"
            for article in crawled_articles
        ])
        
        # 生成播客腳本
        # ...爬蟲完後...

        podcast_service = PydanticAIService()

        summaries = []
        print("🔎 開始逐篇摘要：")
        for idx, article in enumerate(crawled_articles, 1):
            print(f"\n--- 第 {idx} 篇 ---")
            print(f"標題: {article.title}")
            print("摘要生成中...")
            # 產生摘要（不是播客腳本！）
            summary = await podcast_service.summarize_article(
                f"請用500字摘要以下新聞內容，只用真實新聞細節，不要虛構：\n{article.content or article.summary}"
            )
            print(f"【摘要】（{len(summary)}字）：\n{summary}\n")
            summaries.append(f"標題: {article.title}\n摘要: {summary}\n來源: {article.url}")

        combined_summary = "\n\n".join(summaries)

        print("\n🚀 三篇摘要已完成，準備丟入 Llama3 生成播客腳本...")
        print("執行中...（請稍候，AI 正在生成約2500字腳本）\n")

        request = PodcastGenerationRequest(
            topic=main_title,
            content=combined_summary,
            tone="casual",
            duration=15
        )

        podcast_script = await podcast_service.generate_podcast_script(
            request=request,
            crawled_content=crawled_articles
        )

        print("\n🎉 播客腳本生成完成！")
        print(f"腳本字數：{len(podcast_script.full_dialogue)}")
        if len(podcast_script.full_dialogue) < 2000:
            print("⚠️ 產出字數偏少，建議檢查摘要長度或強化 prompt。")
        print("\n📝 播客腳本預覽：")
        print(podcast_script.full_dialogue[:500] + "...")
        
        # 詢問是否要查看完整腳本
        full_script_choice = input("📜 是否要查看完整播客腳本？(y/N): ").strip().lower()
        
        if full_script_choice in ['y', 'yes', '是']:
            print()
            print("📜 " + "="*60)
            print("📜  完整播客腳本")
            print("📜 " + "="*60)
            print()
            print(podcast_script.full_dialogue)
            print()
        
        # 詢問是否要保存腳本
        save_choice = input("💾 是否要保存腳本到文件？(y/N): ").strip().lower()
        
        if save_choice in ['y', 'yes', '是']:
            filename = f"podcast_script_{topic_key}_{len(crawled_articles)}articles.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Hakkast 播客腳本\n")
                f.write(f"="*50 + "\n\n")
                f.write(f"標題: {podcast_script.title}\n")
                f.write(f"主持人: {podcast_script.hosts}\n")
                f.write(f"預估時長: {podcast_script.estimated_duration_minutes} 分鐘\n")
                f.write(f"關鍵詞: {', '.join(podcast_script.key_points)}\n")
                f.write(f"主題: {selected_topic['name']}\n")
                f.write(f"文章數量: {len(crawled_articles)}\n")
                f.write(f"\n" + "="*50 + "\n")
                f.write(f"完整對話內容:\n\n")
                f.write(podcast_script.full_dialogue)
                f.write(f"\n\n" + "="*50 + "\n")
                f.write(f"使用的文章來源:\n")
                for i, article in enumerate(crawled_articles, 1):
                    f.write(f"{i}. {article.title}\n")
                    f.write(f"   來源: {article.url}\n")
                    f.write(f"   發布: {article.published_at.strftime('%Y-%m-%d')}\n\n")
            
            print(f"✅ 腳本已保存至: {filename}")
        
        print()
        print("🎉 " + "="*60)
        print("🎉  任務完成！感謝使用 Hakkast 播客生成系統")
        print("🎉 " + "="*60)
        
    except Exception as e:
        print(f"❌ 發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """主程式進入點"""
    try:
        asyncio.run(interactive_podcast_generator())
    except KeyboardInterrupt:
        print("\n\n👋 用戶中斷，再見！")
    except Exception as e:
        print(f"\n❌ 系統錯誤: {str(e)}")

if __name__ == "__main__":
    main()