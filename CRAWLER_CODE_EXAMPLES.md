# 爬蟲整合範例代碼

## 1. 擴展後的爬蟲資料模型

```python
# app/models/crawler.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class CrawledContent(BaseModel):
    """擴展的爬蟲內容模型"""
    title: str                              # 新聞標題
    summary: str                            # 新聞摘要 (AI 生成或提取前幾句)
    content: str                            # 完整新聞內容
    url: str                                # 原始網址
    published_date: Optional[datetime]      # 發布時間
    source: str                             # 新聞來源 (網站名稱)
    category: Optional[str] = "general"     # 新聞分類
    keywords: List[str] = []                # 關鍵詞列表
    language: str = "zh-tw"                 # 語言代碼
    crawl_timestamp: datetime               # 爬取時間戳
    content_hash: str                       # 內容雜湊值 (用於去重)
    word_count: int                         # 文字數量
    quality_score: float = 0.0              # 內容品質評分 (0-1)

class CrawlRequest(BaseModel):
    """爬蟲請求模型"""
    keywords: Optional[List[str]] = None    # 關鍵詞搜尋
    urls: Optional[List[str]] = None        # 指定 URL 列表  
    sources: Optional[List[str]] = None     # 指定新聞來源
    max_results: int = 10                   # 最大結果數量
    days_back: int = 7                      # 搜尋幾天內的新聞
    min_word_count: int = 200               # 最小字數要求
```

## 2. 爬蟲服務框架

```python
# app/services/crawler_service.py
import asyncio
import hashlib
from typing import List, Optional
from datetime import datetime, timedelta
import httpx
from bs4 import BeautifulSoup
import jieba
from collections import Counter

from app.models.crawler import CrawledContent, CrawlRequest

class CrawlerService:
    """新聞爬蟲服務"""
    
    def __init__(self):
        self.session = httpx.AsyncClient(
            timeout=30.0,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        self.supported_sources = {
            'cna': 'https://www.cna.com.tw',
            'ltn': 'https://news.ltn.com.tw', 
            'udn': 'https://udn.com',
            # 更多新聞源...
        }
    
    async def crawl_by_keywords(self, request: CrawlRequest) -> List[CrawledContent]:
        """根據關鍵詞爬取新聞"""
        results = []
        
        # 對每個支援的新聞源進行搜尋
        for source_name, base_url in self.supported_sources.items():
            if not request.sources or source_name in request.sources:
                try:
                    source_results = await self._crawl_source_by_keywords(
                        source_name, base_url, request.keywords
                    )
                    results.extend(source_results)
                except Exception as e:
                    print(f"爬取 {source_name} 失敗: {e}")
                    
        # 過濾、去重、評分
        filtered_results = self._filter_and_process(results, request)
        return filtered_results[:request.max_results]
    
    async def crawl_from_urls(self, urls: List[str]) -> List[CrawledContent]:
        """從指定 URL 列表爬取內容"""
        tasks = [self._crawl_single_url(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 過濾掉異常結果
        valid_results = [r for r in results if isinstance(r, CrawledContent)]
        return valid_results
    
    async def _crawl_single_url(self, url: str) -> Optional[CrawledContent]:
        """爬取單一 URL"""
        try:
            response = await self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取內容 (這裡需要針對不同網站客製化)
            title = self._extract_title(soup)
            content = self._extract_content(soup)
            
            if not title or not content or len(content) < 200:
                return None
                
            # 生成摘要
            summary = self._generate_summary(content)
            
            # 提取關鍵詞
            keywords = self._extract_keywords(f"{title} {content}")
            
            return CrawledContent(
                title=title,
                summary=summary,
                content=content,
                url=url,
                published_date=self._extract_date(soup),
                source=self._identify_source(url),
                keywords=keywords,
                crawl_timestamp=datetime.now(),
                content_hash=self._calculate_hash(content),
                word_count=len(content),
                quality_score=self._calculate_quality_score(title, content)
            )
            
        except Exception as e:
            print(f"爬取 {url} 失敗: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取標題 (需針對不同網站客製化)"""
        # 通用標題選擇器
        selectors = ['h1', '.title', '.headline', 'title']
        for selector in selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                return element.get_text(strip=True)
        return ""
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """提取正文內容 (需針對不同網站客製化)"""
        # 通用內容選擇器
        selectors = ['.content', '.article-body', '.post-content', 'article']
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                # 清理內容
                return self._clean_content(element.get_text())
        return ""
    
    def _clean_content(self, content: str) -> str:
        """清理內容"""
        import re
        # 移除多餘空白
        content = re.sub(r'\s+', ' ', content)
        # 移除特殊字符
        content = re.sub(r'[^\w\s\u4e00-\u9fff，。！？；：「」『』（）\[\]《》]', '', content)
        return content.strip()
    
    def _generate_summary(self, content: str, max_length: int = 200) -> str:
        """生成摘要 (取前幾句)"""
        import re
        sentences = re.split(r'[。！？]', content)
        summary = ""
        for sentence in sentences:
            if len(summary + sentence) <= max_length:
                summary += sentence + "。"
            else:
                break
        return summary.strip()
    
    def _extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """提取關鍵詞"""
        # 使用 jieba 分詞
        words = jieba.lcut(text)
        
        # 過濾停用詞和短詞
        stop_words = {'的', '是', '在', '了', '和', '與', '或', '但', '而'}
        filtered_words = [w for w in words if len(w) >= 2 and w not in stop_words]
        
        # 計算詞頻
        word_freq = Counter(filtered_words)
        
        # 返回最頻繁的關鍵詞
        return [word for word, freq in word_freq.most_common(top_n)]
    
    def _calculate_hash(self, content: str) -> str:
        """計算內容雜湊值"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _calculate_quality_score(self, title: str, content: str) -> float:
        """計算內容品質評分"""
        score = 0.0
        
        # 根據長度評分
        if len(content) > 500:
            score += 0.3
        elif len(content) > 200:
            score += 0.2
            
        # 根據標題品質評分
        if len(title) > 10 and len(title) < 100:
            score += 0.2
            
        # 根據內容結構評分 (有段落分隔)
        if '。' in content and content.count('。') > 3:
            score += 0.3
            
        # 其他品質指標...
        score += 0.2  # 基礎分
        
        return min(score, 1.0)
    
    def _filter_and_process(self, contents: List[CrawledContent], request: CrawlRequest) -> List[CrawledContent]:
        """過濾和處理結果"""
        # 過濾字數不足的內容
        contents = [c for c in contents if c.word_count >= request.min_word_count]
        
        # 去重 (根據內容雜湊)
        seen_hashes = set()
        unique_contents = []
        for content in contents:
            if content.content_hash not in seen_hashes:
                seen_hashes.add(content.content_hash)
                unique_contents.append(content)
        
        # 按品質評分排序
        unique_contents.sort(key=lambda x: x.quality_score, reverse=True)
        
        return unique_contents

# 使用範例
async def example_usage():
    crawler = CrawlerService()
    
    # 關鍵詞搜尋
    request = CrawlRequest(
        keywords=["菲律賓", "南海", "美國"],
        max_results=5,
        days_back=7
    )
    
    results = await crawler.crawl_by_keywords(request)
    print(f"找到 {len(results)} 篇相關新聞")
    
    for article in results:
        print(f"標題: {article.title}")
        print(f"來源: {article.source}")
        print(f"關鍵詞: {', '.join(article.keywords)}")
        print(f"品質評分: {article.quality_score}")
        print("-" * 50)
```

