import asyncio
from app.services.crawl4ai_service import crawl_news

TOPIC_OPTIONS = {
    "1": "technology_news",
    "2": "finance_economics",
    "3": "research_deep_learning"
}

if __name__ == "__main__":
    print("Select the topic to crawl:")
    print("1. Tech")
    print("2. Finance")
    print("3. Research")

    choice = input("Please enter 1, 2, or 3:：\n> ").strip()

    topic = TOPIC_OPTIONS.get(choice)

    if topic:
        asyncio.run(crawl_news(topic, max_articles=3))
    else:
        print("error")
