"""
Pydantic AI 測試腳本
"""

import asyncio
import sys
import os

# 將 backend 目錄加入 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.pydantic_ai_service import PydanticAIService, test_pydantic_ai_service
from app.models.podcast import PodcastGenerationRequest

async def simple_test():
    """簡單測試 Pydantic AI 功能"""
    print("🚀 開始測試 Pydantic AI 服務...")
    
    try:
        # 測試環境變數
        from app.core.config import settings
        if not settings.GEMINI_API_KEY:
            print("❌ GEMINI_API_KEY 未設定，請設定環境變數")
            return
        
        print("✅ GEMINI_API_KEY 已設定")
        
        # 創建服務實例
        print("📡 正在創建 Pydantic AI 服務實例...")
        service = PydanticAIService()
        print("✅ 服務實例創建成功")
        
        # 創建測試請求
        request = PodcastGenerationRequest(
            topic="客家美食文化",
            style="conversational",
            duration=10
        )
        
        # 測試內容分析
        print("🔍 測試內容分析功能...")
        analysis = await service.analyze_content_requirements(request.topic, request.style)
        print(f"✅ 內容分析完成: {analysis}")
        
        # 測試腳本生成
        print("📝 測試腳本生成功能...")
        script = await service.generate_podcast_script(request, content_analysis=analysis)
        print(f"✅ 腳本生成完成: 標題='{script.title}', 時長={script.estimated_duration_minutes}分鐘")
        
        print("🎉 所有測試通過！")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(simple_test())
