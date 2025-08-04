#!/usr/bin/env python3
"""
整合版：支援「華客語」與「雙客語」的 Podcast 生成功能
- 使用 Gemini 處理華語
- 使用 TWCC 處理客語（含四縣/海陸腔）
- 合併邏輯來自 generate_bi_audio.py，避免 podcast_audio_manager 的不穩定合併
"""
import asyncio
import json
import os
import re
import subprocess
from pathlib import Path
from app.services.tts_service import TTSService


# 用戶選擇模式：華客語 or 雙客語
print("請選擇語音模式：")
print("1. 華客語（佳昀=中文, 敏權=客語）")
print("2. 雙客語（佳昀=客語, 敏權=客語）")
mode_choice = input("請輸入選項（1/2）: ").strip()

if mode_choice == "1":
    MODE = "華客語"
elif mode_choice == "2":
    MODE = "雙客語"
else:
    print("無效選項")
    exit(1)

# 選擇腔調
user_dialect = input("請輸入腔調（四縣/海陸）: ").strip()
if user_dialect not in ["四縣", "海陸"]:
    print("只支援 四縣/海陸")
    exit(1)

# 腔調對應表（支援多腔調客語）
SPEAKER_MAP = {
    "四縣": {"敏權": "hak-xi-TW-vs2-M01", "佳昀": "hak-xi-TW-vs2-F01"},
    "海陸": {"敏權": "hak-hoi-TW-vs2-M01", "佳昀": "hak-hoi-TW-vs2-F01"},
}

SPEAKER_CODE = {"佳昀": "UNK", "敏權": "SXM"}



def extract_number(path):
    m = re.search(r'_(\d{3})_fixed\.wav$', str(path))
    return int(m.group(1)) if m else 0

def fix_wav_format(input_path, output_path, sample_rate=44100):
    """使用 FFmpeg 修復 WAV 格式"""
    cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-ar", str(sample_rate), "-ac", "1", "-sample_fmt", "s16",
        str(output_path)
    ]
    print(f"執行 ffmpeg：{' '.join(cmd)}")
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    stderr_output = result.stderr.decode("utf-8")
    if result.returncode != 0:
        print(f"ffmpeg 轉檔失敗：{input_path.name}")
        print(stderr_output)
        return False
    else:
        print(f"ffmpeg 成功轉檔為：{output_path.name}")
        return True

async def merge_audio_only():
    """只合併現有的 fixed 音檔"""
    audio_dir = Path("static/audio")
    wav_files = sorted(
        [audio_dir / f for f in os.listdir(audio_dir) if re.match(r'podcast_[A-Z]+_\d{3}_fixed\.wav$', f)],
        key=extract_number
    )
    print("合併順序：")
    for f in wav_files:
        print(f)

    if not wav_files:
        print("沒有找到任何 _fixed.wav 檔案")
        return

    filelist_txt = audio_dir / "filelist.txt"
    with open(filelist_txt, "w", encoding="utf-8") as f:
        for path in wav_files:
            f.write(f"file '{path.resolve().as_posix()}'\n")

    final_path = audio_dir / "podcast_final.wav"
    print(f"最終檔案將儲存在：{final_path}")

    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(filelist_txt),
        "-ar", "44100", "-ac", "1", "-sample_fmt", "s16",
        str(final_path)
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("FFmpeg stderr output：")
    print(result.stderr.decode("utf-8"))

    if final_path.exists() and final_path.stat().st_size > 0:
        print(f"音檔已成功合併產生：{final_path}")
        print(f"最終檔案大小：{final_path.stat().st_size} bytes")
        
        # 可選：刪除個別檔案
        delete_individual = input("是否刪除個別音檔？(y/N)：").strip().lower()
        if delete_individual == 'y':
            for path in wav_files:
                try:
                    path.unlink()
                    origin = path.with_name(path.name.replace("_fixed", ""))
                    if origin.exists():
                        origin.unlink()
                except Exception as e:
                    print(f"刪除檔案失敗：{e}")
    else:
        print("合併失敗")

with open("json/podcast_script_technology_news_3articles.json", "r", encoding="utf-8") as f:
    data = json.load(f)

user_dialect = input("請輸入腔調（四縣/海陸）: ").strip()
if user_dialect not in ["四縣", "海陸"]:
    print("只支援 四縣/海陸")
    exit(1)

SPEAKER_MAP = {
    "四縣": {"敏權": "hak-xi-TW-vs2-M01", "佳昀": "gemini"},
    "海陸": {"敏權": "hak-hoi-TW-vs2-M01", "佳昀": "gemini"},
}
SPEAKER_CODE = {"佳昀": "UNK", "敏權": "SXM"}

