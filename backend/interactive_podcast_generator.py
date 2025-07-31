#!/usr/bin/env python3
"""
Hakkast 互動式播客生成系统
用戶可選擇主題 → 爬取相關文章 → AI生成播客腳本
"""

import asyncio
from app.services.crawl4ai_service import crawl_news
#from app.services.pydantic_ai_service import PydanticAIService
#from app.models.podcast import PodcastGenerationRequest
from app.services.ai_service import AIService
import json
from app.services.translation_service import TranslationService

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
        print(f"{key}. {value['name']}")
        print(f"{value['description']}")
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
        # 選擇腔調
        print("請選擇客語腔調：")
        print("1. 四縣腔")
        print("2. 海陸腔")
        while True:
            dialect_choice = input("請輸入選項: ").strip()
            if dialect_choice == "1":
                dialect = "sihxian"
                break
            elif dialect_choice == "2":
                dialect = "hailu"
                break
            else:
                print("無效選項，請輸入 1 或 2")
                continue

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
            print(f"授權網址: {getattr(article, 'license_url', '')}")
            print(f"授權類型: {getattr(article, 'license_type', '')}")
            print()
        
        # 確認是否繼續生成腳本
        continue_choice = input("是否要繼續生成腳本？(y/N): ").strip().lower()
        
        if continue_choice not in ['y', 'yes', '是']:
            print("任務完成")
            return
        
        print("開始生成腳本...")

        # 使用第一篇文章的標題為主標題
        main_title = crawled_articles[0].title
        
        # 合併文章內容
        combined_content = "\n\n".join([
            f"標題: {article.title}\n內容: {article.content or article.summary}\n來源: {article.url}"
            for article in crawled_articles
        ])
        
        # 產生腳本
        ai_service = AIService()
        result = await ai_service.generate_podcast_script_with_agents(crawled_articles, max_minutes=25)
        
        # 從返回的字典中取出原始腳本
        podcast_script = result["original_script"]
        print("\n腳本生成完成")
        print("進行客語翻譯...")

        # 傳 dialect 給 add_hakka_translation_to_script
        podcast_script = await add_hakka_translation_to_script(podcast_script, dialect=dialect)
        print("翻譯完成")
        print(podcast_script.model_dump_json(indent=2))
       
        print(f"腳本字數：{len(podcast_script.content)}")
        print("\n完整播客腳本：\n")
        for item in podcast_script.content:
            print(f"{item.speaker}: {item.text} -> {item.hakka_text}")

        # 儲存腳本
        save_choice = input("是否要保存腳本到文件？(y/N): ").strip().lower()
        
        if save_choice in ['y', 'yes', '是']:
            import os
            # 確保 json 資料夾存在
            json_dir = "json"
            os.makedirs(json_dir, exist_ok=True)
            
            filename = f"podcast_script_{topic_key}_{len(crawled_articles)}articles.json"
            filepath = os.path.join(json_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(podcast_script.model_dump_json(indent=2))
            print(f"腳本已保存至: {filepath}")
        
        print("bye")
     
    except Exception as e:
        print(f"發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()

#將 content 裡 text 翻譯成客語漢字，並產生羅馬拼音（四縣腔/海陸腔）
async def add_hakka_translation_to_script(podcast_script, dialect="sihxian"):
    service = TranslationService()
    ai_service = AIService()
    
    for item in podcast_script.content:
        if not service.headers:
            await service.login()
        result = await service.translate_chinese_to_hakka(item.text, dialect=dialect)
        item.hakka_text = result.get("hakka_text", "")
        item.romanization = result.get("romanization", "")
        item.romanization_tone = result.get("romanization_tone", "")
        
        # 🔧 英文轉羅馬拼音處理 - 解決TTS標調問題
        if item.romanization:
            print(f"處理羅馬拼音中的英文單字: {item.romanization}")
            try:
                # 使用AI Service處理英文單字轉換
                processed_romanization = await ai_service.process_romanization_for_tts(item.romanization)
                item.romanization = processed_romanization
                print(f"轉換完成: {processed_romanization}")
            except Exception as e:
                print(f"羅馬拼音處理失敗: {str(e)}")
                # 保持原始romanization，不中斷流程
    
    await service.close()
    return podcast_script

def main():
    try:
        asyncio.run(interactive_podcast_generator())
    except KeyboardInterrupt:
        print("\n\n用戶中斷")
    except Exception as e:
        print(f"\n系統錯誤: {str(e)}")

if __name__ == "__main__":
    main()