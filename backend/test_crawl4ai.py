import asyncio
from app.services.crawl4ai_service import crawl_news

TOPIC_OPTIONS = {
    "1": "technology_news",
    "2": "finance_economics",
    "3": "research_deep_learning"
}

async def test_crawl():
    print("Select the topic to crawl:")
    print("1. Tech")
    print("2. Finance")
    print("3. Research")

    choice = input("Please enter 1, 2, or 3:\n> ").strip()
    topic = TOPIC_OPTIONS.get(choice)

    if topic:
        print(f"\n🔍 Crawling topic: {topic}")
        try:
            articles = await crawl_news(topic, max_articles=3)
            if articles:
                print(f"Success, Crawled {len(articles)} articles.")
                for i, article in enumerate(articles, 1):
                    print(f"   {i}. {article.title}")
                    print(f"   Content:\n{article.content}\n{'-'*40}")
            else:
                print("No articles found.")
        except Exception as e:
            print(f"Error: {str(e)}")
    else:
        print("Invalid option.")

if __name__ == "__main__":
    asyncio.run(test_crawl())