async def main():
    tts = TTSService()
    audio_dir = Path("static/audio")
    audio_dir.mkdir(parents=True, exist_ok=True)
    # 存放最終要合併的 fixed 檔案路徑
    fixed_audio_paths = []  

    for idx, seg in enumerate(data["content"]):
        text = seg["text"]
        hakka_text = seg.get("hakka_text", "")
        romanization = seg.get("romanization", "")
        speaker = seg.get("speaker", "")
        
        print(f"\n處理第 {idx} 段：{speaker}")
        print(f"文本：{text[:50]}...")

        if speaker == "敏權":
            if not hakka_text.strip() and not romanization.strip():
                print(f"敏權第 {idx} 段 hakka_text 與 romanization 都是空的，跳過")
                continue

        if speaker == "佳昀":
            if MODE == "華客語":
                print(f"呼叫 Gemini TTS")
                try:
                    filename = tts._generate_readable_filename(text, SPEAKER_CODE.get(speaker, speaker), idx, "podcast", idx)
                    output_path = audio_dir / filename
                    await tts.generate_gemini_tts(text, str(output_path))

                    if not output_path.exists() or output_path.stat().st_size == 0:
                        print(f"Gemini 產生的音檔無效：{output_path}")
                        continue

                    fixed_path = output_path.parent / (output_path.stem + "_fixed.wav")
                    if fix_wav_format(output_path, fixed_path):
                        print(f"Gemini 音檔產生成功: {fixed_path}")
                        fixed_audio_paths.append(str(fixed_path))
                        try:
                            output_path.unlink()
                        except:
                            pass
                    else:
                        print(f"Gemini 音檔格式修復失敗")
                        continue

                except Exception as e:
                    print(f"Gemini 音檔產生失敗: {e}")
                    continue

            else:  # 雙客語 
                speaker_id = SPEAKER_MAP[user_dialect]["佳昀"]
                print(f"🎤 雙客語：呼叫 TWCC 客語 TTS → speaker_id={speaker_id}")
                try:
                    result = await tts.generate_hakka_audio(
                        hakka_text=hakka_text,
                        romanization=romanization,
                        speaker=speaker_id,
                        segment_index=idx,
                        script_name="podcast"
                    )

                    if not isinstance(result, dict) or "audio_path" not in result or not result["audio_path"]:
                        print(f"TWCC 回傳格式錯誤：{result}")
                        continue

                    output_path = Path(result["audio_path"])
                    if not output_path.exists() or output_path.stat().st_size == 0:
                        print(f"TWCC 產生的音檔無效：{output_path}")
                        continue

                    fixed_path = output_path.parent / (output_path.stem + "_fixed.wav")
                    if fix_wav_format(output_path, fixed_path):
                        print(f"TWCC 音檔產生成功: {fixed_path}")
                        fixed_audio_paths.append(str(fixed_path))
                        try:
                            output_path.unlink()
                        except:
                            pass
                    else:
                        print(f"TWCC 音檔格式修復失敗")
                        continue

                except Exception as e:
                    print(f"TWCC 音檔產生失敗: {e}")
                    continue

        elif speaker == "敏權":
            speaker_id = SPEAKER_MAP[user_dialect]["敏權"]
            print(f"呼叫 TWCC TTS：speaker_id={speaker_id}")
            try:
                # generate_hakka_audio 會處理分割、合併，產生單一檔案
                result = await tts.generate_hakka_audio(
                    hakka_text=hakka_text,
                    romanization=romanization,
                    speaker=speaker_id,
                    segment_index=idx,
                    script_name="podcast"
                )

                if not isinstance(result, dict) or "audio_path" not in result or not result["audio_path"]:
                    print(f"TWCC 回傳格式錯誤：{result}")
                    continue
                
                output_path = Path(result["audio_path"])
                
                if not output_path.exists() or output_path.stat().st_size == 0:
                    print(f"TWCC 產生的音檔無效：{output_path}")
                    continue
                
                # 產生 fixed 
                fixed_path = output_path.parent / (output_path.stem + "_fixed.wav")
                if fix_wav_format(output_path, fixed_path):
                    print(f"TWCC 音檔產生成功: {fixed_path}")
                    fixed_audio_paths.append(str(fixed_path))
                    
                    # 刪除原始檔案，只保留 fixed 
                    try:
                        output_path.unlink()
                    except:
                        pass
                else:
                    print(f"TWCC 音檔格式修復失敗")
                    continue

            except Exception as e:
                print(f"TWCC 音檔產生失敗: {e}")
                continue

        else:
            print(f"未知說話者: {speaker}，跳過")
            continue

    # 合併所有 fixed 檔案 
    if not fixed_audio_paths:
        print("沒有任何成功產生的音檔，無法合併")
        return

    print(f"共有 {len(fixed_audio_paths)} 個音檔要合併：")
    for i, path in enumerate(fixed_audio_paths):
        file_size = Path(path).stat().st_size if Path(path).exists() else 0
        print(f"  {i+1}. {Path(path).name} ({file_size} bytes)")

    # 建立合併檔案清單
    filelist_txt = audio_dir / "filelist.txt"
    with open(filelist_txt, "w", encoding="utf-8") as f:
        for path in fixed_audio_paths:
            f.write(f"file '{Path(path).resolve().as_posix()}'\n")

    # 執行最終合併
    final_path = audio_dir / "podcast_final.wav"
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(filelist_txt),
        "-ar", "44100", "-ac", "1", "-sample_fmt", "s16",
        str(final_path)
    ]
    
    print(f"執行最終合併：{' '.join(cmd)}")
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    stderr_output = result.stderr.decode("utf-8")
    print("FFmpeg stderr output：")
    print(stderr_output)

    if final_path.exists() and final_path.stat().st_size > 0:
        print(f" Podcast 音檔已產生：{final_path}")
        
        # 清理檔案
        cleanup = input("是否刪除個別音檔，只保留最終合併檔？(y/N)：").strip().lower()
        if cleanup == 'y':
            for path in fixed_audio_paths:
                try:
                    Path(path).unlink()
                    print(f" 已刪除：{Path(path).name}")
                except Exception as e:
                    print(f" 刪除檔案失敗：{e}")
    else:
        print(" Podcast 最終合併失敗")

if __name__ == "__main__":
    print("請選擇功能：")
    print("1. 產生&合併音檔")
    print("2. 只合併現有音檔")
    choice = input("請輸入選項（1/2）：").strip()
    if choice == "1":
        asyncio.run(main())
    elif choice == "2":
        asyncio.run(merge_audio_only())
    else:
        print("無效選項")