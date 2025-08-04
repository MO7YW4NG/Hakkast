#!/usr/bin/env python3
"""
測試英文翻譯功能的腳本
驗證 translate_english_to_chinese 方法的英文替換功能
"""

import asyncio
import sys
import os

# 將 backend 目錄添加到 Python 路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.ai_service import PydanticAIService


async def test_english_translation():
    """測試英文翻譯和替換功能"""
    
    # 初始化服務（使用 Gemini）
    try:
        translation_service = PydanticAIService(use_twcc=False)
        print("✅ 服務初始化成功")
    except Exception as e:
        print(f"❌ 服務初始化失敗: {e}")
        return
    
    # 測試用例
    test_cases = [
        "我今天要學習 Machine Learning 和 Deep Learning。",
        "Apple 公司推出了新的 iPhone 15。",
        "這個 GitHub repository 很有用。",
        "AI 技術正在改變世界，ChatGPT 是一個很好的例子。",
        "這裡沒有英文內容。"
    ]
    
    print("\n開始測試英文翻譯和替換功能...")
    print("=" * 60)
    
    for i, test_text in enumerate(test_cases, 1):
        print(f"\n測試案例 {i}:")
        print(f"原始文本: {test_text}")
        
        try:
            # 調用翻譯方法
            result = await translation_service.translate_english_to_chinese(test_text)
            
            print(f"原始英文: {result.original_texts}")
            print(f"中文翻譯: {result.translated_texts}")
            print(f"處理後文本: {result.processed_content}")
            
            # 驗證結果
            if result.original_texts and result.translated_texts:
                print("✅ 發現並處理了英文內容")
                
                # 驗證替換是否成功
                for orig, trans in zip(result.original_texts, result.translated_texts):
                    if orig not in result.processed_content and trans in result.processed_content:
                        print(f"✅ 成功替換: {orig} -> {trans}")
                    else:
                        print(f"⚠️  替換可能有問題: {orig} -> {trans}")
            else:
                print("ℹ️  沒有發現英文內容")
                
        except Exception as e:
            print(f"❌ 測試失敗: {e}")
        
        print("-" * 40)


if __name__ == "__main__":
    print("英文翻譯功能測試")
    print("檢查環境變數 GEMINI_API_KEY 是否已設置...")
    
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ 請設置 GEMINI_API_KEY 環境變數")
        sys.exit(1)
    
    print("✅ GEMINI_API_KEY 已設置")
    
    # 運行測試
    asyncio.run(test_english_translation())
