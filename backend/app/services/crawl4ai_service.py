from crawl4ai import AsyncWebCrawler
from datetime import datetime
from app.models.crawler import CrawledContent, ContentType
from bs4 import BeautifulSoup
import requests
import re
import xml.etree.ElementTree as ET

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
        res = requests.get(url, timeout=20)
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

def get_arxiv_license(arxiv_id: str) -> str:
    # 用 API
    api_url = f"https://export.arxiv.org/api/query?id_list={arxiv_id}"
    try:
        res = requests.get(api_url, timeout=10)
        root = ET.fromstring(res.text)
        ns = {'arxiv': 'https://arxiv.org/schemas/atom'}
        license_elem = root.find('.//arxiv:license', ns)
        if license_elem is not None and license_elem.text:
            return license_elem.text
    except Exception as e:
        print(f"查詢 arXiv API license 失敗：{e}")

    # 若 API 無，爬網頁
    try:
        url = f"https://arxiv.org/abs/{arxiv_id}"
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        # 抓網頁右邊的 license 
        license_tag = soup.select_one('div.abs-license a')
        if license_tag and license_tag.get('href', '').startswith('http'):
            return license_tag['href']
    except Exception as e:
        print(f"爬 arXiv 網頁 license 失敗：{e}")

    return ""

def fetch_arxiv_html_content(arxiv_id: str) -> str:
    """抓 arXiv 論文 HTML 摘要"""
    url = f"https://arxiv.org/abs/{arxiv_id}"
    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        abstract = soup.select_one("blockquote.abstract")
        return abstract.get_text(separator="\n", strip=True) if abstract else ""
    except Exception as e:
        print(f"抓 arXiv HTML 失敗：{e}")
        return ""

def get_arxiv_html_url(arxiv_id: str) -> str:
    """回傳 arXiv HTML 全文網址"""
    return f"https://arxiv.org/html/{arxiv_id}"

def fetch_arxiv_full_html(arxiv_id: str) -> str:
    """抓 arXiv HTML 全文"""
    html_url = get_arxiv_html_url(arxiv_id)
    try:
        res = requests.get(html_url, timeout=15)
        res.encoding = "utf-8"
        return res.text
    except Exception as e:
        print(f"抓 arXiv HTML 全文失敗：{e}")
        return ""

#cc授權相關，可去test_arxiv_html.py test
def parse_license_type(license_url: str) -> str:
    if "by-nc-sa" in license_url:
        return "CC BY-NC-SA"
    if "by-sa" in license_url:
        return "CC BY-SA"
    if "by-nc" in license_url:
        return "CC BY-NC"
    if "by" in license_url:
        return "CC BY"
    return "Other"

def is_usable_license(license_url: str) -> bool:
    # 允許 CC BY、CC BY-SA、CC BY-NC、CC BY-NC-SA(目前設定:允許非商業，不確定之後再修...)
    return (
        "creativecommons.org" in license_url
        and "nd" not in license_url
    )

async def crawl_news(topic: str, max_articles: int = 3):
    crawled = []
    ...
    if topic == "research_deep_learning":
        try:
            found = 0
            page_num = 1
            page_size = 50
            while found < max_articles:
                api_url = f"https://api.alphaxiv.org/v2/papers/trending-papers?page_num={page_num}&sort_by=Hot&page_size={page_size}"
                response = requests.get(api_url, timeout=20)
                json_data = response.json()
                papers = json_data.get("data", {}).get("trending_papers", [])
                if not isinstance(papers, list) or not papers:
                    if found == 0:
                        print("沒有找到 CC 授權論文。")
                    break

                if page_num == 1:
                    print(f"原始資料共 {len(papers)} 筆")
                    print("第一筆資料預覽：", papers[0])

                print(f"page_num={page_num}, 本頁有 {len(papers)} 篇")
                for item in papers:
                    if found >= max_articles:
                        break
                    paper_id = item.get("universal_paper_id")
                    title = item.get("title", "No Title")
                    abstract = item.get("abstract", "")
                    summary_text = item.get("paper_summary", {}).get("summary", "")
                    published = item.get("first_publication_date", None)

                    arxiv_id = paper_id
                    license_url = get_arxiv_license(arxiv_id)
                    print(f"{arxiv_id} license_url={license_url}")
                    if not is_usable_license(license_url):
                        print(f"跳過非 CC 授權論文：{arxiv_id}")
                        continue

                    html_content = fetch_arxiv_html_content(arxiv_id)
                    url = f"https://arxiv.org/abs/{arxiv_id}"

                    crawled.append(CrawledContent(
                        id=url,
                        title=title,
                        content=html_content or abstract,
                        summary=clean_markdown(summary_text)[:300],
                        url=url,
                        source="arxiv",
                        published_at=datetime.fromisoformat(published) if published else datetime.now(),
                        crawled_at=datetime.now(),
                        content_type=ContentType.RESEARCH,
                        topic=topic,
                        keywords=[],
                        relevance_score=0.0,
                        license_url=license_url,
                        license_type=parse_license_type(license_url)
                    ))
                    found += 1

                    print(f"標題：{title}")
                    print(f"連結：{url}")
                    print(f"授權：{license_url}")
                    print(f"發佈：{published[:10] if published else '未知'}")
                    print(f"摘要：{summary_text[:100]}")
                    print("------")
                page_num += 1

            print(f"共抓到 {len(crawled)} 筆資料")
            return crawled

        except Exception as e:
            print(f"抓 AlphaXiv API 失敗：{e}")
            return []

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
            raw_content = clean_content(raw_content)  
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