## 3. 與播客生成的整合範例

```python
# integration_example.py
async def generate_podcast_from_keywords(keywords: List[str]) -> Dict[str, Any]:
    """從關鍵詞生成播客的完整流程"""
    
    # Step 1: 爬取相關新聞
    crawler = CrawlerService()
    crawl_request = CrawlRequest(
        keywords=keywords,
        max_results=3,  # 限制 3 篇最相關的新聞
        min_word_count=300
    )
    
    crawled_content = await crawler.crawl_by_keywords(crawl_request)
    
    if not crawled_content:
        return {"error": "未找到相關新聞內容"}
    
    # Step 2: 準備播客主題
    main_topics = []
    all_keywords = set()
    
    for content in crawled_content:
        main_topics.append(content.title)
        all_keywords.update(content.keywords)
    
    # 組合主題
    topic = f"基於最新新聞的深度分析: {', '.join(main_topics[:2])}"  # 使用前兩個標題
    
    # Step 3: 生成播客
    ai_service = PydanticAIService(use_twcc=True)
    
    podcast_request = PodcastGenerationRequest(
        topic=topic,
        tone="educational",
        duration=18
    )
    
    result = await ai_service.generate_complete_podcast_content(
        podcast_request,
        crawled_content=crawled_content
    )
    
    # Step 4: 添加爬蟲資訊到結果
    if result.get("success"):
        result["source_articles"] = [
            {
                "title": content.title,
                "url": content.url,
                "source": content.source,
                "published_date": content.published_date,
                "keywords": content.keywords
            }
            for content in crawled_content
        ]
    
    return result

# API 路由範例
@router.post("/generate-from-news")
async def generate_podcast_from_news(keywords: List[str]):
    """從新聞關鍵詞生成播客的 API 端點"""
    result = await generate_podcast_from_keywords(keywords)
    return result
```

這個框架為您的朋友提供了：

1. **完整的資料模型**：支援所有必要的新聞資訊
2. **可擴展的爬蟲架構**：容易添加新的新聞來源
3. **智能內容處理**：自動去重、評分、關鍵詞提取
4. **與 AI 系統的整合**：直接對接現有的播客生成功能

您的朋友可以基於這個框架開始開發，逐步完善各個功能模組。
