# 客語播客音檔管理工具使用說明

## 概述

`podcast_audio_manager.py` 是一個整合了 TTS 音檔生成和音檔合併功能的工具，將原來的 `generate_podcast_audio.py` 和 `audio_merger.py` 合併為一個完整的播客製作工具。

## 功能特色

### 1. TTS 音檔生成
- 支援客語文本和中文文本的 TTS 轉換
- 智能文本清理和分段處理
- 自動選擇最佳文本版本（客語優先，中文備選）
- 生成詳細的播放列表檔案

### 2. 音檔合併
- 基於有序檔名的智能音檔排序
- 使用 FFmpeg 進行高品質音檔合併
- 支援不同說話者的音檔處理
- 自動清理臨時檔案

### 3. 完整流程
- 一鍵完成從腳本到完整播客的製作流程
- 互動式操作確認
- 詳細的進度報告和錯誤處理

## 使用方法

### 基本使用

```bash
cd backend
python app/podcast_audio_manager.py
```

### 程式化使用

```python
from app.podcast_audio_manager import PodcastAudioManager
import asyncio

async def main():
    manager = PodcastAudioManager()
    
    # 完整流程：生成 + 合併
    result = await manager.generate_and_merge_podcast(
        script_name="tech_news_3articles",
        speaker="SXF",
        auto_merge=False  # 詢問用戶是否要合併
    )
    
    if result['success']:
        print(f"✅ {result['message']}")
    else:
        print(f"❌ {result['error']}")

asyncio.run(main())
```

## 操作模式

執行主程式時，會提供以下選項：

1. **僅生成音檔** - 只進行 TTS 轉換，不合併
2. **僅合併現有音檔** - 合併已存在的音檔
3. **完整流程（生成 + 合併）** - 先生成音檔，再合併成完整播客
4. **查看音檔資訊** - 檢視現有音檔的詳細資訊

## 檔案結構

```
backend/
├── app/
│   └── podcast_audio_manager.py  # 主程式
├── json/
│   └── podcast_script_*.json     # 播客腳本
└── static/
    └── audio/
        ├── *.wav                 # 生成的音檔
        └── podcast_playlist.json # 播放列表
```

## 路徑配置

工具已自動配置正確的相對路徑：

- 腳本檔案：`backend/json/` 目錄
- 音檔輸出：`backend/static/audio/` 目錄
- 播放列表：`backend/static/audio/podcast_playlist.json`

## 依賴需求

### Python 套件
- FastAPI 相關套件（已在 requirements.txt 中）
- pathlib（內建）
- asyncio（內建）

### 外部工具
- **FFmpeg**（音檔合併必需）
  - Windows 安裝方法：
    ```bash
    # 使用 Chocolatey
    choco install ffmpeg
    
    # 使用 winget
    winget install Gyan.FFmpeg
    ```

### 環境變數
```bash
HAKKA_USERNAME=your_username
HAKKA_PASSWORD=your_password
```

## 音檔命名規範

工具支援以下音檔命名格式：
```
{script_name}_{speaker}_{sequence_number}.wav
```

例如：
- `tech_news_3articles_SXF_101.wav`
- `tech_news_3articles_HLF_102.wav`

## 錯誤處理

### 常見問題

1. **找不到腳本檔案**
   - 確認腳本檔案在 `backend/json/` 目錄中
   - 檢查檔案路徑和名稱是否正確

2. **TTS 登入失敗**
   - 檢查環境變數 `HAKKA_USERNAME` 和 `HAKKA_PASSWORD`
   - 確認網路連線正常

3. **FFmpeg 合併失敗**
   - 確認已安裝 FFmpeg
   - 檢查音檔檔案是否存在且可讀取

4. **找不到音檔**
   - 確認音檔命名符合規範
   - 檢查 `static/audio` 目錄權限

## 進階使用

### 自訂參數

```python
manager = PodcastAudioManager()

# 生成音檔時的參數
result = await manager.generate_podcast_audio(
    script_file="json/custom_script.json"
)

# 合併音檔時的參數
success = manager.merge_audio_files(
    script_name="custom_script",
    output_filename="my_podcast.wav",
    speaker="SXF"
)
```

### 批次處理

```python
scripts = ["script1", "script2", "script3"]
for script in scripts:
    result = await manager.generate_and_merge_podcast(
        script_name=script,
        auto_merge=True  # 自動合併，不詢問
    )
```

## 輸出檔案

### 播放列表檔案
生成的 `podcast_playlist.json` 包含：
- 播客標題和總時長
- 每個段落的說話者資訊
- 音檔列表和時長
- 對應的文本內容

### 合併後的音檔
- 檔名格式：`{script_name}_complete_{speaker}.wav`
- 高品質無損合併
- 自動計算檔案大小和時長

## 開發說明

### 主要類別

- `PodcastAudioManager`：主要管理類別
  - `generate_podcast_audio()`：TTS 音檔生成
  - `merge_audio_files()`：音檔合併
  - `generate_and_merge_podcast()`：完整流程
  - `show_script_info()`：音檔資訊顯示

### 輔助方法

- `split_text_by_sentences()`：文本分段
- `clean_hakka_text()`：客語文本清理
- `get_organized_files()`：音檔排序
- `create_ffmpeg_concat_file()`：FFmpeg 清單生成

## 更新日誌

### v1.0 (2025-08-01)
- 合併 `generate_podcast_audio.py` 和 `audio_merger.py`
- 修正路徑配置問題
- 新增完整流程模式
- 改善錯誤處理和用戶體驗
- 新增詳細的進度報告
