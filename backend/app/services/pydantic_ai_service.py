"""
Pydantic AI Service for Hakka Podcast Generation
使用 Pydantic AI 框架重構的 AI 服務，支援 TWCC AFS 和 Gemini 模型
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.models.openai import OpenAIModel
import asyncio
import os
from datetime import datetime

from app.core.config import settings
from app.models.podcast import PodcastGenerationRequest
from app.models.crawler import CrawledContent


# 定義結構化的回應模型
class PodcastScript(BaseModel):
    """播客腳本結構化模型"""
    title: str
    hosts: List[str]  # 主持人名單
    full_dialogue: str  # 完整的對話腳本
    estimated_duration_minutes: int
    key_points: List[str]
    sources_mentioned: List[str]


class ContentAnalysis(BaseModel):
    """內容分析結果模型"""
    topic_category: str
    complexity_level: str  # "beginner", "intermediate", "advanced"
    target_audience: str
    recommended_style: str
    content_freshness: str  # "current", "evergreen", "historical"


class PydanticAIService:
    """使用 Pydantic AI 的新 AI 服務，支援 TWCC AFS 和 Gemini 模型"""
    
    def __init__(self, use_twcc: bool = True):
        self.use_twcc = use_twcc
        
        if use_twcc and settings.TWCC_API_KEY and settings.TWCC_BASE_URL:
            # 使用 TWCC AFS 模型
            print("🔧 使用 TWCC AFS 模型...")
            # 設定環境變數供 OpenAI 客戶端使用
            os.environ["OPENAI_API_KEY"] = settings.TWCC_API_KEY
            os.environ["OPENAI_BASE_URL"] = settings.TWCC_BASE_URL
            self.model = OpenAIModel(settings.TWCC_MODEL_NAME)
        elif settings.GEMINI_API_KEY:
            # 使用 Gemini 模型作為備選
            print("🔧 使用 Gemini 模型...")
            # 設定環境變數供 Gemini 客戶端使用
            os.environ["GEMINI_API_KEY"] = settings.GEMINI_API_KEY
            self.model = GeminiModel('gemini-1.5-flash')
            self.use_twcc = False
        else:
            raise ValueError("需要設定 TWCC_API_KEY + TWCC_BASE_URL 或 GEMINI_API_KEY")
        
        # 創建內容分析 Agent
        self.content_analyzer = Agent(
            model=self.model,
            result_type=ContentAnalysis,
            system_prompt="""
            你是一位專業的內容分析師，專門分析播客主題和受眾需求。
            分析用戶提供的主題，判斷：
            1. 主題類別（科技、娛樂、教育、新聞等）
            2. 複雜度等級（初學者、中級、高級）
            3. 目標受眾
            4. 推薦的播客風格
            5. 內容時效性
            
            請用繁體中文回應，並提供專業的分析結果。
            """
        )
        
        # 創建腳本生成 Agent
        self.script_generator = Agent(
            model=self.model,
            result_type=PodcastScript,
            system_prompt="""
            你是一位專業的播客腳本創作者，專門創作雙主持人深度對話形式的新聞分析播客。

            腳本格式要求：
            1. 標題：準確且吸引人，反映新聞核心議題
            2. 雙主持人：主持人A和主持人B進行深入對話分析
            3. 完整對話腳本特色：
               - 開場：介紹節目和當天主題
               - 新聞背景：詳細介紹新聞事件
               - 深度分析：從多角度分析事件意義和影響
               - 地緣政治：分析背後的國際關係和戰略考量
               - 經濟層面：討論貿易、經濟合作等議題
               - 總結：歸納重點和後續發展預測
               - 結尾：感謝收聽和預告
               
            4. 對話風格：
               - 專業深入但通俗易懂
               - 一問一答，互相補充和深入
               - 每段對話都有實質內容，避免空洞
               - 包含具體的數據、事實和背景資訊
               - 每段對話前標註說話者（🎙️主持人A: / 🎙️主持人B:）
               
            5. 內容深度要求：
               - 分析新聞背後的深層原因
               - 討論地緣政治和戰略意義
               - 解釋複雜的國際關係
               - 提供多角度的觀點
               - 預測可能的後續發展
               
            6. 長度要求：生成足夠長的對話內容，確實符合目標時長
            
            參考優質對話風格：
            - 不只陳述事實，還要分析原因和影響
            - 用"沒錯，而且..."、"對，但有趣的是..."等過渡語
            - 包含"從新聞來看..."、"這背後可不單純..."等分析性語句
            - 總結時用"我們總結一下今天的重點..."
            
            請用繁體中文撰寫，風格專業且有深度。
            """
        )

    async def analyze_content_requirements(self, topic: str, tone: str = "casual") -> ContentAnalysis:
        """分析內容需求和受眾"""
        try:
            result = await self.content_analyzer.run(
                f"請分析這個播客主題：'{topic}'，播客風格偏向：{tone}"
            )
            return result.data
        except Exception as e:
            print(f"Content analysis error: {e}")
            # 返回預設分析結果
            return ContentAnalysis(
                topic_category="通用",
                complexity_level="intermediate",
                target_audience="一般聽眾",
                recommended_style="對話式",
                content_freshness="evergreen"
            )

    async def generate_podcast_script(
        self, 
        request: PodcastGenerationRequest,
        crawled_content: Optional[List[CrawledContent]] = None,
        content_analysis: Optional[ContentAnalysis] = None
    ) -> PodcastScript:
        """生成結構化的播客腳本"""
        
        # 如果沒有內容分析，先進行分析
        if not content_analysis:
            content_analysis = await self.analyze_content_requirements(
                request.topic, 
                request.tone or "casual"
            )
        
        # 準備上下文資訊
        context_info = f"""
        主題：{request.topic}
        風格：{request.tone or 'casual'}
        目標時長：{request.duration or 10} 分鐘
        
        內容分析結果：
        - 類別：{content_analysis.topic_category}
        - 複雜度：{content_analysis.complexity_level}
        - 目標受眾：{content_analysis.target_audience}
        - 推薦風格：{content_analysis.recommended_style}
        - 內容時效性：{content_analysis.content_freshness}
        """
        
        # 如果有爬取的內容，加入參考資料
        if crawled_content:
            context_info += "\n\n參考資料：\n"
            for content in crawled_content[:3]:  # 限制使用前3篇文章
                context_info += f"- 標題：{content.title}\n  摘要：{content.summary[:200]}...\n"
        
        try:
            result = await self.script_generator.run(context_info)
            return result.data
        except Exception as e:
            print(f"Script generation error: {e}")
            # 返回備用腳本
            return self._create_fallback_script(request)

    async def generate_complete_podcast_content(
        self, 
        request: PodcastGenerationRequest,
        crawled_content: Optional[List[CrawledContent]] = None
    ) -> Dict[str, Any]:
        """完整的播客內容生成流程"""
        
        try:
            # Step 1: 分析內容需求
            print("🔍 正在分析內容需求...")
            content_analysis = await self.analyze_content_requirements(request.topic, request.tone)
            
            # Step 2: 生成結構化腳本
            print("📝 正在生成播客腳本...")
            script = await self.generate_podcast_script(request, crawled_content, content_analysis)
            
            # Step 3: 組合完整內容（對話式腳本）
            full_content = f"""
