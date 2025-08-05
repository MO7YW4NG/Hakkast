import os
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.models.openai import OpenAIModel
from app.core.config import settings
from app.models.podcast import PodcastScript, PodcastScriptContent, EnglishTranslationResult, HostConfig
from app.services.translation_service import TranslationService
from app.services.tts_service import TTSService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentService:
    """使用 Pydantic AI (TWCC AFS 和 Gemini)"""
 
    def __init__(self):
        
        self.twcc_model = None
        self.gemini_flash_model = None
        self.gemini_pro_model = None
        
        if settings.TWCC_API_KEY and settings.TWCC_BASE_URL:
            # TWCC AFS 
            logger.info("使用 TWCC AFS ...")
            os.environ["OPENAI_API_KEY"] = settings.TWCC_API_KEY
            os.environ["OPENAI_BASE_URL"] = settings.TWCC_BASE_URL
            self.twcc_model = OpenAIModel(settings.TWCC_MODEL_NAME)
        
        if settings.GEMINI_API_KEY:
            # Gemini 
            logger.info("使用 Gemini 模型...")
            os.environ["GEMINI_API_KEY"] = settings.GEMINI_API_KEY
            self.gemini_flash_model = GeminiModel('gemini-2.5-flash')    
            self.gemini_pro_model = GeminiModel('gemini-2.0-pro') 
        
        # 對話 Agent
        self.dialogue_agent = Agent(
            model=self.gemini_flash_model,
            output_type=str,
            system_prompt="""
            你是Podcast主持人，請根據上下文和摘要，產生一段對話回應。
            請用繁體中文，以口語化方式回覆。
            """
        )    
        # 英文翻譯 agent
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
    async def translate_english_to_chinese(self, text: str) -> EnglishTranslationResult:
        """
        處理英文翻譯
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
            - 一定要翻譯所有英文內容，不要漏掉任何一個
            - 專業術語要準確翻譯
            - 使用常見中文譯名
            - 確保翻譯自然流暢
            """
            
            result = await self.english_translator.run(prompt)
            translation_data = result.output
            
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
            logger.error(f"English translation error: {e}")
            # 如果翻譯失敗，返回原文
            return EnglishTranslationResult(
                original_texts=[],
                translated_texts=[],
                processed_content=text
            )
            
    async def generate_reply(self, prompt: str) -> str:
        """生成對話回應"""
        result = await self.dialogue_agent.run(prompt)
        return result.output

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
    def __init__(self, name: str, personality: str, ai_service: AgentService):
        self.name = name
        self.personality = personality
        self.ai_service = ai_service

    async def reply(self, context_list, all_articles, current_article_idx, turn, is_last_turn):
        trimmed_context = trim_context(context_list[-6:])  # 只保留最近6輪
        context_text = "\n".join(trimmed_context)
        # article = all_articles[current_article_idx]
        transition = ""
        if is_last_turn and current_article_idx < len(all_articles) - 1:
            transition = (
                f"\n請在本輪發言結尾，自然地將話題帶到下一則新聞，不要用『接下來』等制式語，"
                f"而是用評論、延伸、或舉例的方式，讓對話順暢銜接到下一篇主題。"
                f"下一篇主題的重點是：{all_articles[current_article_idx+1].summary or all_articles[current_article_idx+1].content[:60]}"
            )

        prompt = (
            f"你是{self.name}，個性是{self.personality}。\n"
            f"請用{self.personality}的語氣，根據對話紀錄進行討論。\n"
            f"請一定要避免重複前面已經討論過的內容，盡量提出新的觀點、舉例或延伸討論，並與另一位主持人有互動。\n"
            f"每次發言**最多4句話**，請用像朋友之間輕鬆自然聊天方式，時不時加些有趣的回覆，內容要有深度與互動。"
            f"每句話之間請用句號分隔，回應前加上**「{self.name}: 」**"
            f"目前對話紀錄：\n{context_text}\n"
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
        self.translation_service = TranslationService()
        self.tts_service = TTSService()
        self.agent_service = AgentService()

    async def generate_podcast_script_with_agents(self, articles, max_minutes=25, hosts=None):
        """Generate podcast script using agent-based conversation (merged from agents.py)"""
        if hosts is None:
            hosts = [
                HostConfig(name="佳昀", gender="female", dialect="sihxian", personality="理性、專業、分析"),
                HostConfig(name="敏權", gender="male", dialect="sihxian", personality="幽默、活潑、互動")
            ]
        
        if len(hosts) < 2:
            raise ValueError("At least 2 hosts are required for podcast generation")
        

        # Use personality from HostConfig
        host_a = HostAgent(hosts[0].name, hosts[0].personality, self.agent_service)
        host_b = HostAgent(hosts[1].name, hosts[1].personality, self.agent_service)
        dialogue = []
        total_chars = 0
        max_chars = max_chars_for_duration(max_minutes)
        per_article_chars = max_chars // len(articles)
        turn = 0

        # 開場
        dialogue.append(f"{host_a.name}: 大家好，我是{host_a.name}。")
        dialogue.append(f"{host_b.name}: 我是{host_b.name}，歡迎收聽哈客播。")
        dialogue.append(f"{host_a.name}: 今天我們為大家帶來三則重要新聞，讓我們一起看看！")

        for idx, article in enumerate(articles):
            article_chars = 0

            # 用 LLM 產生精簡摘要
            summary_prompt = (
                "請你用自然的語氣，像朋友聊天一樣，順勢帶出下面這則新聞的重點摘要，"
                "不要用『這則新聞的重點是』、『接下來』等制式開頭，"
                "而是用評論、感想、或延伸話題的方式自然銜接，50字以內：\n"
                f"{article.content or article.summary}"
            )
            brief = await self.agent_service.generate_reply(summary_prompt)
            # 限制摘要最多四句
            sentences = brief.strip().split("。")
            intro = f"{host_a.name}: {'。'.join(sentences[:5]).strip()}"
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
            f"請你以{host_a.name}的身分，針對今天討論的三則新聞做一個重點總結。\n"
            f"本集三則新聞分別是：\n{news_list}\n"
            "請直接用自然語言總結今天的討論內容，務必不可出現任何[新聞一主題]、[省略]或任何佔位符，"
            f"內容要完整、精簡且貼合本集主題，約3~4句話，每句話用句號分隔，開頭加「{host_a.name}: 」"
        )
        summary_a = await self.agent_service.generate_reply(summary_prompt_a)
        dialogue.append(summary_a.strip())

        summary_prompt_b = (
            f"請你以{host_b.name}的身分，針對{host_a.name}的總結內容做補充或分享個人觀點，"
            f"語氣輕鬆，約2~3句話，每句話用句號分隔，開頭加「{host_b.name}: 」"
        )
        summary_b = await self.agent_service.generate_reply(summary_prompt_b)
        dialogue.append(summary_b.strip())

        ending_prompt_a = (
            f"請你以{host_a.name}的身分，用一段話做本集播客的溫馨結語，"
            f"內容要呼應今天討論的三則新聞，開頭加「{host_a.name}: 」，不要有任何佔位符。"
        )
        ending_a = await self.agent_service.generate_reply(ending_prompt_a)
        dialogue.append(ending_a.strip())

        def merge_same_speaker_lines(dialogue_lines):
            merged = []
            buffer = ""
            last_speaker = None
            for line in dialogue_lines:
                line = line.strip()
                if not line:
                    continue
                if line.startswith(f"{host_a.name}:"):
                    speaker = host_a.name
                elif line.startswith(f"{host_b.name}:"):
                    speaker = host_b.name
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
        
        # 處理英文轉換
        logger.info("正在處理腳本中的英文內容...")
        processed_lines = []
        session_translations = {}  # 本次會話的翻譯對照表
        
        def contains_english_chars(text: str) -> bool:
            """檢查文本是否包含英文字元"""
            import re
            return bool(re.search(r'[a-zA-Z]', text))
        
        def apply_translations(text: str) -> tuple[str, list]:
            """應用緩存的翻譯，返回處理後的文本和新增的翻譯"""
            processed_text = text
            
            # 檢查緩存中是否有匹配的翻譯
            for orig, trans in session_translations.items():
                if orig in processed_text:
                    processed_text = processed_text.replace(orig, trans)
            
            return processed_text
        
        for line in merged_lines:
            try:
                # 檢查是否包含英文字元，如果沒有則直接跳過
                if not contains_english_chars(line):
                    processed_lines.append(line)
                    continue
                
                # 先應用緩存的翻譯
                cached_result = apply_translations(line)
                
                # 如果緩存翻譯後還有英文字元，才發送新的翻譯請求
                if contains_english_chars(cached_result):
                    # 使用新的英文翻譯 agent 處理
                    translation_result = await self.agent_service.translate_english_to_chinese(cached_result)
                    
                    # 處理新的翻譯結果
                    if translation_result.original_texts:
                        # 儲存到會話翻譯表和全局緩存
                        logger.info(f"英文翻譯處理:")
                        for orig, trans in zip(translation_result.original_texts, translation_result.translated_texts):
                            session_translations[orig] = trans
                            logger.info(f"  {orig} -> {trans}")
                    
                    final_result = translation_result.processed_content
                else:
                    # 只使用了緩存翻譯
                    final_result = cached_result
                
                processed_lines.append(final_result)
                    
            except Exception as e:
                logger.error(f"處理行 '{line[:50]}...' 時發生錯誤: {e}")
                # 如果處理失敗，使用原始內容
                processed_lines.append(line)
        
        # 轉成結構化陣列
        content = []
        tts_content = []  # 新增：專為TTS準備的內容
        
        for i, line in enumerate(merged_lines):
            processed_line = processed_lines[i]
            
            if line.startswith(f"{host_a.name}:"):
                content.append(PodcastScriptContent(speaker=host_a.name, text=line[len(f"{host_a.name}:"):].strip()))
                tts_content.append(PodcastScriptContent(speaker=host_a.name, text=processed_line[len(f"{host_a.name}:"):].strip()))
            elif line.startswith(f"{host_b.name}:"):
                content.append(PodcastScriptContent(speaker=host_b.name, text=line[len(f"{host_b.name}:"):].strip()))
                tts_content.append(PodcastScriptContent(speaker=host_b.name, text=processed_line[len(f"{host_b.name}:"):].strip()))
        
        # 創建兩個版本的腳本
        podcast_script = PodcastScript(
            title="Hakkast 哈客播新聞討論",
            hosts=hosts,
            content=content
        )
        
        # TTS版本腳本
        tts_podcast_script = PodcastScript(
            title="Hakkast 哈客播新聞討論",
            hosts=hosts,
            content=tts_content
        )
        
        print(f"腳本字數：{sum(len(c.text) for c in content)}")
        
        # 返回包含TTS版本的結果
        return {
            "original_script": podcast_script,
            "tts_ready_script": tts_podcast_script
        }