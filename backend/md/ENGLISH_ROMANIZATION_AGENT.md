# 英文轉羅馬拼音 Agent 說明

## 功能概述

這個 Agent 專門處理混合中英文文本中的英文單字轉換問題，將英文單字轉換成類似羅馬拼音的格式，以便 TTS 系統能夠正確發音。

## 主要特色

1. **智慧檢測**: 自動檢測文本中是否包含英文內容
2. **精準轉換**: 將英文單字轉換成近似的羅馬拼音發音
3. **保持格式**: 完全保留中文內容和原有標點符號
4. **無聲調標記**: 英文轉換後不添加數字標調（符合 TTS 需求）
5. **常見詞彙優化**: 對常見品牌和技術術語使用慣用音譯

## 核心方法

### 1. `convert_english_to_romanization(text: str) -> str`
直接轉換文本中的英文單字

```python
# 使用範例
ai_service = PydanticAIService(use_twcc=True)
text = "今天我們討論 Apple 和 Google 的競爭"
converted = await ai_service.convert_english_to_romanization(text)
# 結果: "今天我們討論 a-pu-er 和 gu-ge-er 的競爭"
```

### 2. `process_mixed_text_for_tts(text: str) -> str`
完整的 TTS 準備流程，包含英文檢測和轉換

```python
# 使用範例
text = "歡迎收聽 ChatGPT 相關新聞"
tts_ready = await ai_service.process_mixed_text_for_tts(text)
# 自動檢測並轉換英文內容
```

## 轉換範例

| 原文 | 轉換後（TTS格式） |
|------|--------|
| Apple | a24 pu24 er24 |
| Google | gu24 ge24 er24 |
| Microsoft | mai24 ke24 ro24 so24 fu24 te24 |
| Facebook | fei24 si24 bu24 ke24 |
| iPhone | ai24 feng24 |
| ChatGPT | cha24 te24 ji24 pi24 ti24 |
| YouTube | you24 tu24 be24 |
| Instagram | yin24 si24 ta24 ge24 lan24 mu24 |

### 數字標調說明
- **24**: 中平調（最常用）
- **55**: 高平調（重要品牌重音）
- **11**: 低平調（結尾音節）
- **2**: 上聲
- **31**: 去聲

## 整合到播客生成流程

### 在 `generate_complete_podcast_content` 中
```python
# 自動處理英文轉換
result = await ai_service.generate_complete_podcast_content(request, crawled_content)
# result 包含:
# - "full_content": 原始內容
# - "tts_ready_content": TTS 準備內容
```

### 在 `generate_podcast_script_with_agents` 中
```python
# 返回兩個版本的腳本
result = await ai_service.generate_podcast_script_with_agents(articles, max_minutes)
# result 包含:
# - "original_script": 原始腳本
# - "tts_ready_script": TTS 準備腳本
```

## 使用場景

1. **播客腳本後處理**: 將生成的播客腳本準備給 TTS 系統
2. **新聞內容處理**: 處理包含英文品牌名稱的新聞內容
3. **科技內容轉換**: 處理包含大量英文術語的科技討論
4. **混合語言內容**: 任何包含中英文混合的內容處理

## 配置需求

確保已設定以下環境變數之一：

### TWCC AFS (推薦)
```env
TWCC_API_KEY=your_twcc_api_key
TWCC_BASE_URL=your_twcc_base_url
TWCC_MODEL_NAME=your_model_name
```

### Gemini (備選)
```env
GEMINI_API_KEY=your_gemini_api_key
```

## 測試工具

### 基本測試
```bash
cd backend
python test_english_conversion.py
```

### 使用範例
```bash
cd backend
python example_english_conversion.py
```

## 注意事項

1. **網路連接**: 需要穩定的網路連接來調用 AI 模型
2. **API 配額**: 注意 API 使用配額限制
3. **處理時間**: 轉換過程需要調用 LLM，會有一定的處理時間
4. **錯誤處理**: 如果轉換失敗，會自動返回原文
5. **向後兼容**: 新功能完全向後兼容，不會影響現有代碼

## 錯誤處理

- **API 錯誤**: 自動回退到原文
- **網路問題**: 提供錯誤訊息但不中斷流程
- **模型不可用**: 使用備用方案或返回原文

## 性能優化建議

1. **批次處理**: 對長文本進行適當分段
2. **快取機制**: 可考慮對常見詞彙建立快取
3. **並行處理**: 對多段內容可並行處理（注意 API 限制）

這個 Agent 讓你的播客系統能夠無縫處理中英文混合內容，確保 TTS 輸出的品質和自然度！
