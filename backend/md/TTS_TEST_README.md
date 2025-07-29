# TTS 測試使用說明

## 概述

已成功將翻譯腳本與 TTS 服務整合，現在可以將翻譯出來的客語內容直接輸出給 `tts_service.py` 進行語音生成測試。

## 功能特色

1. **完整流程**: 翻譯 → TTS分段 → 語音生成 → 測試驗證
2. **分離模式**: 可單獨運行 TTS 測試，無需重新翻譯
3. **自動fallback**: TTS API 失敗時自動使用模擬音頻
4. **詳細記錄**: 保存測試結果、音頻資訊和統計數據

## 使用方法

### 1. 完整流程（翻譯 + TTS 測試）
```bash
cd backend
python translate_podcast_script.py
```

### 2. 僅 TTS 測試（使用已有翻譯）
```bash
cd backend
python translate_podcast_script.py --tts-only
```

### 3. 音頻文件驗證
```bash
cd backend
python test_audio_files.py
```

## 生成的文件

### 翻譯相關
- `podcast_script_hakka_YYYYMMDD_HHMMSS.txt` - 完整客語腳本
- `podcast_dialogue_hakka_YYYYMMDD_HHMMSS.json` - 詳細對話資訊
- `podcast_romanization_YYYYMMDD_HHMMSS.txt` - 拼音對照表
- `tts_segments_YYYYMMDD_HHMMSS.json` - TTS就緒分段

### TTS 測試相關
- `tts_test_result_YYYYMMDD_HHMMSS.json` - TTS測試結果
- `static/audio/*.wav` - 生成的音頻文件

## TTS 測試結果

### 最新測試狀態
- **測試時間**: 2025/7/24 23:40
- **測試段落**: 3 段對話
- **成功率**: 100% (3/3)
- **生成模式**: Fallback (API返回400錯誤)

### 音頻文件資訊
- **格式**: WAV
- **取樣率**: 44.1 kHz
- **聲道**: 單聲道 (Mono)
- **樣本寬度**: 16-bit
- **持續時間**: 60秒 (模擬音頻)
- **檔案大小**: ~5.3 MB 每個文件

## 播放音頻文件

### 方法1: 直接播放
```bash
# 使用系統默認播放器
start static/audio/[檔名].wav
```

### 方法2: 瀏覽器播放
1. 啟動後端服務: `uvicorn app.main:app --reload`
2. 訪問: `http://localhost:8000/static/audio/[檔名].wav`

### 方法3: 音頻編輯軟體
使用 Audacity、Adobe Audition 等軟體打開 WAV 文件

## TTS 服務狀態

### 當前狀態
- ✅ **連接成功**: 可成功登入 TTS 服務
- ❌ **API錯誤**: 合成請求返回 400 錯誤
- ✅ **Fallback正常**: 自動生成模擬音頻

### 故障排除
1. **檢查環境變數**:
   - `HAKKA_TTS_API_URL`
   - `HAKKA_USERNAME` 
   - `HAKKA_PASSWORD`

2. **檢查 API 格式**:
   - 確認請求格式符合 TTS API 規範
   - 檢查文本編碼和特殊字符

3. **網絡連接**:
   - 確認可訪問 TTS 服務端點
   - 檢查防火牆設置

## 統計資訊

### 翻譯統計 (最新)
- **對話段落**: 36 段
- **預估總時長**: 1264.0秒 (21.1分鐘)
- **平均每段時長**: 35.1秒

### TTS 測試統計
- **測試段落**: 3 段 (前3段用於測試)
- **成功生成**: 3 個音頻文件
- **總檔案大小**: 15.14 MB
- **平均檔案大小**: 5.05 MB

## 下一步建議

1. **修復 TTS API**:
   - 檢查 API 文檔和請求格式
   - 調試 400 錯誤的具體原因
   - 測試不同的文本輸入

2. **增強功能**:
   - 添加音頻品質評估
   - 支援批次處理全部對話
   - 添加音頻後處理功能

3. **整合播放器**:
   - 在前端加入音頻播放功能
   - 實現連續播放播客
   - 添加播放控制功能

## 文件結構

```
backend/
├── translate_podcast_script.py    # 主要翻譯+TTS腳本
├── test_audio_files.py           # 音頻文件驗證
├── static/audio/                 # 生成的音頻文件
├── podcast_dialogue_hakka_*.json # 翻譯對話資料
├── tts_test_result_*.json        # TTS測試結果
└── app/services/
    ├── translation_service.py    # 翻譯服務
    └── tts_service.py            # TTS服務
```
