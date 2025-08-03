import os
import asyncio
import wave
from app.services.tts_service import TTSService

def test_generate_gemini_tts():
    tts = TTSService()
    test_text = "你好，這是繁體中文語音測試。"
    output_path = "test_gemini.wav"

    async def run():
        result_path = await tts.generate_gemini_tts(test_text, output_path)
        assert os.path.exists(result_path), "音檔未產生"
        assert os.path.getsize(result_path) > 0, "音檔為空"
        print("好難可是成功", os.path.getsize(result_path))
        # 檔案開頭
        with open(result_path, "rb") as f:
            head = f.read(16)
            print("檔案開頭:", head)
        # 音訊長度（秒）
        with wave.open(result_path, "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            duration = frames / float(rate)
            print("音訊長度（秒）:", duration)

    asyncio.run(run())

if __name__ == "__main__":
    test_generate_gemini_tts()