from app.services.crawl4ai_service import crawl_news, fetch_arxiv_full_html
import asyncio

def test_crawl_and_fetch_full_html(topic: str, max_articles: int = 3):
    articles = asyncio.run(crawl_news(topic, max_articles))
    print(f"共抓到 {len(articles)} 篇論文")
    for i, article in enumerate(articles, 1):
        print(f"\n第{i}篇：{article.title}")
        print(f"授權網址: {getattr(article, 'license_url', '')}")
        print(f"授權類型: {getattr(article, 'license_type', '')}")
        print(f"摘要內容:\n{article.content[:300]}...")
        # 取得全文 HTML
        arxiv_id = str(article.url).split('/')[-1]
        full_html = fetch_arxiv_full_html(arxiv_id)
        print(f"全文 HTML 前500字:\n{full_html[:500]}...")

if __name__ == "__main__":
    test_crawl_and_fetch_full_html("research_deep_learning", max_articles=3)