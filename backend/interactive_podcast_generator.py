#!/usr/bin/env python3
"""
Hakkast 互動式播客生成系统
用戶可選擇主題 → 爬取相關文章 → AI生成播客腳本
"""

import asyncio
from app.services.crawl4ai_service import crawl_news
from app.services.pydantic_ai_service import PydanticAIService
from app.models.podcast import PodcastGenerationRequest
from agents import generate_podcast_script_with_agents
import json

TOPIC_OPTIONS = {
    "1": {
        "key": "technology_news",
        "name": "Technology",
        "description": "Latest technology trends, AI, cloud computing, digital transformation, and related topics."
    },
    "2": {
        "key": "finance_economics", 
        "name": "Finance",
        "description": "Financial markets, economic policies, investment trend analysis."
    },
    "3": {
        "key": "research_deep_learning",
        "name": "AI Research",
        "description": "Latest AI research papers and breakthroughs in machine learning."
    }
}

async def interactive_podcast_generator():
    """
    互動式播客生成主程式
    """

    print("歡迎使用 Hakkast")

    # 顯示主題選項
    print("請選擇你想要的主題：")
    print()
    for key, value in TOPIC_OPTIONS.items():
        print(f"   {key}. {value['name']}")
        print(f"      {value['description']}")
        print()
    
    # user選擇主題
    while True:
        choice = input("請輸入選項 (1-3) 或 'q' 退出: ").strip()
        
        if choice.lower() == 'q':
            print("感謝使用 Hakkast")
            return
        
        if choice in TOPIC_OPTIONS:
            selected_topic = TOPIC_OPTIONS[choice]
            break
        else:
            print("無效選項，請輸入 1、2、3 或 'q'")
            continue
        
    print(f"已選擇主題: {selected_topic['name']}")

    
    # 爬蟲*3
    start_crawl = input("是否開始爬取新聞？(y/N): ").strip().lower()
    if start_crawl not in ['y', 'yes', '是']:
        print("任務完成！")
        return

    max_articles = 3
    topic_key = selected_topic['key']

    print(f"開始爬取 {selected_topic['name']} 相關文章...")

    
    # 爬取新聞
    try:
        crawled_articles = await crawl_news(topic_key, max_articles)
        
        if not crawled_articles:
            print("沒有抓到任何文章，請稍後再試")
            return
        

        print(f"成功爬取 {len(crawled_articles)} 篇文章")
 
        
        # 顯示爬取結果
        for i, article in enumerate(crawled_articles, 1):
            print(f"{i}. {article.title}")
            print(f"來源: {article.source}")
            print(f"發佈日期: {article.published_at.strftime('%Y-%m-%d')}")
            print(f"摘要: {article.summary[:100]}...")
            print()
        
        # 確認是否繼續生成播客
        continue_choice = input("是否要繼續生成腳本？(y/N): ").strip().lower()
        
        if continue_choice not in ['y', 'yes', '是']:
            print("任務完成")
            return
        
        print("開始生成腳本...")

        # 使用第一篇文章的標題為主標題
        main_title = crawled_articles[0].title
        
        # 合併所有文章內容
        combined_content = "\n\n".join([
            f"標題: {article.title}\n內容: {article.content or article.summary}\n來源: {article.url}"
            for article in crawled_articles
        ])
        
        # 產生腳本
        podcast_script = await generate_podcast_script_with_agents(crawled_articles, max_minutes=25)
        print("\n腳本生成完成")
        
        # <<<<<<<<<<< 新增這段，清楚印出 dict 結構 >>>>>>>>>>
        print("\n[PodcastScript 結構化 dict 輸出]")
        print(json.dumps(podcast_script, ensure_ascii=False, indent=2))
        # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

        print(f"腳本字數：{len(podcast_script['content'])}")
        print("\n完整播客腳本：\n")
        print(podcast_script['content'])
        
        # 儲存腳本
        save_choice = input("是否要保存腳本到文件？(y/N): ").strip().lower()
        
        if save_choice in ['y', 'yes', '是']:
            filename = f"podcast_script_{topic_key}_{len(crawled_articles)}articles.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(podcast_script, f, ensure_ascii=False, indent=2)
            print(f"腳本已保存至: {filename}")
        

        print("bye")

        
    except Exception as e:
        print(f"發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    try:
        asyncio.run(interactive_podcast_generator())
    except KeyboardInterrupt:
        print("\n\n用戶中斷")
    except Exception as e:
        print(f"\n系統錯誤: {str(e)}")

if __name__ == "__main__":
    main()