import asyncio
import aiohttp
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
import re
import logging
from bs4 import BeautifulSoup
import feedparser
from difflib import SequenceMatcher

from ..models.crawler import (
    CrawlerSource, TopicCrawlerConfig, CrawledContent, 
    CrawlerResult, ContentType, CRAWLER_CONFIGS
)
from ..core.config import settings

logger = logging.getLogger(__name__)

class ContentCrawlerService:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.max_concurrent_requests = 5
        self.request_timeout = 30
        
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(limit=self.max_concurrent_requests)
        timeout = aiohttp.ClientTimeout(total=self.request_timeout)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'Hakkast-Crawler/1.0 (Educational Content Aggregator)'
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def crawl_topic_content(self, topic: str, max_articles: int = 10) -> CrawlerResult:
        """Crawl content for a specific topic"""
        start_time = datetime.utcnow()
        
        if topic not in CRAWLER_CONFIGS:
            # Try to find a matching config by keywords
            config = await self._find_best_config_for_topic(topic)
            if not config:
                logger.warning(f"No crawler configuration found for topic: {topic}")
                return CrawlerResult(
                    topic=topic,
                    total_found=0,
                    content_items=[],
                    crawl_duration=0.0,
                    sources_used=[],
                    errors=[f"No crawler configuration for topic: {topic}"]
                )
        else:
            config = CRAWLER_CONFIGS[topic]
        
        all_content: List[CrawledContent] = []
        errors: List[str] = []
        sources_used: List[str] = []
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        
        # Crawl all sources concurrently
        tasks = []
        for source in config.sources:
            task = self._crawl_source(semaphore, source, config, max_articles // len(config.sources))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_msg = f"Error crawling {config.sources[i].name}: {str(result)}"
                errors.append(error_msg)
                logger.error(error_msg)
            else:
                content_list, source_errors = result
                all_content.extend(content_list)
                errors.extend(source_errors)
                if content_list:
                    sources_used.append(config.sources[i].name)
        
        # Sort by relevance and publish date
        all_content.sort(key=lambda x: (x.relevance_score, x.published_at or datetime.min), reverse=True)
        
        # Limit to max articles and remove duplicates
        unique_content = await self._deduplicate_content(all_content[:max_articles])
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        return CrawlerResult(
            topic=topic,
            total_found=len(unique_content),
            content_items=unique_content,
            crawl_duration=duration,
            sources_used=sources_used,
            error_count=len(errors),
            errors=errors
        )
    
    async def _crawl_source(
        self, 
        semaphore: asyncio.Semaphore, 
        source: CrawlerSource, 
        config: TopicCrawlerConfig,
        max_articles: int
    ) -> tuple[List[CrawledContent], List[str]]:
        """Crawl a single source"""
        async with semaphore:
            try:
                await asyncio.sleep(source.rate_limit)  # Rate limiting
                
                content_items = []
                errors = []
                
                # Handle different source types
                if source.content_type == ContentType.RESEARCH and "arxiv" in str(source.base_url):
                    content_items = await self._crawl_arxiv(source, config, max_articles)
                elif "rss" in str(source.base_url).lower() or source.base_url.path.endswith('.xml'):
                    content_items = await self._crawl_rss_feed(source, config, max_articles)
                else:
                    content_items = await self._crawl_web_page(source, config, max_articles)
                
                return content_items, errors
                
            except Exception as e:
                error_msg = f"Failed to crawl {source.name}: {str(e)}"
                logger.error(error_msg)
                return [], [error_msg]
    
    async def _crawl_web_page(
        self, 
        source: CrawlerSource, 
        config: TopicCrawlerConfig, 
        max_articles: int
    ) -> List[CrawledContent]:
        """Crawl regular web pages"""
        content_items = []
        
        try:
            headers = source.headers or {}
            async with self.session.get(str(source.base_url), headers=headers) as response:
                if response.status != 200:
                    logger.warning(f"HTTP {response.status} for {source.name}")
                    return []
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract article links
                article_links = await self._extract_article_links(soup, source)
                
                # Limit the number of articles to crawl
                article_links = article_links[:min(max_articles, source.max_pages)]
                
                # Crawl individual articles
                for link in article_links:
                    try:
                        article_content = await self._crawl_article(link, source, config)
                        if article_content:
                            content_items.append(article_content)
                    except Exception as e:
                        logger.error(f"Error crawling article {link}: {e}")
                        continue
                
        except Exception as e:
            logger.error(f"Error crawling {source.name}: {e}")
        
        return content_items
    
    async def _crawl_arxiv(
        self, 
        source: CrawlerSource, 
        config: TopicCrawlerConfig, 
        max_articles: int
    ) -> List[CrawledContent]:
        """Crawl arXiv papers"""
        content_items = []
        
        try:
            # Use arXiv API for better results
            search_query = "+OR+".join(config.keywords[:3])  # Limit keywords for API
            api_url = f"http://export.arxiv.org/api/query?search_query=all:{search_query}&start=0&max_results={max_articles}&sortBy=lastUpdatedDate&sortOrder=descending"
            
            async with self.session.get(api_url) as response:
                if response.status != 200:
                    return []
                
                xml_content = await response.text()
                feed = feedparser.parse(xml_content)
                
                for entry in feed.entries[:max_articles]:
                    try:
                        # Calculate relevance score
                        relevance = await self._calculate_relevance(
                            entry.title + " " + entry.summary, 
                            config.keywords, 
                            config.exclude_keywords
                        )
                        
                        if relevance < 0.3:  # Skip low relevance papers
                            continue
                        
                        content_item = CrawledContent(
                            id=str(uuid.uuid4()),
                            title=entry.title,
                            content=entry.summary,
                            summary=entry.summary[:500] + "..." if len(entry.summary) > 500 else entry.summary,
                            url=entry.link,
                            source=source.name,
                            published_at=datetime.strptime(entry.published, "%Y-%m-%dT%H:%M:%SZ"),
                            crawled_at=datetime.utcnow(),
                            content_type=source.content_type,
                            topic=config.topic,
                            keywords=config.keywords,
                            relevance_score=relevance
                        )
                        content_items.append(content_item)
                        
                    except Exception as e:
                        logger.error(f"Error processing arXiv entry: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error crawling arXiv: {e}")
        
        return content_items
    
    async def _crawl_rss_feed(
        self, 
        source: CrawlerSource, 
        config: TopicCrawlerConfig, 
        max_articles: int
    ) -> List[CrawledContent]:
        """Crawl RSS feeds"""
        content_items = []
        
        try:
            async with self.session.get(str(source.base_url)) as response:
                if response.status != 200:
                    return []
                
                xml_content = await response.text()
                feed = feedparser.parse(xml_content)
                
                for entry in feed.entries[:max_articles]:
                    try:
                        # Calculate relevance
                        text_content = f"{entry.title} {getattr(entry, 'summary', '')}"
                        relevance = await self._calculate_relevance(
                            text_content, 
                            config.keywords, 
                            config.exclude_keywords
                        )
                        
                        if relevance < 0.3:
                            continue
                        
                        published_date = None
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            published_date = datetime(*entry.published_parsed[:6])
                        
                        content_item = CrawledContent(
                            id=str(uuid.uuid4()),
                            title=entry.title,
                            content=getattr(entry, 'summary', ''),
                            summary=getattr(entry, 'summary', '')[:300] + "...",
                            url=entry.link,
                            source=source.name,
                            published_at=published_date,
                            crawled_at=datetime.utcnow(),
                            content_type=source.content_type,
                            topic=config.topic,
                            keywords=config.keywords,
                            relevance_score=relevance
                        )
                        content_items.append(content_item)
                        
                    except Exception as e:
                        logger.error(f"Error processing RSS entry: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error crawling RSS feed: {e}")
        
        return content_items
    
    async def _extract_article_links(self, soup: BeautifulSoup, source: CrawlerSource) -> List[str]:
        """Extract article links from a webpage"""
        links = []
        
        # Common selectors for article links
        link_selectors = [
            'a[href*="/article"]',
            'a[href*="/story"]',
            'a[href*="/news"]',
            'a[href*="/post"]',
            '.article-link a',
            '.news-item a',
            'h2 a', 'h3 a',
            '.headline a'
        ]
        
        for selector in link_selectors:
            elements = soup.select(selector)
            for element in elements:
                href = element.get('href')
                if href:
                    if href.startswith('/'):
                        href = urljoin(str(source.base_url), href)
                    if href.startswith('http') and self._is_valid_article_url(href):
                        links.append(href)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_links = []
        for link in links:
            if link not in seen:
                seen.add(link)
                unique_links.append(link)
        
        return unique_links[:source.max_pages]
    
    def _is_valid_article_url(self, url: str) -> bool:
        """Check if URL looks like a valid article URL"""
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        # Skip common non-article paths
        skip_patterns = [
            '/category/', '/tag/', '/author/', '/search/', '/page/',
            '/login', '/register', '/subscribe', '/contact',
            '.jpg', '.png', '.gif', '.pdf', '.mp4'
        ]
        
        return not any(pattern in path for pattern in skip_patterns)
    
    async def _crawl_article(
        self, 
        url: str, 
        source: CrawlerSource, 
        config: TopicCrawlerConfig
    ) -> Optional[CrawledContent]:
        """Crawl individual article"""
        try:
            await asyncio.sleep(source.rate_limit)  # Rate limiting
            
            headers = source.headers or {}
            async with self.session.get(url, headers=headers) as response:
                if response.status != 200:
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract content using selectors
                title = self._extract_text(soup, source.selectors.get('title', 'h1'))
                content = self._extract_text(soup, source.selectors.get('content', 'article, .content, .post-content'))
                
                if not title or not content or len(content) < 100:
                    return None
                
                # Extract published date
                published_date = None
                if 'published' in source.selectors:
                    date_element = soup.select_one(source.selectors['published'])
                    if date_element:
                        published_date = self._parse_date(date_element.get_text().strip())
                
                # Calculate relevance
                text_for_analysis = f"{title} {content}"
                relevance = await self._calculate_relevance(
                    text_for_analysis, 
                    config.keywords, 
                    config.exclude_keywords
                )
                
                if relevance < 0.2:  # Skip low relevance content
                    return None
                
                # Generate summary
                summary = await self._generate_summary(content)
                
                return CrawledContent(
                    id=str(uuid.uuid4()),
                    title=title,
                    content=content,
                    summary=summary,
                    url=url,
                    source=source.name,
                    published_at=published_date,
                    crawled_at=datetime.utcnow(),
                    content_type=source.content_type,
                    topic=config.topic,
                    keywords=config.keywords,
                    relevance_score=relevance
                )
                
        except Exception as e:
            logger.error(f"Error crawling article {url}: {e}")
            return None
    
    def _extract_text(self, soup: BeautifulSoup, selector: str) -> str:
        """Extract text content using CSS selector"""
        try:
            elements = soup.select(selector)
            if elements:
                # Join text from all matching elements
                text = ' '.join(el.get_text().strip() for el in elements)
                # Clean up whitespace
                text = re.sub(r'\s+', ' ', text).strip()
                return text
        except Exception as e:
            logger.error(f"Error extracting text with selector '{selector}': {e}")
        return ""
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats"""
        date_patterns = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d",
            "%B %d, %Y",
            "%b %d, %Y",
            "%d %B %Y",
            "%d %b %Y"
        ]
        
        for pattern in date_patterns:
            try:
                return datetime.strptime(date_str, pattern)
            except ValueError:
                continue
        
        return None
    
    async def _calculate_relevance(
        self, 
        text: str, 
        keywords: List[str], 
        exclude_keywords: List[str]
    ) -> float:
        """Calculate relevance score based on keywords"""
        text_lower = text.lower()
        
        # Check for exclude keywords (immediate disqualification)
        for exclude_keyword in exclude_keywords:
            if exclude_keyword.lower() in text_lower:
                return 0.0
        
        # Calculate positive score based on keyword matches
        total_score = 0.0
        keyword_matches = 0
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            count = text_lower.count(keyword_lower)
            if count > 0:
                keyword_matches += 1
                # Score based on frequency and keyword length
                score = count * (len(keyword) / 10)  # Longer keywords get higher weight
                total_score += min(score, 1.0)  # Cap per-keyword score
        
        # Normalize score
        if keywords:
            relevance = (total_score / len(keywords)) * (keyword_matches / len(keywords))
            return min(relevance, 1.0)
        
        return 0.0
    
    async def _generate_summary(self, content: str, max_length: int = 300) -> str:
        """Generate a summary of the content"""
        # Simple extractive summary - take first few sentences
        sentences = re.split(r'[.!?]+', content)
        summary_sentences = []
        current_length = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if current_length + len(sentence) > max_length:
                break
            
            summary_sentences.append(sentence)
            current_length += len(sentence)
        
        summary = '. '.join(summary_sentences)
        if len(summary) < len(content):
            summary += "..."
        
        return summary or content[:max_length] + "..."
    
    async def _deduplicate_content(self, content_list: List[CrawledContent]) -> List[CrawledContent]:
        """Remove duplicate content based on title similarity"""
        unique_content = []
        seen_titles = []
        
        for content in content_list:
            is_duplicate = False
            for seen_title in seen_titles:
                similarity = SequenceMatcher(None, content.title.lower(), seen_title.lower()).ratio()
                if similarity > 0.8:  # 80% similarity threshold
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_content.append(content)
                seen_titles.append(content.title)
        
        return unique_content
    
    async def _find_best_config_for_topic(self, topic: str) -> Optional[TopicCrawlerConfig]:
        """Find the best matching crawler configuration for a topic"""
        topic_lower = topic.lower()
        
        # Direct keyword matching
        for config_topic, config in CRAWLER_CONFIGS.items():
            for keyword in config.keywords:
                if keyword.lower() in topic_lower:
                    return config
        
        # Fuzzy matching on config topic names
        best_match = None
        best_score = 0.0
        
        for config_topic, config in CRAWLER_CONFIGS.items():
            similarity = SequenceMatcher(None, topic_lower, config_topic.lower()).ratio()
            if similarity > best_score and similarity > 0.5:  # 50% similarity threshold
                best_score = similarity
                best_match = config
        
        return best_match