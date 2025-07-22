# Hakkast 播客生成系統 - 爬蟲整合開發文檔

## 📋 項目概述

本項目是一個基於 TWCC AFS 和 Pydantic AI 的客家播客自動生成系統，目前已完成核心的 AI 播客腳本生成功能，需要完善爬蟲模組來獲取新聞內容。

## 🎯 當前狀態

### ✅ 已完成功能
- **AI 服務核心**：`app/services/pydantic_ai_service.py` - 完整的對話式播客腳本生成
- **TWCC AFS 整合**：支援 `llama3.1-ffm-70b-32k-chat` 模型
- **結構化輸出**：使用 Pydantic 模型確保腳本格式一致
- **備用機制**：TWCC 失敗時自動切換到 Google Gemini
- **播客格式**：雙主持人深度對話分析格式

### 🔧 需要完善的爬蟲功能

## 📁 爬蟲相關檔案結構

```
backend/
├── app/
│   ├── models/
│   │   └── crawler.py          # 爬蟲資料模型 (已存在，需完善)
│   ├── services/
│   │   └── crawler_service.py  # 爬蟲服務 (需完善)
│   └── routers/
│       └── crawler.py          # 爬蟲 API 路由 (需完善)
```

## 🎪 爬蟲模組開發需求

### 1. 資料模型 (`app/models/crawler.py`)

當前模型結構：
```python
class CrawledContent(BaseModel):
    title: str
    summary: str
    # 需要擴展更多欄位
```

**需要擴展的欄位：**
```python
class CrawledContent(BaseModel):
    title: str                    # 新聞標題
    summary: str                  # 新聞摘要
    content: str                  # 完整新聞內容
    url: str                      # 原始網址
    published_date: datetime      # 發布時間
    source: str                   # 新聞來源
    category: str                 # 新聞分類
    keywords: List[str]           # 關鍵詞
    language: str                 # 語言 (zh-tw, en, etc.)
    crawl_timestamp: datetime     # 爬取時間戳
```

### 2. 爬蟲服務 (`app/services/crawler_service.py`)

**核心功能需求：**
- 支援多個新聞網站爬取
- 智能內容提取和清理
- 關鍵詞自動標記
- 內容去重和品質過濾
- 錯誤處理和重試機制

**建議的類別結構：**
```python
class CrawlerService:
    def crawl_news_by_keyword(self, keywords: List[str]) -> List[CrawledContent]
    def crawl_from_urls(self, urls: List[str]) -> List[CrawledContent]
    def extract_content(self, url: str) -> CrawledContent
    def filter_and_dedupe(self, contents: List[CrawledContent]) -> List[CrawledContent]
```

### 3. API 路由 (`app/routers/crawler.py`)

**需要的 API 端點：**
```python
@router.post("/crawl/keywords")  # 根據關鍵詞爬取
@router.post("/crawl/urls")      # 根據 URL 列表爬取
@router.get("/crawl/sources")    # 獲取支援的新聞來源
@router.get("/crawl/history")    # 獲取爬取歷史
```

## 🔗 與播客生成系統的整合

### 整合點 1：內容輸入
```python
# 在 pydantic_ai_service.py 中
async def generate_complete_podcast_content(
    request: PodcastGenerationRequest,
    crawled_content: Optional[List[CrawledContent]] = None  # 爬蟲內容輸入
) -> Dict[str, Any]:
```

### 整合點 2：工作流程
```
用戶輸入關鍵詞 → 爬蟲獲取相關新聞 → AI 分析生成播客腳本 → 輸出結果
```

## 🛠️ 技術要求

### 推薦的爬蟲技術棧
- **網頁解析**：BeautifulSoup4, lxml
- **HTTP 請求**：httpx (async), requests
- **內容提取**：newspaper3k, readability-lxml
- **去重**：hashlib (內容雜湊)
- **速率限制**：aiohttp-throttle, asyncio.Semaphore

### 需要支援的新聞網站 (建議優先級)
1. **台灣新聞**：中央社、自由時報、聯合報
2. **國際新聞**：BBC Chinese、CNN Chinese
3. **科技新聞**：TechCrunch、Ars Technica
4. **通用**：RSS 訂閱源支援

## 📊 爬蟲效能要求

- **並發處理**：支援至少 10 個並發請求
- **速率限制**：每個網站每秒最多 2 個請求
- **內容品質**：文章長度至少 200 字
- **時效性**：支援最近 7 天內的新聞
- **語言處理**：優先繁體中文內容

## 🔍 內容處理需求

### 內容清理
- 移除廣告和無關連結
- 統一格式化（去除多餘空白、標準化標點）
- 提取純文字內容

### 關鍵詞提取
- 使用 jieba 中文分詞
- TF-IDF 關鍵詞提取
- 命名實體識別 (NER)

### 品質過濾
- 過濾重複內容 (相似度 > 80%)
- 過濾過短文章 (< 200 字)
- 過濾無效連結和 404 頁面

## 🧪 測試需求

### 單元測試
```python
# tests/test_crawler_service.py
def test_crawl_single_url()
def test_extract_content()
def test_content_deduplication()
def test_keyword_extraction()
```

### 整合測試
```python
# tests/test_crawler_integration.py  
def test_crawler_to_podcast_pipeline()
def test_multiple_sources_crawling()
def test_error_handling()
```

## 🚀 開發里程碑

### Phase 1: 基礎爬蟲 (Week 1-2)
- [ ] 完善 `CrawledContent` 模型
- [ ] 實現基本的單一 URL 爬取
- [ ] 內容提取和清理功能

### Phase 2: 多源爬蟲 (Week 3-4)  
- [ ] 支援多個新聞網站
- [ ] 關鍵詞搜尋功能
- [ ] 並發處理和速率限制

### Phase 3: 智能處理 (Week 5-6)
- [ ] 內容去重和品質過濾
- [ ] 關鍵詞自動提取
- [ ] 錯誤處理和重試機制

### Phase 4: 整合優化 (Week 7-8)
- [ ] 與播客生成系統完整整合
- [ ] API 端點完善
- [ ] 效能優化和測試

## 💡 開發建議

1. **開始點**：先實現一個簡單的新聞網站爬蟲，確保基本功能正常
2. **逐步擴展**：一個網站一個網站地添加支援
3. **測試驅動**：每個功能都要有對應的測試案例
4. **文檔更新**：及時更新 API 文檔和使用範例

## 📞 聯絡與支援

如有任何技術問題或需要協助，可以：
- 查看現有的 `pydantic_ai_service.py` 了解 AI 服務如何使用爬蟲內容
- 參考 `final_dialogue_generator.py` 了解完整的使用流程
- 檢查 `app/models/podcast.py` 了解資料結構要求

---

**注意**：開發過程中請遵守各網站的 robots.txt 和使用條款，合理控制爬取頻率，避免對目標網站造成過大負擔。
