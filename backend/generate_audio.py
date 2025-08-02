#先用現有json測，還沒整合到 interactive_podcast_generator.py
import json
import asyncio
import os
import re
from pathlib import Path
import subprocess
from app.services.tts_service import TTSService

#抓音檔ㄉ順序
def extract_number(path):
    m = re.search(r'_(\d{3})_fixed\.wav$', str(path))
    return int(m.group(1)) if m else 0

#音檔轉成統一格式
def fix_wav_format(input_path, output_path, sample_rate=44100):
    cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-ar", str(sample_rate), "-ac", "1", "-sample_fmt", "s16",
        str(output_path)
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

async def merge_audio_only():
    audio_dir = Path("static/audio")
    # 抓 _fixed.wav 的檔案+排序
    wav_files = sorted(
        [audio_dir / f for f in os.listdir(audio_dir) if re.match(r'podcast_[A-Z]+_\d{3}_fixed\.wav$', f)],
        key=extract_number
    )

    print("合併順序：")
    for f in wav_files:
        print(f)

    filelist_txt = audio_dir / "filelist.txt"
    with open(filelist_txt, "w", encoding="utf-8") as f:
        for path in wav_files:
            abs_path = path.resolve().as_posix()
            f.write(f"file '{abs_path}'\n")

    final_path = (audio_dir / "podcast_final.wav").resolve()
    print(f"最終檔案將儲存在：{final_path}")

    #  ffmpeg 合併
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(filelist_txt),
        "-ar", "44100", "-ac", "1", "-sample_fmt", "s16",
        str(final_path)
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    print("FFmpeg stderr output：")
    print(result.stderr.decode("utf-8"))

    if final_path.exists():
        print(f"音檔已成功合併產生：{final_path}")
        # 刪除fixed&原始
        for path in wav_files:
            try:
                path.unlink()
                original_path = path.with_name(path.name.replace("_fixed", ""))
                if original_path.exists():
                    original_path.unlink()
            except Exception as e:
                print(f"刪除檔案失敗 ;;：{e}")

        # 刪 filelist.txt
        if filelist_txt.exists():
            filelist_txt.unlink()
    else:
        print("合併失敗，請檢查錯誤訊息或 filelist.txt 檔案格式")

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

SPEAKER_CODE = {
    "佳昀": "UNK",
    "敏權": "SXM"
}

async def main():
    tts = TTSService()
    audio_dir = Path("static/audio")
    audio_dir.mkdir(parents=True, exist_ok=True)
    segment_audio_paths = []

    for idx, seg in enumerate(data["content"]):
        text = seg["text"]
        speaker = seg.get("speaker", "")
        filename = tts._generate_readable_filename(
            text, SPEAKER_CODE.get(speaker, speaker), idx, "podcast", idx
        )
        output_path = audio_dir / filename

        if speaker == "佳昀":
            print(f"呼叫 Gemini API：speaker=佳昀, text={text[:10]}...")
            try:
                await tts.generate_gemini_tts(text, str(output_path))
                print(f"Gemini音檔產生成功: {output_path}")
            except Exception as e:
                print(f"Gemini音檔產生失敗: {e}")
                continue
        elif speaker == "敏權":
            speaker_id = SPEAKER_MAP[user_dialect]["敏權"]
            print(f"呼叫 TWCC API：speaker_id={speaker_id}, text={text[:10]}...")
            try:
                await tts.generate_hakka_audio(
                    hakka_text=text,
                    speaker=speaker_id,
                    segment_index=idx,
                    script_name="podcast"
                )
                print(f"TWCC音檔產生成功: {output_path}")
            except Exception as e:
                print(f"TWCC音檔產生失敗: {e}")
                continue
        else:
            print(f"未知說話者: {speaker}，跳過，不加入合併")
            continue

        fixed_path = output_path.parent / (output_path.stem + "_fixed.wav")
        fix_wav_format(output_path, fixed_path)
        segment_audio_paths.append(str(fixed_path))

    filelist_txt = audio_dir / "filelist.txt"
    with open(filelist_txt, "w", encoding="utf-8") as f:
        for path in segment_audio_paths:
            rel_path = Path(path).resolve().as_posix()
            f.write(f"file '{rel_path}'\n")

    final_path = audio_dir / "podcast_final.wav"
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(filelist_txt),
        "-ar", "44100", "-ac", "1", "-sample_fmt", "s16",
        str(final_path)
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("FFmpeg stderr:\n", result.stderr.decode("utf-8"))

    if final_path.exists():
        print(f"Podcast 音檔已產生: {final_path}")
        for path in segment_audio_paths:
            try:
                fixed = Path(path)
                if fixed.exists():
                    fixed.unlink()
                original = fixed.with_name(fixed.name.replace("_fixed", ""))
                if original.exists():
                    original.unlink()
            except Exception as e:
                print(f"刪除檔案失敗：{e}")

        if filelist_txt.exists():
            filelist_txt.unlink()

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
