from crawl4ai import AsyncWebCrawler
from datetime import datetime
from app.models.crawler import CrawledContent, ContentType
from bs4 import BeautifulSoup
import requests
import re
import xml.etree.ElementTree as ET
import logging

logger = logging.getLogger(__name__)

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
    """Optimized news crawling function with better error handling and structure"""
    if topic == "research_deep_learning":
        return await _crawl_research_papers(topic, max_articles)
    
    # Handle general web crawling
    return await _crawl_general_news(topic, max_articles)

async def _crawl_research_papers(topic: str, max_articles: int):
    """Crawl research papers from AlphaXiv API"""
    crawled = []
    
    try:
        found = 0
        page_num = 1
        page_size = 50
        
        while found < max_articles:
            api_url = f"https://api.alphaxiv.org/v2/papers/trending-papers?page_num={page_num}&sort_by=Hot&page_size={page_size}"
            
            try:
                response = requests.get(api_url, timeout=20)
                response.raise_for_status()
                json_data = response.json()
            except requests.RequestException as e:
                logger.error(f"API request failed: {e}")
                break
            except ValueError as e:
                logger.error(f"Invalid JSON response: {e}")
                break
            
            papers = json_data.get("data", {}).get("trending_papers", [])
            if not isinstance(papers, list) or not papers:
                if found == 0:
                    logger.info("No CC licensed papers found")
                break

            logger.info(f"Page {page_num}: {len(papers)} papers found")
            
            for item in papers:
                if found >= max_articles:
                    break
                    
                try:
                    paper_data = _extract_paper_data(item)
                    if not paper_data:
                        continue
                        
                    license_url = get_arxiv_license(paper_data['arxiv_id'])
                    if not is_usable_license(license_url):
                        logger.debug(f"Skipping non-CC paper: {paper_data['arxiv_id']}")
                        continue

                    content_item = _create_research_content_item(paper_data, topic, license_url)
                    crawled.append(content_item)
                    found += 1
                    
                    logger.info(f"Added paper: {paper_data['title'][:50]}...")
                    
                except Exception as e:
                    logger.error(f"Failed to process paper: {e}")
                    continue
                    
            page_num += 1

        logger.info(f"Successfully crawled {len(crawled)} research papers")
        return crawled

    except Exception as e:
        logger.error(f"Research crawling failed: {e}")
        return []

async def _crawl_general_news(topic: str, max_articles: int):
    """Crawl general news articles"""
    crawled = []
    
    try:
        list_page_url = _list_page_url_for_topic(topic)
        if not list_page_url:
            logger.error(f"No URL configured for topic: {topic}")
            return []
            
        article_urls = _extract_article_links(list_page_url, limit=max_articles)
        if not article_urls:
            logger.warning(f"No article URLs found for topic: {topic}")
            return []

        async with AsyncWebCrawler() as crawler:
            for url in article_urls:
                try:
                    result = await crawler.arun(url)
                    content_item = _create_news_content_item(result, topic)
                    crawled.append(content_item)
                    
                    logger.info(f"Added news: {content_item.title[:50]}...")
                    
                except Exception as e:
                    logger.error(f"Failed to crawl URL {url}: {e}")
                    continue

        logger.info(f"Successfully crawled {len(crawled)} news articles")
        return crawled
        
    except Exception as e:
        logger.error(f"General news crawling failed: {e}")
        return []

def _extract_paper_data(item):
    """Extract paper data from API response"""
    try:
        paper_id = item.get("universal_paper_id")
        if not paper_id:
            return None
            
        return {
            'arxiv_id': paper_id,
            'title': item.get("title", "No Title"),
            'abstract': item.get("abstract", ""),
            'summary_text': item.get("paper_summary", {}).get("summary", ""),
            'published': item.get("first_publication_date")
        }
    except Exception as e:
        logger.error(f"Failed to extract paper data: {e}")
        return None

def _create_research_content_item(paper_data, topic, license_url):
    """Create CrawledContent item for research paper"""
    arxiv_id = paper_data['arxiv_id']
    html_content = fetch_arxiv_html_content(arxiv_id)
    url = f"https://arxiv.org/abs/{arxiv_id}"
    
    published_at = None
    if paper_data['published']:
        try:
            published_at = datetime.fromisoformat(paper_data['published'])
        except ValueError:
            published_at = datetime.now()
    
    return CrawledContent(
        id=url,
        title=paper_data['title'],
        content=html_content or paper_data['abstract'],
        summary=clean_markdown(paper_data['summary_text'])[:300],
        url=url,
        source="arxiv",
        published_at=published_at or datetime.now(),
        crawled_at=datetime.now(),
        content_type=ContentType.RESEARCH,
        topic=topic,
        keywords=[],
        relevance_score=0.0,
        license_url=license_url,
        license_type=parse_license_type(license_url)
    )

def _create_news_content_item(result, topic):
    """Create CrawledContent item for news article"""
    title = result.metadata.get("title", "No title")
    markdown = getattr(result, "markdown", "")
    content = getattr(result, "content", "")

    raw_content = content if content and len(content.strip()) > 50 else extract_fallback_content(result.url)
    raw_content = clean_content(raw_content)  
    raw_summary = raw_content if raw_content else markdown
    summary = clean_markdown(raw_summary).strip()[:300]
    published_time = extract_published_date(result.url)

    return CrawledContent(
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
    )

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