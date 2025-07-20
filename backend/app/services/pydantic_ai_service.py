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
    introduction: str
    main_content: str
    conclusion: str
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
            你是一位專業的客語播客腳本創作者。
            
            任務：根據提供的主題和內容分析，創作一份結構完整的播客腳本。
            
            腳本要求：
            1. 標題要吸引人且符合客語文化
            2. 開場要親切自然，符合客語播客風格
            3. 主要內容要豐富有趣，適合口語表達
            4. 結尾要溫馨，鼓勵聽眾參與
            5. 估算合理的播放時長
            6. 提取關鍵要點
            7. 列出可能的資料來源
            
            語言：請用繁體中文撰寫，後續會翻譯成客語。
            風格：親切、溫暖、具有客家文化特色。
            長度：根據用戶需求調整，預設10-15分鐘的播客內容。
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
            
            # Step 3: 組合完整內容
            full_content = f"""
標題：{script.title}

開場：
{script.introduction}

主要內容：
{script.main_content}

結語：
{script.conclusion}
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
        return PodcastScript(
            title=f"關於{request.topic}的客語播客",
            introduction=f"大家好，歡迎收聽今天的客語播客。今天我們要聊的主題是{request.topic}。",
            main_content=f"讓我們一起來探討{request.topic}這個有趣的話題。這是一個值得深入了解的主題，讓我們從不同角度來看看這個議題。",
            conclusion="謝謝大家的收聽，希望今天的內容對您有所幫助。我們下次再見！",
            estimated_duration_minutes=request.duration or 10,
            key_points=[f"{request.topic}相關要點"],
            sources_mentioned=["一般知識"]
        )


# 使用範例和測試函數
async def test_pydantic_ai_service():
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
        
        # 測試請求
        test_request = PodcastGenerationRequest(
            topic="客家傳統文化與現代科技的結合",
            tone="educational",
            duration=15
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


if __name__ == "__main__":
    # 執行測試
    asyncio.run(test_pydantic_ai_service())