🎙️Podcast 標題：{script.title}

🎧主持人：{' 與 '.join(script.hosts)}

{script.full_dialogue}
"""
            
            return {
                "success": True,
                "model_info": {
                    "provider": "TWCC AFS" if self.use_twcc else "Google Gemini",
                    "model_name": settings.TWCC_MODEL_NAME if self.use_twcc else "gemini-1.5-flash"
                },
                "content_analysis": content_analysis.dict(),
                "structured_script": script.dict(),
                "full_content": full_content,
                "generation_timestamp": datetime.now().isoformat(),
                "processing_steps": [
                    "內容需求分析",
                    "結構化腳本生成", 
                    "內容整合完成"
                ]
            }
            
        except Exception as e:
            print(f"Complete generation error: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_content": self._create_fallback_script(request).dict()
            }

    def _create_fallback_script(self, request: PodcastGenerationRequest) -> PodcastScript:
        """創建備用腳本"""
        fallback_dialogue = f"""
🎙️主持人A：
歡迎收聽今天的播客節目，我是主持人A。

🎙️主持人B：
我是主持人B。今天我們要聊的主題是{request.topic}。

🎙️主持人A：
這確實是一個很有趣的話題，讓我們來深入討論一下。

🎙️主持人B：
沒錯，這個議題值得我們從多個角度來分析。

