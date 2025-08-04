# 🚀 TWCC AFS + Pydantic AI 客語播客生成服務

## 🎯 功能概述
這個更新後的服務支援使用 TWCC (Taiwan Computing Cloud) AFS 平台的 AI 模型來生成客語播客內容，提供更好的繁體中文支援和台灣本土化體驗。

## 🔧 支援的 AI 模型

### 🥇 推薦使用：TWCC AFS 模型
- **llama3.3-ffm-70b-32k-chat** - 最新版本，Tool Call 功能強化
- **taide-lx-7b-chat** - 台灣國科會開發的本土化模型
- **llama3.1-ffm-70b-32k-chat** - 高性能版本
- **llama3-ffm-8b-chat** - 輕量版本，適合測試

### 🛡️ 備用模型
- **Google Gemini** - 作為備用選項

## 📋 設定步驟

### 1. 取得 TWCC API Key
1. 訪問 [TWCC 官網](https://tws.twcc.ai/)
2. 註冊並登入帳號
3. 進入 AFS 服務 → ModelSpace
4. 建立任務並取得 API Key

### 2. 配置環境變數
複製 `.env.example` 到 `.env` 並填入您的 API Key：

```bash
# TWCC AFS 配置 (推薦)
TWCC_API_KEY=your_actual_twcc_api_key
TWCC_BASE_URL=https://api-ams.twcc.ai/api/models
TWCC_MODEL_NAME=llama3.3-ffm-70b-32k-chat

# Gemini 配置 (備用)
GEMINI_API_KEY=your_gemini_api_key
```

### 3. 安裝依賴
```bash
pip install pydantic-ai openai google-genai
```

## 🧪 測試方式

### 基本測試
```bash
python test_twcc.py
```

### 模擬測試（無需 API Key）
```bash
python mock_test.py
```

### 程式碼測試
```python
from app.services.pydantic_ai_service import PydanticAIService
from app.models.podcast import PodcastGenerationRequest

# 建立服務
service = PydanticAIService(use_twcc=True)

# 建立請求
request = PodcastGenerationRequest(
    topic="客家傳統文化與現代科技的結合",
    tone="educational",
    duration=15
)

# 生成內容
result = await service.generate_complete_podcast_content(request)
```

## 🔄 系統特色

### 智能回退機制
```
TWCC AFS 模型 → Google Gemini → 本地備用腳本
```
確保服務始終可用，即使某個 AI 服務不可用。

### 結構化輸出
```json
{
  "success": true,
  "model_info": {
    "provider": "TWCC AFS",
    "model_name": "llama3.3-ffm-70b-32k-chat"
  },
  "content_analysis": { ... },
  "structured_script": { ... },
  "full_content": "...",
  "generation_timestamp": "...",
  "processing_steps": [...]
}
```

### 客製化配置
- 支援多種音調：casual, educational, storytelling, interview
- 可調整播客時長：5-60 分鐘
- 支援多語言：hakka, mixed, bilingual

## 📊 使用建議

### 🎯 推薦配置組合

**高品質內容生成**：
```bash
TWCC_MODEL_NAME=llama3.3-ffm-70b-32k-chat
```

**快速原型開發**：
```bash
TWCC_MODEL_NAME=llama3-ffm-8b-chat
```

**台灣本土化體驗**：
```bash
TWCC_MODEL_NAME=taide-lx-7b-chat
```

## 🛠️ 故障排除

### 常見問題

**Q: API Key 錯誤**
```
A: 檢查 TWCC_API_KEY 是否正確設定，確認 API Key 有效性
```

**Q: 模型名稱錯誤**
```
A: 確認 TWCC_MODEL_NAME 在支援列表中，參考 TWCC_CONFIG.md
```

**Q: 連線失敗**
```
A: 檢查 TWCC_BASE_URL 格式，確認網路連線正常
```

### 偵錯模式
設定 `DEBUG=true` 可以看到更詳細的錯誤資訊：
```bash
echo "DEBUG=true" >> .env
```

## 🚀 進階使用

### 自訂 Agent 配置
```python
# 可以自訂 system prompt 來調整輸出風格
service = PydanticAIService(use_twcc=True)
# Agent 會根據客語播客需求自動調整
```

### 批量處理
```python
topics = ["客家文化", "客語教學", "客家美食"]
for topic in topics:
    request = PodcastGenerationRequest(topic=topic, tone="casual", duration=10)
    result = await service.generate_complete_podcast_content(request)
```

## 📈 效能優化

- 使用較小的模型 (8B) 可以提升速度
- 調整 `duration` 參數控制內容長度
- TWCC AFS 提供更好的繁體中文支援

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request 來改善這個服務！

---

*最後更新：2025-07-20*
