# 爬蟲開發待辦清單和測試指南

## 📝 開發待辦清單

### Phase 1: 基礎架構 ✅ (已提供範例代碼)
- [x] 擴展 `CrawledContent` 模型
- [x] 建立 `CrawlerService` 基礎架構
- [x] 設計整合介面

### Phase 2: 核心功能開發
- [ ] **實現基本爬蟲功能**
  - [ ] 單一 URL 內容提取
  - [ ] HTTP 請求處理和錯誤恢復
  - [ ] HTML 解析和內容清理
  - [ ] 基本的內容品質檢查

- [ ] **新聞網站適配器**
  - [ ] 中央社 (CNA) 適配器
  - [ ] 自由時報 (LTN) 適配器  
  - [ ] 聯合報 (UDN) 適配器
  - [ ] 通用 RSS 解析器

- [ ] **內容處理功能**
  - [ ] 中文分詞和關鍵詞提取
  - [ ] 內容摘要自動生成
  - [ ] 重複內容檢測
  - [ ] 內容品質評分系統

### Phase 3: 高級功能
- [ ] **搜尋功能**
  - [ ] 關鍵詞搜尋實現
  - [ ] 日期範圍過濾
  - [ ] 多來源並行爬取
  - [ ] 結果排序和篩選

- [ ] **效能優化**
  - [ ] 非同步並發處理
  - [ ] 請求速率限制
  - [ ] 快取機制
  - [ ] 資料庫儲存 (可選)

### Phase 4: API 和整合
- [ ] **REST API 端點**
  - [ ] `/crawl/keywords` - 關鍵詞搜尋
  - [ ] `/crawl/urls` - URL 列表爬取
  - [ ] `/crawl/sources` - 支援的來源列表
  - [ ] `/generate-from-news` - 新聞轉播客

- [ ] **整合測試**
  - [ ] 爬蟲→AI 播客生成管線測試
  - [ ] 錯誤處理測試
  - [ ] 效能負載測試

## 🧪 測試指南

### 1. 單元測試範例

```python
# tests/test_crawler_service.py
import pytest
from app.services.crawler_service import CrawlerService
from app.models.crawler import CrawlRequest

@pytest.mark.asyncio
async def test_crawl_single_url():
    """測試單一 URL 爬取"""
    crawler = CrawlerService()
    
    # 測試一個已知的新聞 URL
    test_url = "https://www.cna.com.tw/news/aipl/202307220001.aspx"
    result = await crawler._crawl_single_url(test_url)
    
    assert result is not None
    assert len(result.title) > 0
    assert len(result.content) > 200
    assert result.url == test_url
    assert result.source == "cna"

@pytest.mark.asyncio 
async def test_keyword_search():
    """測試關鍵詞搜尋"""
    crawler = CrawlerService()
    
    request = CrawlRequest(
        keywords=["台灣", "科技"],
        max_results=3,
        min_word_count=200
    )
    
    results = await crawler.crawl_by_keywords(request)
    
    assert len(results) <= 3
    for result in results:
        assert result.word_count >= 200
        # 檢查是否包含關鍵詞
        content_lower = result.content.lower()
        assert "台灣" in content_lower or "科技" in content_lower

def test_content_deduplication():
    """測試內容去重"""
    crawler = CrawlerService()
    
    # 創建兩篇內容相同的文章
    from app.models.crawler import CrawledContent
    from datetime import datetime
    
    content1 = CrawledContent(
        title="測試標題1",
        summary="測試摘要", 
        content="這是測試內容",
        url="http://test1.com",
        source="test",
        crawl_timestamp=datetime.now(),
        content_hash=crawler._calculate_hash("這是測試內容"),
        word_count=7
    )
    
    content2 = CrawledContent(
        title="測試標題2",
        summary="測試摘要",
        content="這是測試內容",  # 相同內容
        url="http://test2.com", 
        source="test",
        crawl_timestamp=datetime.now(),
        content_hash=crawler._calculate_hash("這是測試內容"),
        word_count=7
    )
    
    request = CrawlRequest(max_results=10, min_word_count=1)
    filtered = crawler._filter_and_process([content1, content2], request)
    
    # 去重後應該只有一篇
    assert len(filtered) == 1

def test_keyword_extraction():
    """測試關鍵詞提取"""
    crawler = CrawlerService()
    
    text = "台灣科技產業發展迅速，人工智慧和半導體技術領先全球。"
    keywords = crawler._extract_keywords(text)
    
    assert "台灣" in keywords
    assert "科技" in keywords
    assert "人工智慧" in keywords or "智慧" in keywords
    assert len(keywords) > 0
```

### 2. 整合測試範例

