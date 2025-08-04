import os
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.models.openai import OpenAIModel
from app.core.config import settings
from app.models.podcast import PodcastScript, PodcastScriptContent, EnglishTranslationResult
from app.services.translation_service import TranslationService
from app.services.tts_service import TTSService

class AgentService:
    """使用 Pydantic AI (TWCC AFS 和 Gemini)"""
 
    def __init__(self):
        
        if settings.TWCC_API_KEY and settings.TWCC_BASE_URL:
            # TWCC AFS 
            print("使用 TWCC AFS ...")
            os.environ["OPENAI_API_KEY"] = settings.TWCC_API_KEY
            os.environ["OPENAI_BASE_URL"] = settings.TWCC_BASE_URL
            self.twcc_model = OpenAIModel(settings.TWCC_MODEL_NAME)
        
        if settings.GEMINI_API_KEY:
            # Gemini 
            print("使用 Gemini 模型...")
            os.environ["GEMINI_API_KEY"] = settings.GEMINI_API_KEY
            self.gemini_flash_model = GeminiModel('gemini-2.5-flash')    
            self.gemini_pro_model = GeminiModel('gemini-2.5-pro') 
        
        # 創建對話 Agent
        self.dialogue_agent = Agent(
            model=self.gemini_flash_model,
            output_type=str,
            system_prompt="""
            你是專業Podcast主持人，請根據上下文和新聞摘要，產生一段自然、深入的對話回應。
            請用繁體中文，風格專業且有深度。
            """
        )    
        # 初英文翻譯 agent
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
            print(f"English translation error: {e}")
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
        self.translation_service = TranslationService()
        self.tts_service = TTSService()

    async def generate_podcast_script_with_agents(self, articles, max_minutes=25):
        """Generate podcast script using agent-based conversation (merged from agents.py)"""
        ai_service = AgentService()
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
        
        # 處理英文轉換
        print("正在處理腳本中的英文內容...")
        processed_lines = []
        
        for line in merged_lines:
            try:
                # 使用新的英文翻譯 agent 處理每一行
                translation_result = await ai_service.translate_english_to_chinese(line)
                
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