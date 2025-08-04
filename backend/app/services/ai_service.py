import os
import google.generativeai as genai
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.models.openai import OpenAIModel
import asyncio
from datetime import datetime
from app.core.config import settings
from app.models.podcast import PodcastGenerationRequest, PodcastScript, PodcastScriptContent
from app.services.translation_service import TranslationService
from app.services.tts_service import TTSService
from app.services.crawl4ai_service import crawl_news
from app.models.crawler import CrawledContent

# 結構化的回應模型 (從 pydantic_ai_service.py 合併)
class PydanticPodcastScript(BaseModel):
    title: str
    hosts: List[str]  
    full_dialogue: str  
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


class EnglishTranslationResult(BaseModel):
    """英文翻譯結果模型"""
    original_texts: List[str]  # 翻譯前的英文文本列表
    translated_texts: List[str]  # 翻譯後的中文文本列表
    processed_content: str  # 替換英文後的完整文本


class PydanticAIService:
    """使用 Pydantic AI ( TWCC AFS 和 Gemini ) - 從 pydantic_ai_service.py 合併"""
 
    def __init__(self, use_twcc: bool = True):
        self.use_twcc = use_twcc
        
        if use_twcc and settings.TWCC_API_KEY and settings.TWCC_BASE_URL:
            # TWCC AFS 
            print("使用 TWCC AFS ...")
            os.environ["OPENAI_API_KEY"] = settings.TWCC_API_KEY
            os.environ["OPENAI_BASE_URL"] = settings.TWCC_BASE_URL
            self.model = OpenAIModel(settings.TWCC_MODEL_NAME)
        elif settings.GEMINI_API_KEY:
            # Gemini 
            print("使用 Gemini 模型...")
            os.environ["GEMINI_API_KEY"] = settings.GEMINI_API_KEY
            self.model = GeminiModel('gemini-2.5-flash')
            self.use_twcc = False
        else:
            raise ValueError("需要設定 TWCC_API_KEY + TWCC_BASE_URL 或 GEMINI_API_KEY")
        
        self.gemini_flash_model = GeminiModel('gemini-2.5-flash')    # 創建對話 Agent
        self.dialogue_agent = Agent(
            model=self.gemini_flash_model,
            output_type=str,
            system_prompt="""
            你是專業播客主持人，請根據上下文和新聞摘要，產生一段自然、深入的對話回應。
            請用繁體中文，風格專業且有深度。
            """
        )    
        # 初始化英文翻譯 agent (使用 Gemini 2.5 Pro)
        if settings.GEMINI_API_KEY:
            self.gemini_pro_model = GeminiModel('gemini-2.5-pro')  # 使用更強大的 Pro 版本
            self.english_translator = Agent(
                model=self.gemini_pro_model,
                output_type=EnglishTranslationResult,
                system_prompt="""
                你是一個專業的英文翻譯agent。你的任務是：
                1. 從輸入文本中識別並提取所有英文單字、片語和句子
                2. 將這些英文內容翻譯成自然流暢的繁體中文
                3. 提供翻譯前後的對照列表
                
                翻譯原則：
                - 保持原意不變
                - 使用自然的中文表達
                - 專業術語要準確翻譯
                - 品牌名稱使用常見中文譯名
                - 不需要英文註解
                """
            )
        else:
            self.gemini_pro_model = None
            self.english_translator = None
        
    async def generate_podcast_script(
        self, 
        request: PodcastGenerationRequest,
        crawled_content: Optional[List[CrawledContent]] = None,
        content_analysis: Optional[ContentAnalysis] = None
    ) -> PydanticPodcastScript:
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
        
        # 加入參考資料
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

            # 逐篇摘要
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
            # 用腳本生成 agent 產生腳本
            script = await self.script_generator.run(podcast_prompt)

            # 分段生成
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

            # 合併段落
            full_script = "\n\n".join(segments)
            
            # 暫時跳過英文處理，將在翻譯階段處理羅馬拼音中的英文
            print("跳過英文處理，將在翻譯階段處理...")
            tts_ready_script = full_script

            # 完整內容（對話腳本）
            full_content = f"""
            Podcast 標題：{script.title}

            主持人：{' 與 '.join(script.hosts)}

            {script.full_dialogue}
            """

            return {
                "success": True,
                "model_info": {"model_type": "TWCC AFS" if self.use_twcc else "Gemini"},
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
                "tts_ready_content": tts_ready_script,  # 新增：專為TTS準備的內容
                "generation_timestamp": datetime.now().isoformat(),
                "processing_steps": [
                    "內容需求分析",
                    "逐篇摘要",
                    "分段生成",
                    "英文轉換處理",
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

    def _create_fallback_script(self, request: PodcastGenerationRequest) -> PydanticPodcastScript:
        """創建備用腳本"""
        fallback_dialogue = f"""
        主持人A：
        歡迎收聽今天的播客節目，我是主持人A。

        主持人B：
        我是主持人B。今天我們要聊的主題是{request.topic}。

        主持人A：
        這確實是一個很有趣的話題，讓我們來深入討論一下。

        主持人B：
        沒錯，這個議題值得我們從多個角度來分析。

        主持人A：
        感謝大家今天的收聽，我們下次再見！
        """
        
        return PydanticPodcastScript(
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

    async def generate_reply(self, prompt: str, output_type=None) -> str:
        """生成對話回應"""
        if output_type:
            agent = Agent(model=self.model, output_type=output_type)
            result = await agent.run(prompt)
            return result.output
        else:
            # default:dialogue_agent
            result = await self.dialogue_agent.run(prompt)
            return result.output

    async def translate_english_to_chinese(self, text: str) -> EnglishTranslationResult:
        """
        使用 Gemini 2.5 Pro 處理英文翻譯
        1. 將英文從文本提取
        2. 翻譯成全中文文本  
        3. 回傳兩個列表，各自儲存翻譯前文本和翻譯後文本
        4. 將原文中的英文部分根據翻譯結果進行替換
        """
        if not self.english_translator:
            # 如果沒有翻譯 agent，返回空結果
            return EnglishTranslationResult(
                original_texts=[],
                translated_texts=[],
                processed_content=text
            )
        
        try:
            prompt = f"""
            請處理以下文本中的英文內容：

            輸入文本：
            {text}

            處理要求：
            1. 識別並提取文本中所有的英文單字、片語、句子
            2. 將這些英文內容翻譯成自然流暢的繁體中文
            3. 提供原文英文和中文翻譯的對照列表

            注意事項：
            - 專業術語要準確翻譯
            - 使用常見中文譯名
            - 保持原文的格式和結構
            - 確保翻譯自然流暢
            """
            
            result = await self.english_translator.run(prompt)
            translation_data = result.data
            
            # 進行英文替換，生成處理後的文本
            processed_content = text
            if translation_data.original_texts and translation_data.translated_texts:
                # 確保兩個列表長度一致
                min_length = min(len(translation_data.original_texts), len(translation_data.translated_texts))
                
                for i in range(min_length):
                    original_english = translation_data.original_texts[i]
                    chinese_translation = translation_data.translated_texts[i]
                    
                    # 替換原文中的英文部分
                    processed_content = processed_content.replace(original_english, chinese_translation)
            
            # 返回包含處理後內容的結果
            return EnglishTranslationResult(
                original_texts=translation_data.original_texts,
                translated_texts=translation_data.translated_texts,
                processed_content=processed_content
            )
            
        except Exception as e:
            print(f"English translation error: {e}")
            # 如果翻譯失敗，返回原文
            return EnglishTranslationResult(
                original_texts=[],
                translated_texts=[],
                processed_content=text
            )

    # async def convert_english_to_romanization(self, text: str) -> str:
    #     """將文本中的英文單字轉換成帶數字標調的羅馬拼音格式"""
    #     try:
    #         prompt = f"""
    #         請將以下文本中的英文單字轉換成帶數字標調的羅馬拼音格式，中文部分保持不變：

    #         原文：
    #         {text}

    #         轉換要求：
    #         1. 只轉換英文單字，中文完全不變
    #         2. 英文轉換成類似發音的羅馬拼音，每個音節加數字標調
    #         3. 標調規則：24=中平調，55=高平調，11=低平調，2=上聲，31=去聲
    #         4. 音節間用空格分隔
    #         5. 保持原有標點符號和格式
    #         6. 常見品牌使用標準音譯：
    #            - Apple → a24 pu24 er24
    #            - Google → gu24 ge24 er24
    #            - Facebook → fei24 si24 bu24 ke24
    #            - Microsoft → mai24 ke24 ro24 so24 fu24 te24
    #            - iPhone → ai24 feng24
    #            - ChatGPT → cha24 te24 ji24 pi24 ti24

    #         請直接輸出轉換後的完整文本：
    #         """
            
    #         result = await self.english_romanizer.run(prompt)
    #         return result.data
    #     except Exception as e:
    #         print(f"English romanization error: {e}")
    #         # 如果轉換失敗，返回原文
    #         return text

    # async def process_romanization_for_tts(self, romanization_text: str) -> str:
    #     """專門處理romanization欄位中的英文單字，為TTS系統準備統一格式"""
    #     try:
    #         # 檢查是否包含沒有數字標調的英文單字
    #         import re
            
    #         # 尋找英文單字（字母組成但沒有數字標調）
    #         english_words = re.findall(r'\b[a-zA-Z]+\b', romanization_text)
            
    #         if not english_words:
    #             print("未檢測到需要處理的英文單字")
    #             return romanization_text
            
    #         print(f"檢測到英文單字: {english_words}")
            
    #         # 為每個英文單字添加標調
    #         processed_text = romanization_text
            
    #         for word in english_words:
    #             # 轉換英文單字為帶標調的羅馬拼音
    #             converted_word = await self.convert_english_word_to_toned_romanization(word)
                
    #             # 替換原文中的英文單字
    #             processed_text = re.sub(r'\b' + re.escape(word) + r'\b', converted_word, processed_text)
    #             print(f"轉換: {word} → {converted_word}")
            
    #         return processed_text
            
    #     except Exception as e:
    #         print(f"Romanization processing error: {e}")
    #         return romanization_text

    # async def convert_english_word_to_toned_romanization(self, english_word: str) -> str:
    #     """將單個英文單字轉換為帶數字標調的羅馬拼音"""
    #     try:
    #         import re
            
    #         prompt = f"""
    #         請將英文單字 "{english_word}" 轉換成帶數字標調的羅馬拼音格式，用於客家話TTS系統。

    #         轉換規則：
    #         1. 將英文單字分解成音節
    #         2. 每個音節添加數字標調（主要使用24=中平調）
    #         3. 音節間用空格分隔
    #         4. 不要包含原英文單字，只輸出羅馬拼音

    #         常見轉換範例：
    #         - Apple → a24 pu24 er24
    #         - Google → gu24 ge24 er24
    #         - Facebook → fei24 si24 bu24 ke24
    #         - iPhone → ai24 feng24
    #         - Hakkast → ha24 ka24 si24 te24
    #         - ChatGPT → cha24 te24 ji24 pi24 ti24

    #         請只輸出轉換後的羅馬拼音（包含數字標調）：
    #         """
            
    #         result = await self.english_romanizer.run(prompt)
    #         converted = result.data.strip()
            
    #         # 確保輸出包含數字標調
    #         if not re.search(r'\d+', converted):
    #             # 如果沒有數字標調，使用簡單的後備方案
    #             syllables = self.simple_syllable_split(english_word)
    #             converted = ' '.join([f"{syl}24" for syl in syllables])
            
    #         return converted
            
    #     except Exception as e:
    #         print(f"English word conversion error for '{english_word}': {e}")
    #         # 簡單後備方案
    #         syllables = self.simple_syllable_split(english_word)
    #         return ' '.join([f"{syl}24" for syl in syllables])

    # def simple_syllable_split(self, word: str) -> list:
    #     """簡單的英文單字音節分割（後備方案）"""
    #     word = word.lower()
        
    #     # 常見單字的音節分割
    #     common_splits = {
    #         'apple': ['a', 'pu', 'er'],
    #         'google': ['gu', 'ge', 'er'],
    #         'facebook': ['fei', 'si', 'bu', 'ke'],
    #         'microsoft': ['mai', 'ke', 'ro', 'so', 'fu', 'te'],
    #         'iphone': ['ai', 'feng'],
    #         'hakkast': ['ha', 'ka', 'si', 'te'],
    #         'chatgpt': ['cha', 'te', 'ji', 'pi', 'ti'],
    #         'youtube': ['you', 'tu', 'be'],
    #         'openai': ['o', 'pen', 'ai'],
    #         'android': ['an', 'zhuo', 'yi', 'de']
    #     }
        
    #     if word in common_splits:
    #         return common_splits[word]
        
    #     # 簡單分割：每2-3個字母一組
    #     syllables = []
    #     i = 0
    #     while i < len(word):
    #         if i + 2 < len(word):
    #             syllables.append(word[i:i+2])
    #             i += 2
    #         else:
    #             syllables.append(word[i:])
    #             break
        
    #     return syllables


# Constants and utility functions from agents.py
CONTEXT_WINDOW_TOKENS = 32000

#估算token數量
def count_tokens(text):
    return int(len(text) / 1.5)

def trim_context(context_list, max_tokens=CONTEXT_WINDOW_TOKENS):
    trimmed = []
    total_tokens = 0
    for line in reversed(context_list):
        tokens = count_tokens(line)
        if total_tokens + tokens > max_tokens:
            break
        trimmed.insert(0, line)
        total_tokens += tokens
    return trimmed

def max_chars_for_duration(minutes):
    return int(minutes * 120)

#定義兩個主持人佳昀/敏權
class HostAgent:
    def __init__(self, name, personality, ai_service):
        self.name = name
        self.personality = personality
        self.ai_service = ai_service

    async def reply(self, context_list, all_articles, current_article_idx, turn, is_last_turn):
        trimmed_context = trim_context(context_list[-6:])  # 只保留最近6輪
        context_text = "\n".join(trimmed_context)
        article = all_articles[current_article_idx]
        transition = ""
        if is_last_turn and current_article_idx < len(all_articles) - 1:
            transition = (
                f"\n請在本輪發言結尾，自然地將話題帶到下一則新聞，不要用『接下來』等制式語，"
                f"而是用評論、延伸、或舉例的方式，讓對話順暢銜接到下一篇主題。"
                f"下一篇主題的重點是：{all_articles[current_article_idx+1].summary or all_articles[current_article_idx+1].content[:60]}"
            )

        prompt = (
            f"你是{self.name}，個性是{self.personality}。\n"
            f"請用{self.personality}的語氣，根據目前對話紀錄進行討論。\n"
            f"目前對話紀錄：\n{context_text}\n"
            f"請一定要避免重複前面已經討論過的內容，盡量提出新的觀點、舉例或延伸討論，並與另一位主持人有互動。\n"
            f"每次發言最多4句話，全程請用像朋友之間輕鬆自然聊天方式，時不時加些有趣的回覆，內容要有深度與互動。"
            f"每句話之間請用句號分隔，回應前加上「{self.name}: 」"
            f"{transition}"
        )
        response = await self.ai_service.generate_reply(prompt)
        sentences = response.split("。")
        limited = "。".join(sentences[:4]).strip()
        if not limited.startswith(f"{self.name}:"):
            limited = f"{self.name}: {limited}"
        return limited + ("。" if not limited.endswith("。") else "")


class AIService:
    def __init__(self):
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            self.model = None
        
        self.translation_service = TranslationService()
        self.tts_service = TTSService()
    
    async def generate_hakka_podcast_content(self, request: PodcastGenerationRequest) -> Dict[str, Any]:
        """
        Generate Hakka podcast content using the enhanced 4-step pipeline:
        1. Crawl latest content for the topic (if applicable)
        2. Generate Traditional Chinese script using Gemini + crawled content
        3. Translate Chinese to Hakka
        4. Generate Hakka TTS audio
        """
        
        try:
            # Step 1: Crawl latest content for dynamic topics
            crawled_content = await self._crawl_topic_content(request.topic)
            
            # Step 2: Generate Traditional Chinese content using Gemini + crawled content
            chinese_content = await self._generate_chinese_content(request, crawled_content)
            
            # Step 3: Translate Chinese to Hakka
            translation_result = await self.translation_service.translate_chinese_to_hakka(
                chinese_content["content"]
            )
            
            # Step 4: Generate Hakka TTS audio
            tts_result = await self.tts_service.generate_hakka_audio(
                translation_result["hakka_text"],
                translation_result["romanization"]
            )
            
            return {
                "title": chinese_content["title"],
                "chinese_content": chinese_content["content"],
                "hakka_content": translation_result["hakka_text"],
                "romanization": translation_result["romanization"],
                "audio_url": tts_result.get("audio_url"),
                "audio_duration": tts_result.get("duration", 0),
                "sources_used": chinese_content.get("sources_used", []),
                "crawled_articles": len(crawled_content) if crawled_content else 0
            }
            
        except Exception as e:
            print(f"Error in AI pipeline: {e}")
            return await self._generate_fallback_content(request)
    
    async def _crawl_topic_content(self, topic: str) -> List[CrawledContent]:
        """Crawl latest content for dynamic topics like news or research"""
        try:
            # Check if topic requires crawling
            crawling_keywords = [
                "news", "latest", "recent", "current", "update", "research", 
                "gaming", "technology", "science", "politics", "economics"
            ]
            
            topic_lower = topic.lower()
            should_crawl = any(keyword in topic_lower for keyword in crawling_keywords)
            
            if not should_crawl:
                return []
            
            # Determine appropriate crawler topic
            crawler_topic = self._map_to_crawler_topic(topic_lower)
            if not crawler_topic:
                return []
            
            # Use crawl_news function from crawl4ai_service
            result = await crawl_news(crawler_topic, max_articles=5)
            return result
                
        except Exception as e:
            print(f"Error crawling content for topic '{topic}': {e}")
            return []
    
    def _map_to_crawler_topic(self, topic: str) -> str:
        """Map user topic to predefined crawler configurations"""
        mapping = {
            "gaming": "gaming_news",
            "game": "gaming_news", 
            "video game": "gaming_news",
            "esports": "gaming_news",
            "deep learning": "research_deep_learning",
            "machine learning": "research_deep_learning", 
            "ai research": "research_deep_learning",
            "neural network": "research_deep_learning",
            "technology": "technology_news",
            "tech": "technology_news",
            "startup": "technology_news",
            "health": "health_wellness",
            "wellness": "health_wellness",
            "fitness": "health_wellness",
            "climate": "climate_environment",
            "environment": "climate_environment",
            "sustainability": "climate_environment",
            "finance": "finance_economics",
            "economics": "finance_economics",
            "investment": "finance_economics"
        }
        
        for keyword, crawler_topic in mapping.items():
            if keyword in topic:
                return crawler_topic
        
        return ""

    async def _generate_chinese_content(self, request: PodcastGenerationRequest, crawled_content: List[CrawledContent] = None) -> Dict[str, Any]:
        """Generate Traditional Chinese content using Gemini AI"""
        
        if not self.model:
            return self._generate_chinese_fallback(request)
        
        try:
            prompt = self._build_chinese_prompt(request, crawled_content)
            response = self.model.generate_content(prompt)
            
            # Parse the response
            content = response.text
            title = self._extract_title(content)
            
            # Extract sources used
            sources_used = []
            if crawled_content:
                sources_used = list(set(item.source for item in crawled_content))
            
            return {
                "title": title,
                "content": content,
                "sources_used": sources_used
            }
        except Exception as e:
            print(f"Error generating Chinese content with Gemini: {e}")
            return self._generate_chinese_fallback(request)
    
    def _build_chinese_prompt(self, request: PodcastGenerationRequest, crawled_content: List[CrawledContent] = None) -> str:
        """Build the prompt for generating Traditional Chinese content"""
        
        tone_instructions = {
            "casual": "使用親切、對話的語調，就像和好朋友聊天一樣。",
            "educational": "採用資訊豐富的教學風格，清楚解釋概念。",
            "storytelling": "運用敘事技巧和引人入勝的故事元素。",
            "interview": "以訪談格式結構化，包含問題和詳細回答。"
        }
        
        # Add crawled content to prompt if available
        current_content_section = ""
        if crawled_content:
            current_content_section = "\n\n最新相關資訊參考：\n"
            for i, content in enumerate(crawled_content[:3], 1):  # Limit to top 3 articles
                current_content_section += f"\n{i}. 標題：{content.title}\n"
                current_content_section += f"   來源：{content.source}\n"
                current_content_section += f"   摘要：{content.summary}\n"
            current_content_section += "\n請根據以上最新資訊，結合客家文化視角進行播客內容創作。"
        
        prompt = f"""
請為以下主題創建一個 {request.duration} 分鐘的客家文化播客腳本："{request.topic}"

要求：
- 使用繁體中文撰寫
- {tone_instructions.get(request.tone, '使用親切、對話的語調')}
- 專注於客家文化、傳統和遺產
- 內容要引人入勝且真實
- 包含文化背景和歷史脈絡
- 結構清晰：開場白、主要內容、結語
- 語速估算：每分鐘約 50 字
{current_content_section}

{"個人興趣融入：" + request.interests if request.interests else ""}

請在第一行提供吸引人的標題，然後提供完整的播客腳本。
內容應該適合後續翻譯為客家話並製作成語音播客。
"""
        
        return prompt
    
    def _extract_title(self, content: str) -> str:
        """Extract title from the generated content"""
        lines = content.strip().split('\n')
        if lines:
            # First non-empty line is likely the title
            for line in lines:
                if line.strip():
                    return line.strip()
        return "Hakka Podcast"
    
    def _generate_chinese_fallback(self, request: PodcastGenerationRequest) -> Dict[str, Any]:
        """Generate fallback Chinese content when Gemini is not available"""
        
        fallback_content = f"""
{request.topic} - 客家文化探索

歡迎來到我們的客家播客！今天我們要探討關於{request.topic}這個迷人的主題。

[這是演示版本。如需AI生成內容，請在.env文件中配置您的Gemini API密鑰。]

客家文化擁有豐富的傳統和歷史。我們的祖先從中國北方遷徙而來，帶來了獨特的習俗、語言和飲食傳統，這些都被世代保存下來。

無論我們以{request.tone}的方式討論{request.topic}，總有新的發現等著我們去探索客家文化遺產。從傳統歌謠和故事到古老智慧的現代詮釋，客家文化在保持核心價值的同時持續發展。

客家話本身就是一個表達寶庫，捕捉了我們民族堅韌不拔和社區精神的精髓。通過這些播客，我們希望與母語使用者和正在學習文化遺產的人們分享這美麗的文化。

感謝您加入我們的文化之旅。下次見，繼續探索和慶祝您的客家根源！

[時長：約{request.duration}分鐘]
"""
        
        return {
            "title": f"{request.topic} - 客家文化探索",
            "content": fallback_content
        }
    
    async def _generate_fallback_content(self, request: PodcastGenerationRequest) -> Dict[str, Any]:
        """Generate complete fallback content when services are not available"""
        
        chinese_content = self._generate_chinese_fallback(request)
        
        # Mock translation
        hakka_content = chinese_content["content"].replace("歡迎", "歡迎汝").replace("我們", "俚")
        
        return {
            "title": chinese_content["title"],
            "chinese_content": chinese_content["content"],
            "hakka_content": hakka_content,
            "romanization": "",
            "audio_url": None,
            "audio_duration": 0
        }

    async def generate_podcast_script_with_agents(self, articles, max_minutes=25):
        """Generate podcast script using agent-based conversation (merged from agents.py)"""
        ai_service = PydanticAIService()
        host_a = HostAgent("佳昀", "理性、專業、分析", ai_service)
        host_b = HostAgent("敏權", "幽默、活潑、互動", ai_service)
        dialogue = []
        total_chars = 0
        max_chars = max_chars_for_duration(max_minutes)
        per_article_chars = max_chars // len(articles)
        turn = 0

        # 開場
        dialogue.append("佳昀: 大家好，我是佳昀。")
        dialogue.append("敏權: 我是敏權，歡迎收聽Hakkast 哈客播。")
        dialogue.append("佳昀: 今天我們為大家帶來三則重要新聞，讓我們一起看看！")

        for idx, article in enumerate(articles):
            article_chars = 0

            # 用 LLM 產生精簡摘要
            summary_prompt = (
                "請你用自然的語氣，像朋友聊天一樣，順勢帶出下面這則新聞的重點摘要，"
                "不要用『這則新聞的重點是』、『接下來』等制式開頭，"
                "而是用評論、感想、或延伸話題的方式自然銜接，50字以內：\n"
                f"{article.content or article.summary}"
            )
            brief = await ai_service.generate_reply(summary_prompt)
            # 限制摘要最多四句
            sentences = brief.strip().split("。")
            intro = f"佳昀: {'。'.join(sentences[:5]).strip()}"
            dialogue.append(intro)

            for round in range(30):
                is_last_turn = (article_chars + 100 > per_article_chars * 0.95)
                if article_chars > per_article_chars * 0.95 or total_chars > max_chars * 0.95:
                    break  
                if turn % 2 == 0:
                    reply = await host_a.reply(dialogue, articles, idx, turn, is_last_turn)
                else:
                    reply = await host_b.reply(dialogue, articles, idx, turn, is_last_turn)
                dialogue.append(reply)
                total_chars += len(reply)
                article_chars += len(reply)
                turn += 1

        # 三篇新聞討論完，進入收尾
        news_list = "\n".join([f"{i+1}. {(a.summary or a.content)[:60]}" for i, a in enumerate(articles)])

        summary_prompt_a = (
            f"請你以佳昀的身分，針對今天討論的三則新聞做一個重點總結。\n"
            f"本集三則新聞分別是：\n{news_list}\n"
            "請直接用自然語言總結今天的討論內容，務必不可出現任何[新聞一主題]、[省略]或任何佔位符，"
            "內容要完整、精簡且貼合本集主題，約3~4句話，每句話用句號分隔，開頭加「佳芸: 」"
        )
        summary_a = await ai_service.generate_reply(summary_prompt_a)
        dialogue.append(summary_a.strip())

        summary_prompt_b = (
            "請你以敏權的身分，針對佳昀的總結內容做補充或分享個人觀點，"
            "語氣輕鬆，約2~3句話，每句話用句號分隔，開頭加「敏權: 」"
        )
        summary_b = await ai_service.generate_reply(summary_prompt_b)
        dialogue.append(summary_b.strip())

        ending_prompt_a = (
            "請你以佳昀的身分，用一段話做本集播客的溫馨結語，"
            "內容要呼應今天討論的三則新聞，開頭加「佳昀: 」，不要有任何佔位符。"
        )
        ending_a = await ai_service.generate_reply(ending_prompt_a)
        dialogue.append(ending_a.strip())

        def merge_same_speaker_lines(dialogue_lines):
            merged = []
            buffer = ""
            last_speaker = None
            for line in dialogue_lines:
                line = line.strip()
                if not line:
                    continue
                if line.startswith("佳昀:"):
                    speaker = "佳昀"
                elif line.startswith("敏權:"):
                    speaker = "敏權"
                else:
                    speaker = None

                if speaker and speaker == last_speaker:
                    buffer += " " + line[len(speaker)+1:].strip()
                else:
                    if buffer:
                        merged.append(buffer)
                    buffer = line
                    last_speaker = speaker
            if buffer:
                merged.append(buffer)
            return merged

        # 合併同主持人發言，並在不同主持人時換行
        merged_lines = merge_same_speaker_lines(dialogue)
        
        # 處理英文轉換 - 使用 Gemini 2.5 Pro 英文翻譯 agent
        print("正在處理腳本中的英文內容...")
        processed_lines = []
        
        # 初始化翻譯服務
        translation_service = PydanticAIService(use_twcc=False)  # 強制使用 Gemini
        
        for line in merged_lines:
            try:
                # 使用新的英文翻譯 agent 處理每一行
                translation_result = await translation_service.translate_english_to_chinese(line)
                
                # 如果有英文內容被翻譯，顯示翻譯對照
                if translation_result.original_texts:
                    print(f"英文翻譯處理:")
                    for orig, trans in zip(translation_result.original_texts, translation_result.translated_texts):
                        print(f"  {orig} -> {trans}")
                
                # 使用處理後的內容（無論是否有翻譯都包含在 processed_content 中）
                processed_lines.append(translation_result.processed_content)
                    
            except Exception as e:
                print(f"處理行 '{line[:50]}...' 時發生錯誤: {e}")
                # 如果處理失敗，使用原始內容
                processed_lines.append(line)
        
        # 轉成結構化陣列
        content = []
        tts_content = []  # 新增：專為TTS準備的內容
        
        for i, line in enumerate(merged_lines):
            processed_line = processed_lines[i]
            
            if line.startswith("佳昀:"):
                content.append(PodcastScriptContent(speaker="佳昀", text=line[len("佳昀:"):].strip()))
                tts_content.append(PodcastScriptContent(speaker="佳昀", text=processed_line[len("佳昀:"):].strip()))
            elif line.startswith("敏權:"):
                content.append(PodcastScriptContent(speaker="敏權", text=line[len("敏權:"):].strip()))
                tts_content.append(PodcastScriptContent(speaker="敏權", text=processed_line[len("敏權:"):].strip()))
        
        # 創建兩個版本的腳本
        podcast_script = PodcastScript(
            title="Hakkast 哈客播新聞討論",
            hosts=["佳昀", "敏權"],
            content=content
        )
        
        # TTS版本腳本
        tts_podcast_script = PodcastScript(
            title="Hakkast 哈客播新聞討論",
            hosts=["佳昀", "敏權"],
            content=tts_content
        )
        
        print(f"腳本字數：{sum(len(c.text) for c in content)}")
        
        # 返回包含TTS版本的結果
        return {
            "original_script": podcast_script,
            "tts_ready_script": tts_podcast_script
        }

    # async def process_romanization_for_tts(self, romanization_text: str) -> str:
    #     """專門處理romanization欄位中的英文單字，為TTS系統準備統一格式"""
    #     try:
    #         # 檢查是否包含沒有數字標調的英文單字
    #         import re
            
    #         # 尋找英文單字（字母組成但沒有數字標調）
    #         english_words = re.findall(r'\b[a-zA-Z]+\b', romanization_text)
            
    #         if not english_words:
    #             return romanization_text
            
    #         # 處理每個英文單字
    #         processed_text = romanization_text
    #         for word in english_words:
    #             try:
    #                 converted_word = await self.convert_english_word_to_toned_romanization(word)
    #                 # 替換原文中的英文單字
    #                 processed_text = processed_text.replace(word, converted_word)
    #                 print(f"英文轉換: {word} -> {converted_word}")
    #             except Exception as e:
    #                 print(f"轉換英文單字 '{word}' 失敗: {e}")
    #                 continue
            
    #         return processed_text
            
    #     except Exception as e:
    #         print(f"處理romanization失敗: {e}")
    #         return romanization_text

#     async def convert_english_word_to_toned_romanization(self, english_word: str) -> str:
#         """將單個英文單字轉換為帶標調的羅馬拼音"""
#         import re
        
#         try:
#             if not self.model:
#                 # 如果沒有模型，使用簡單分割
#                 syllables = self.simple_syllable_split(english_word)
#                 return " ".join([f"{syl}24" for syl in syllables])
            
#             prompt = f"""
# 請將英文單字 "{english_word}" 轉換為客語羅馬拼音，每個音節都要有數字標調。

# 參考範例：
# - GitHub -> gi24 hab2
# - Machine -> ma24 sin24  
# - Learning -> lia24 ning24
# - Hakkast -> ha24 ka24 si24 te24

# 請只回傳轉換結果，不要其他說明。
# """
            
#             response = await self.model.generate_content_async(prompt)
#             result = response.text.strip()
            
#             if result and not re.search(r'[a-zA-Z]', result):
#                 return result
#             else:
#                 # 如果結果包含英文字母，使用後備方案
#                 syllables = self.simple_syllable_split(english_word)
#                 return " ".join([f"{syl}24" for syl in syllables])
                
#         except Exception as e:
#             print(f"AI轉換失敗: {e}")
#             # 使用簡單分割作為後備
#             syllables = self.simple_syllable_split(english_word)
#             return " ".join([f"{syl}24" for syl in syllables])

    # def simple_syllable_split(self, word: str) -> list:
    #     """簡單的音節分割，作為後備方案"""
    #     common_splits = {
    #         "GitHub": ["gi", "hab"],
    #         "Machine": ["ma", "sin"],
    #         "Learning": ["lia", "ning"],
    #         "Hakkast": ["ha", "ka", "si", "te"],
    #         "AI": ["ai"],
    #         "NHS": ["en", "ha", "si"],
    #         "API": ["a", "pi", "ai"]
    #     }
        
    #     if word in common_splits:
    #         return common_splits[word]
        
    #     # 默認每2-3個字母為一個音節
    #     syllables = []
    #     word_lower = word.lower()
    #     i = 0
    #     while i < len(word_lower):
    #         if i + 2 < len(word_lower):
    #             syllables.append(word_lower[i:i+2])
    #             i += 2
    #         else:
    #             syllables.append(word_lower[i:])
    #             break
        
    #     return syllables if syllables else [word.lower()]



async def generate_podcast_script_with_agents(articles, max_minutes=25):
    """
    Generate podcast script with agents - main function from agents.py
    This is the primary function for agent-based podcast script generation
    Returns both original and TTS-ready versions
    """
    ai_service_instance = AIService()
    result = await ai_service_instance.generate_podcast_script_with_agents(articles, max_minutes)
    
    # 為了向後兼容，如果調用者期待單一腳本，返回原始腳本
    # 但同時提供TTS版本
    if isinstance(result, dict) and "original_script" in result:
        # 新格式：返回字典包含兩個版本
        return result
    else:
        # 舊格式：返回單一腳本（向後兼容）
        return result