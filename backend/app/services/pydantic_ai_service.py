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
            print("使用 TWCC AFS 模型...")
            # 設定環境變數供 OpenAI 客戶端使用
            os.environ["OPENAI_API_KEY"] = settings.TWCC_API_KEY
            os.environ["OPENAI_BASE_URL"] = settings.TWCC_BASE_URL
            self.model = OpenAIModel(settings.TWCC_MODEL_NAME)
        elif settings.GEMINI_API_KEY:
            # 使用 Gemini 模型作為備選
            print("使用 Gemini 模型...")
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
            6. 長度要求：生成足夠長的對話內容，確實符合目標時長（例如三篇新聞共15分鐘，每篇約5分鐘）
            7. 串接要求：三篇新聞請以自然的對話方式串接，主持人能順暢地從一則新聞帶到下一則新聞，讓聽眾感覺主題連貫。
            參考優質對話風格：
            - 不只陳述事實，還要分析原因和影響
            - 用"沒錯，而且..."、"對，但有趣的是..."等過渡語
            - 包含"從新聞來看..."、"這背後可不單純..."等分析性語句
            - 總結時用"我們總結一下今天的重點..."
            請用繁體中文撰寫，風格專業且有深度。
            """
        )
        
        # 新增摘要 agent
        self.summarizer = Agent(
            model=self.model,
            result_type=str,
            system_prompt="""
            你是一位專業新聞摘要員，只產生純文字摘要，不要主持人、對話或虛構內容。
            請用繁體中文，濃縮新聞重點，字數約500字。
            """
        )
        
        # 創建對話 Agent
        self.dialogue_agent = Agent(
            model=self.model,
            result_type=str,
            system_prompt="""
            你是專業播客主持人，請根據上下文和新聞摘要，產生一段自然、深入的對話回應。
            請用繁體中文，風格專業且有深度。
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
            for content in crawled_content[:3]:  
                context_info += (
                    f"- 標題：{content.title}\n"
                    f"  內容：{(content.content or content.summary)[:1500]}...\n"
                )
                
        try:
            result = await self.script_generator.run(context_info)
            return result.data
        except Exception as e:
            print(f"Script generation error: {e}")
            return self._create_fallback_script(request)

    async def generate_complete_podcast_content(
        self, 
        request: PodcastGenerationRequest,
        crawled_content: Optional[List[CrawledContent]] = None
    ) -> Dict[str, Any]:
        """完整的播客內容生成流程"""
        try:
            print("正在分析內容需求...")
            content_analysis = await self.analyze_content_requirements(request.topic, request.tone)

            # Step 1: 逐篇摘要
            summaries = []
            if crawled_content:
                for content in crawled_content[:3]:
                    summary = await self.summarize_article(content.content or content.summary)
                    summaries.append(f"標題：{content.title}\n摘要：{summary}\n來源：{content.url}")

            # Step 2: 合併摘要並由LLM產生腳本
            combined_summary = "\n\n".join(summaries)
            podcast_prompt = (
                "請根據以下三篇新聞的重點摘要，逐一分析並串接，"
                "生成一份約2200~2500字、15分鐘的雙主持人播客腳本。"
                "內容必須涵蓋三篇新聞的重點，且不要虛構：\n"
                f"{combined_summary}"
            )
            # 用腳本生成 agent 產生播客腳本
            script = await self.script_generator.run(podcast_prompt)

            # Step 2: 分段生成
            segments = []

            # 開場
            opening_prompt = (
                "請根據以下三篇新聞摘要，生成播客開場白（約700字），"
                "介紹主題並吸引聽眾：\n"
                f"{combined_summary}"
            )
            opening = await self.generate_podcast_script_segment(opening_prompt)
            segments.append(opening)

            # 三篇新聞分別生成
            for idx, summary in enumerate(summaries, 1):
                news_prompt = (
                    f"請根據以下新聞摘要，生成播客對話段落（約800字），"
                    f"主題：第{idx}篇新聞\n{summary}"
                )
                news_segment = await self.generate_podcast_script_segment(news_prompt)
                segments.append(news_segment)

            # 結尾
            closing_prompt = (
                "請根據以上內容，生成播客結尾總結（約400字），"
                "歸納重點並預告下集。"
            )
            closing = await self.generate_podcast_script_segment(closing_prompt)
            segments.append(closing)

            # 合併所有段落
            full_script = "\n\n".join(segments)

            # Step 3: 組合完整內容（對話式腳本）
            full_content = f"""
            🎙️Podcast 標題：{script.title}

            🎧主持人：{' 與 '.join(script.hosts)}

            {script.full_dialogue}
            """

            return {
                "success": True,
                "model_info": {...},
                "content_analysis": content_analysis.dict(),
                "structured_script": {
                    "title": script.title if 'script' in locals() else request.topic,
                    "hosts": ["主持人A", "主持人B"],
                    "full_dialogue": full_script,
                    "estimated_duration_minutes": request.duration,
                    "key_points": [],
                    "sources_mentioned": []
                },
                "full_content": full_script,
                "generation_timestamp": datetime.now().isoformat(),
                "processing_steps": [
                    "內容需求分析",
                    "逐篇摘要",
                    "分段生成",
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

    async def summarize_article(self, article_content: str) -> str:
        """用 LLM 產生單篇新聞摘要，避免幻覺"""
        prompt = f"請用550以內字摘要以下新聞內容，只用真實新聞細節，不要虛構：\n{article_content}"
        result = await self.summarizer.run(prompt)
        return str(result.data)

    async def generate_podcast_script_segment(self, segment_prompt: str) -> str:
        """分段生成播客腳本片段"""
        result = await self.script_generator.run(segment_prompt)
        return str(result.data.full_dialogue) if hasattr(result.data, "full_dialogue") else str(result.data)

    async def generate_reply(self, prompt: str) -> str:
        """生成對話回應"""
        result = await self.dialogue_agent.run(prompt)
        return str(result.data)


# 使用範例和測試函數
"""async def test_pydantic_ai_service(custom_topic: str = None, custom_tone: str = None, custom_duration: int = None):
    測試 Pydantic AI 服務
    try:
        print("開始測試 Pydantic AI 服務...")
        

        try:
            service = PydanticAIService(use_twcc=True)
            print("成功初始化 TWCC AFS 服務")
        except Exception as e:
            print(f"TWCC 初始化失敗: {e}")
            print("嘗試使用 Gemini 備用模型...")
            service = PydanticAIService(use_twcc=False)
            print("成功初始化 Gemini 服務")
        

        test_request = PodcastGenerationRequest(
            topic=custom_topic or "客家傳統文化與現代科技的結合",
            tone=custom_tone or "educational",
            duration=custom_duration or 15
        )
        
        print(f"測試主題: {test_request.topic}")
        print(f"測試風格: {test_request.tone}")
        print(f"目標時長: {test_request.duration} 分鐘")
        

        result = await service.generate_complete_podcast_content(test_request)
        print("生成結果：", result)
        return result
        
    except Exception as e:
        print(f"測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return None"""


"""async def test_twcc_models():
    測試不同的 TWCC 模型
    twcc_models = [
        "llama3.3-ffm-70b-32k-chat",  
        "llama3.1-ffm-70b-32k-chat",  
        "llama3-ffm-70b-chat",       
        "taide-lx-7b-chat"            
    ]
    
    for model_name in twcc_models:
        print(f"\n測試模型: {model_name}")
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
            print(f"{model_name} 測試失敗: {e}")
            continue"""

if __name__ == "__main__":
    # 執行測試 - 您可以選擇要執行哪個測試
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "custom":
        # 執行自定義測試: python pydantic_ai_service.py custom
        asyncio.run(test_with_custom_text())
    else:
        # 執行標準測試: python pydantic_ai_service.py
        asyncio.run(test_pydantic_ai_service())
