import os
import google.generativeai as genai
from typing import Dict, Any, List
from app.core.config import settings
from app.models.podcast import PodcastGenerationRequest
from app.services.translation_service import TranslationService
from app.services.tts_service import TTSService
from app.services.crawler_service import ContentCrawlerService
from app.models.crawler import CrawledContent

class AIService:
    def __init__(self):
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-pro')
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
            
            async with ContentCrawlerService() as crawler:
                result = await crawler.crawl_topic_content(crawler_topic, max_articles=5)
                return result.content_items
                
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
- 語速估算：每分鐘約 200-250 字
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