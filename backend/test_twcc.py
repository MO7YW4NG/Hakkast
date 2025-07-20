#!/usr/bin/env python3
"""
TWCC AFS 測試腳本
用於測試 TWCC AFS 模型連接和功能
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加項目路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.pydantic_ai_service import test_pydantic_ai_service, test_twcc_models
from app.core.config import settings

def print_config():
    """顯示當前配置"""
    print("🔧 當前配置:")
    print(f"  TWCC_API_KEY: {'已設定' if settings.TWCC_API_KEY else '未設定'}")
    print(f"  TWCC_BASE_URL: {settings.TWCC_BASE_URL}")
    print(f"  TWCC_MODEL_NAME: {settings.TWCC_MODEL_NAME}")
    print(f"  GEMINI_API_KEY: {'已設定' if settings.GEMINI_API_KEY else '未設定'}")
    print()

async def main():
    """主測試函數"""
    print("=" * 60)
    print("🧪 TWCC AFS Pydantic AI 測試")
    print("=" * 60)
    
    print_config()
    
    if not settings.TWCC_API_KEY and not settings.GEMINI_API_KEY:
        print("❌ 錯誤: 需要設定 TWCC_API_KEY 或 GEMINI_API_KEY")
        print("請在 .env 文件中設定相關 API Key")
        return
    
    # 基本功能測試
    print("📋 執行基本功能測試...")
    result = await test_pydantic_ai_service()
    
    if result and result.get('success'):
        print("✅ 基本測試通過!")
        
        # 如果 TWCC 可用，測試不同模型
        if settings.TWCC_API_KEY:
            print("\n📋 測試不同 TWCC 模型...")
            await test_twcc_models()
    else:
        print("❌ 基本測試失敗")
    
    print("\n🏁 測試完成")

if __name__ == "__main__":
    asyncio.run(main())
