from crawl4ai import AsyncWebCrawler
from datetime import datetime
from app.models.crawler import CrawledContent, ContentType
from bs4 import BeautifulSoup
import requests
import re

def clean_markdown(md: str) -> str:
    """移除 markdown 中的 [文字](連結) 與多餘星號/空白行"""
    text = re.sub(r"\[.*?\]\(.*?\)", "", md)  # 移除 markdown 連結
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not re.fullmatch(r"[*\s]+", line)  
    ]
    return "\n".join(lines)

def extract_fallback_content(url: str) -> str:
    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        article = soup.select_one("div.td-post-content")
        if article:
            return article.get_text(separator="\n", strip=True)
    except Exception as e:
        print(f"Fallback 抓內容失敗：{e}")
    return ""

def extract_published_date(url: str) -> datetime:
    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        time_tag = soup.select_one("time.entry-date") or soup.select_one("div.td-module-meta-info time")
        if time_tag:
            if time_tag.has_attr("datetime"):
                return datetime.fromisoformat(time_tag["datetime"].replace("Z", "+00:00"))
            else:
                return datetime.strptime(time_tag.text.strip(), "%B %d, %Y")
    except Exception as e:
        print(f"擷取發佈時間失敗：{e}")
    return datetime.now()

def clean_content(raw_content: str) -> str:
    """移除社群連結&廣告"""
    markers = ["Facebook", "Twitter", "LinkedIn", "Print"]
    for marker in markers:
        idx = raw_content.find(marker)
        if idx != -1:
            raw_content = raw_content[:idx]
    return raw_content.strip()

async def crawl_news(topic: str, max_articles: int = 5):
    crawled = []
    ...
    if topic == "research_deep_learning":
        try:
            response = requests.get(_list_page_url_for_topic(topic), timeout=10)
            json_data = response.json()

            papers = json_data.get("data", {}).get("trending_papers", [])
            if not isinstance(papers, list):
                print("data.trending_papers 不是 list")
                return []

            print(f"原始資料共 {len(papers)} 筆")
            if papers:
                print("第一筆資料預覽：", papers[0])

            for item in papers[:max_articles]:
                paper_id = item.get("universal_paper_id")
                title = item.get("title", "No Title")
                abstract = item.get("abstract", "")
                summary_text = item.get("paper_summary", {}).get("summary", "")
                published = item.get("first_publication_date", None)

                url = f"https://alphaxiv.org/paper/{paper_id}"

                crawled.append(CrawledContent(
                    id=url,
                    title=title,
                    content=abstract,
                    summary=clean_markdown(summary_text)[:300],
                    url=url,
                    source="alphaxiv",
                    published_at=datetime.fromisoformat(published) if published else datetime.now(),
                    crawled_at=datetime.now(),
                    content_type=ContentType.RESEARCH,
                    topic=topic,
                    keywords=[],
                    relevance_score=0.0
                ))

                print(f"標題：{title}")
                print(f"連結：{url}")
                print(f"發佈：{published[:10] if published else '未知'}")
                print(f"摘要：{summary_text[:100]}")
                print("------")

        except Exception as e:
            print(f"抓 AlphaXiv API 失敗：{e}")

        print(f"共抓到 {len(crawled)} 筆資料")
        return crawled

    # crawl4ai 一般網頁
    list_page_url = _list_page_url_for_topic(topic)
    article_urls = _extract_article_links(list_page_url, limit=max_articles)

    async with AsyncWebCrawler() as crawler:
        for url in article_urls:
            result = await crawler.arun(url)

            title = result.metadata.get("title", "No title")
            markdown = getattr(result, "markdown", "")
            content = getattr(result, "content", "")

            raw_content = content if content and len(content.strip()) > 50 else extract_fallback_content(result.url)
            raw_content = clean_content(raw_content)  # << 新增這行
            raw_summary = raw_content if raw_content else markdown
            summary = clean_markdown(raw_summary).strip()[:300]
            published_time = extract_published_date(result.url)

            crawled.append(CrawledContent(
                id=result.url,
                title=title,
                content=raw_content,
                summary=summary,
                url=result.url,
                source="crawl4ai",
                published_at=published_time,
                crawled_at=datetime.now(),
                content_type=ContentType.NEWS,
                topic=topic,
                keywords=[],
                relevance_score=0.0
            ))

            print(f"標題：{title}")
            print(f"連結：{result.url}")
            print(f"發佈：{published_time.date()}")
            print(f"摘要：{summary}")
            print("------")

    print(f"共抓到 {len(crawled)} 筆資料")
    return crawled

def _list_page_url_for_topic(topic: str):
    return {
        "technology_news": "https://www.openaccessgovernment.org/category/open-access-news/technology-news/",
        "finance_economics": "https://www.openaccessgovernment.org/category/open-access-news/finance-news/",
        "research_deep_learning": "https://api.alphaxiv.org/v2/papers/trending-papers?page_num=1&sort_by=Hot&page_size=5",
    }.get(topic, "")

def _extract_article_links(list_page_url: str, limit: int = 5):
    try:
        response = requests.get(list_page_url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        links = []
        for a in soup.select("h3.entry-title > a"):
            href = a.get("href")
            if href and href.startswith("https://"):
                links.append(href)
            if len(links) >= limit:
                break
        return links
    except Exception as e:
        print(f"抓文章連結失敗：{e}")
        return []