```python
# tests/test_integration.py
import pytest
from app.services.crawler_service import CrawlerService
from app.services.pydantic_ai_service import PydanticAIService
from app.models.podcast import PodcastGenerationRequest
from app.models.crawler import CrawlRequest

@pytest.mark.asyncio
async def test_news_to_podcast_pipeline():
    """測試從新聞爬取到播客生成的完整管線"""
    
    # Step 1: 爬取新聞
    crawler = CrawlerService()
    crawl_request = CrawlRequest(
        keywords=["人工智慧"],
        max_results=2,
        min_word_count=300
    )
    
    crawled_content = await crawler.crawl_by_keywords(crawl_request)
    assert len(crawled_content) > 0
    
    # Step 2: 生成播客
    ai_service = PydanticAIService(use_twcc=True)
    
    # 組合新聞標題作為主題
    combined_topic = f"AI 新聞分析: {crawled_content[0].title}"
    
    podcast_request = PodcastGenerationRequest(
        topic=combined_topic,
        tone="educational", 
        duration=15
    )
    
    result = await ai_service.generate_complete_podcast_content(
        podcast_request,
        crawled_content=crawled_content
    )
    
    # 驗證結果
    assert result["success"] is True
    assert "structured_script" in result
    script = result["structured_script"]
    assert len(script["title"]) > 0
    assert len(script["full_dialogue"]) > 500  # 確保有足夠的對話內容
    assert "主持人A" in script["full_dialogue"]
    assert "主持人B" in script["full_dialogue"]

@pytest.mark.asyncio
async def test_multiple_sources():
    """測試多來源爬取"""
    crawler = CrawlerService()
    
    # 測試不同來源
    urls = [
        "https://www.cna.com.tw/news/ait/202307220001.aspx",
        "https://news.ltn.com.tw/news/focus/breakingnews/4365001",
        # 添加更多測試 URL
    ]
    
    results = await crawler.crawl_from_urls(urls)
    
    # 應該至少有一個成功的結果
    assert len(results) > 0
    
    # 檢查來源識別是否正確
    sources = {result.source for result in results}
    assert len(sources) > 0  # 至少識別出一個來源
```

### 3. 效能測試範例

```python
# tests/test_performance.py
import pytest
import asyncio
import time
from app.services.crawler_service import CrawlerService

@pytest.mark.asyncio
async def test_concurrent_crawling():
    """測試並發爬取效能"""
    crawler = CrawlerService()
    
    # 準備多個 URL
    urls = [
        "https://www.cna.com.tw/news/aipl/202307220001.aspx",
        "https://www.cna.com.tw/news/ait/202307220002.aspx", 
        "https://www.cna.com.tw/news/asoc/202307220003.aspx",
        # 更多 URL...
    ]
    
    start_time = time.time()
    results = await crawler.crawl_from_urls(urls)
    end_time = time.time()
    
    # 檢查並發效能
    duration = end_time - start_time
    assert duration < 30  # 應該在 30 秒內完成
    assert len(results) > 0

@pytest.mark.asyncio 
async def test_rate_limiting():
    """測試速率限制"""
    crawler = CrawlerService()
    
    # 連續請求同一來源
    base_url = "https://www.cna.com.tw"
    
    start_time = time.time()
    
    # 模擬 5 個連續請求
    tasks = []
    for i in range(5):
        url = f"{base_url}/news/aipl/20230722000{i}.aspx"
        tasks.append(crawler._crawl_single_url(url))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    end_time = time.time()
    
    duration = end_time - start_time
    # 確保有適當的速率限制 (不會太快)
    assert duration > 2  # 至少需要 2 秒 (每秒最多 2 個請求)
```

## 🚀 快速開始指南

### 1. 環境設定
```bash
# 安裝額外的爬蟲依賴
pip install beautifulsoup4 lxml httpx jieba newspaper3k

# 或添加到 requirements.txt
echo "beautifulsoup4==4.12.2" >> requirements.txt
echo "lxml==4.9.3" >> requirements.txt  
echo "httpx==0.24.1" >> requirements.txt
echo "jieba==0.42.1" >> requirements.txt
```

### 2. 開發步驟
1. 先實現 `_crawl_single_url` 方法，測試基本爬取功能
2. 添加第一個新聞網站適配器 (建議從中央社開始)
3. 實現關鍵詞搜尋功能
4. 添加內容處理和品質評分
5. 整合到播客生成系統
6. 添加更多新聞來源

### 3. 測試執行
```bash
# 執行所有測試
pytest tests/ -v

# 執行特定測試
pytest tests/test_crawler_service.py::test_crawl_single_url -v

# 執行整合測試
pytest tests/test_integration.py -v
```

這個指南為您的朋友提供了完整的開發路線圖和測試框架，讓他能夠系統性地開發和測試爬蟲功能。