🎙️主持人A：
感謝大家今天的收聽，我們下次再見！
"""
        
        return PodcastScript(
            title=f"關於{request.topic}的討論",
            hosts=["主持人A", "主持人B"],
            full_dialogue=fallback_dialogue,
            estimated_duration_minutes=request.duration or 10,
            key_points=[f"{request.topic}相關要點"],
            sources_mentioned=["一般知識"]
        )


# 使用範例和測試函數
async def test_pydantic_ai_service(custom_topic: str = None, custom_tone: str = None, custom_duration: int = None):
    """測試 Pydantic AI 服務"""
    try:
        print("🧪 開始測試 Pydantic AI 服務...")
        
        # 測試 TWCC 模型（如果可用）
        try:
            service = PydanticAIService(use_twcc=True)
            print("✅ 成功初始化 TWCC AFS 服務")
        except Exception as e:
            print(f"⚠️ TWCC 初始化失敗: {e}")
            print("🔄 嘗試使用 Gemini 備用模型...")
            service = PydanticAIService(use_twcc=False)
            print("✅ 成功初始化 Gemini 服務")
        
        # 測試請求 - 支援自定義輸入
        test_request = PodcastGenerationRequest(
            topic=custom_topic or "客家傳統文化與現代科技的結合",
            tone=custom_tone or "educational",
            duration=custom_duration or 15
        )
        
        print(f"📋 測試主題: {test_request.topic}")
        print(f"📋 測試風格: {test_request.tone}")
        print(f"📋 目標時長: {test_request.duration} 分鐘")
        
        # 執行完整生成流程
        result = await service.generate_complete_podcast_content(test_request)
        print("🎉 生成結果：", result)
        return result
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_twcc_models():
    """測試不同的 TWCC 模型"""
    twcc_models = [
        "llama3.3-ffm-70b-32k-chat",  # 最新的 FFM 模型
        "llama3.1-ffm-70b-32k-chat",  # Llama3.1 FFM
        "llama3-ffm-70b-chat",        # Llama3 FFM
        "taide-lx-7b-chat"            # 台灣本土化模型
    ]
    
    for model_name in twcc_models:
        print(f"\n🧪 測試模型: {model_name}")
        try:
            # 暫時修改配置
            original_model = getattr(settings, 'TWCC_MODEL_NAME', '')
            settings.TWCC_MODEL_NAME = model_name
            
            service = PydanticAIService(use_twcc=True)
            
            test_request = PodcastGenerationRequest(
                topic="客家文化與AI科技",
                tone="casual",
                duration=10
            )
            
            result = await service.generate_complete_podcast_content(test_request)
            print(f"✅ {model_name} 測試成功")
            
            # 恢復原設定
            settings.TWCC_MODEL_NAME = original_model
            
        except Exception as e:
            print(f"❌ {model_name} 測試失敗: {e}")
            continue


async def test_with_custom_text():
    """使用自定義文本進行測試"""
    print("📝 自定義文本測試")
    print("=" * 50)
    
    # 基於您提供的新聞內容設計的客家播客主題
    custom_topics = [
        "菲律賓總統訪美：從客家人的國際視野看亞太局勢變化",
        "中美貿易關稅爭議：客家商人如何看待國際經濟局勢", 
        "南海紛爭與客家海外社群：東南亞華人的處境與思考",
        "美菲同盟關係：客家人在國際政治中的角色與觀點"
    ]
    
    service = PydanticAIService(use_twcc=True)
    
    for i, topic in enumerate(custom_topics, 1):
        print(f"\n🎯 測試主題 {i}: {topic}")
        print("-" * 50)
        
        # 根據主題調整風格和時長
        tone_map = ["educational", "casual", "storytelling", "interview"]
        duration_map = [12, 10, 15, 18]
        
        test_request = PodcastGenerationRequest(
            topic=topic,
            tone=tone_map[(i-1) % 4],
            duration=duration_map[(i-1) % 4]
        )
        
        print(f"📋 風格: {test_request.tone}")
        print(f"⏱️  時長: {test_request.duration} 分鐘")
        
        try:
            result = await service.generate_complete_podcast_content(test_request)
            
            if result.get("success"):
                script = result['structured_script']
                print(f"✅ 成功生成播客")
                print(f"🏷️  標題: {script['title']}")
                print(f"📝 開場預覽: {script['introduction'][:150]}...")
                print(f"🎯 關鍵要點: {', '.join(script['key_points'])}")
                print(f"📚 資料來源: {', '.join(script['sources_mentioned'])}")
                
                # 顯示完整腳本（限制長度以便閱讀）
                if i == 1:  # 只顯示第一個主題的完整腳本
                    print(f"\n📜 完整腳本預覽:")
                    print("=" * 40)
                    print(result['full_content'])
                    print("=" * 40)
            else:
                print(f"❌ 生成失敗: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ 測試失敗: {e}")
            
        print("\n" + "="*50)


if __name__ == "__main__":
    # 執行測試 - 您可以選擇要執行哪個測試
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "custom":
        # 執行自定義測試: python pydantic_ai_service.py custom
        asyncio.run(test_with_custom_text())
    else:
        # 執行標準測試: python pydantic_ai_service.py
        asyncio.run(test_pydantic_ai_service())
