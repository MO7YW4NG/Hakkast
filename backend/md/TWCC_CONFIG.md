# TWCC AFS 模型配置說明

## 可用模型列表

### FFM 系列模型（推薦）
這些是繁體中文強化的模型，特別適合客語播客生成：

- `llama3.3-ffm-70b-32k-chat` - 最新版本，Tool Call 功能強化
- `llama3.1-ffm-70b-32k-chat` - 高性能版本，支援 Function Calling
- `llama3.1-ffm-8b-32k-chat` - 輕量版本，速度較快
- `llama3-ffm-70b-chat` - 經典版本
- `llama3-ffm-8b-chat` - 輕量經典版本

### 台灣本土化模型
- `taide-lx-7b-chat` - 國科會打造的台灣本土化 LLM

### 其他可選模型
- `ffm-mixtral-8x7b-32k-instruct` - Mixtral 繁中強化版
- `ffm-mistral-7b-32k-instruct` - Mistral 繁中強化版

## 配置方式

### 1. 從 TWCC 官網取得 API Key
1. 註冊 TWSC 帳號：https://tws.twsc.ai/
2. 進入 AFS 服務
3. 建立 AFS ModelSpace 任務
4. 取得 API Key 和端點

### 2. 設定環境變數
```bash
# 在 .env 文件中設定
TWCC_API_KEY=your_actual_api_key
TWCC_BASE_URL=https://api-ams.twcc.ai/api/models  # 公用模式
TWCC_MODEL_NAME=llama3.3-ffm-70b-32k-chat       # 選擇模型
```

### 3. 不同部署模式的 BASE_URL
- **AFS MS 公用模式**: `https://api-ams.twcc.ai/api/models`
- **AFS MS 私有模式**: `https://xxxxx.afs.twcc.ai/text-generation/api/v4/models`
- **AFS Cloud**: 從詳細資料頁面取得專屬 API 端點

## 使用建議

### 客語播客生成推薦配置
```bash
TWCC_MODEL_NAME=llama3.3-ffm-70b-32k-chat
```
理由：
- 最新的繁中強化模型
- Tool Call 功能強化，提升生成品質
- 32K 上下文長度，支援長篇內容

### 快速測試推薦配置
```bash
TWCC_MODEL_NAME=llama3.1-ffm-8b-32k-chat
```
理由：
- 回應速度較快
- 成本較低
- 適合開發測試

### 台灣本土化體驗
```bash
TWCC_MODEL_NAME=taide-lx-7b-chat
```
理由：
- 台灣國科會開發
- 本土文化語意理解更佳
- 適合台灣在地內容

## 測試方式

修改好配置後，可以使用以下方式測試：

```python
# 測試 TWCC 連接
python -c "
import asyncio
from app.services.pydantic_ai_service import test_pydantic_ai_service
asyncio.run(test_pydantic_ai_service())
"

# 測試不同模型
python -c "
import asyncio  
from app.services.pydantic_ai_service import test_twcc_models
asyncio.run(test_twcc_models())
"
```

## 故障排除

### 常見錯誤
1. **API Key 錯誤**: 檢查 TWCC_API_KEY 是否正確
2. **模型名稱錯誤**: 確認 TWCC_MODEL_NAME 在可用列表中
3. **端點錯誤**: 檢查 TWCC_BASE_URL 格式

### 回退機制
系統會自動回退到 Gemini 模型（如果 TWCC 不可用）：
```
TWCC 不可用 → 自動使用 Gemini → 保證服務可用性
```
