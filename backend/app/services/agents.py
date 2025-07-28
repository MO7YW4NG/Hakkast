from app.services.pydantic_ai_service import PydanticAIService
from app.models.podcast import PodcastScript, PodcastScriptContent

CONTEXT_WINDOW_TOKENS = 32000

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

async def generate_podcast_script_with_agents(articles, max_minutes=25):
    ai_service = PydanticAIService()
    host_a = HostAgent("主持人A", "理性、專業、分析", ai_service)
    host_b = HostAgent("主持人B", "幽默、活潑、互動", ai_service)
    dialogue = []
    total_chars = 0
    max_chars = max_chars_for_duration(max_minutes)
    per_article_chars = max_chars // len(articles)
    turn = 0

    # 開場
    dialogue.append("主持人A: 大家好，我是主持人A。")
    dialogue.append("主持人B: 我是主持人B，歡迎收聽Hakkast 哈客播。")
    dialogue.append("主持人A: 今天我們為大家帶來三則重要新聞，讓我們一起看看！")

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
        intro = f"主持人A: {'。'.join(sentences[:5]).strip()}"
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
        f"請你以主持人A的身分，針對今天討論的三則新聞做一個重點總結。\n"
        f"本集三則新聞分別是：\n{news_list}\n"
        "請直接用自然語言總結今天的討論內容，務必不可出現任何[新聞一主題]、[省略]或任何佔位符，"
        "內容要完整、精簡且貼合本集主題，約3~4句話，每句話用句號分隔，開頭加「主持人A: 」"
    )
    summary_a = await ai_service.generate_reply(summary_prompt_a)
    dialogue.append(summary_a.strip())

    summary_prompt_b = (
        "請你以主持人B的身分，針對主持人A的總結內容做補充或分享個人觀點，"
        "語氣輕鬆，約2~3句話，每句話用句號分隔，開頭加「主持人B: 」"
    )
    summary_b = await ai_service.generate_reply(summary_prompt_b)
    dialogue.append(summary_b.strip())

    ending_prompt_a = (
        "請你以主持人A的身分，用一段話做本集播客的溫馨結語，"
        "內容要呼應今天討論的三則新聞，開頭加「主持人A: 」，不要有任何佔位符。"
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
            if line.startswith("主持人A:"):
                speaker = "主持人A"
            elif line.startswith("主持人B:"):
                speaker = "主持人B"
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
    # 轉成結構化陣列
    content = []
    for line in merged_lines:
        if line.startswith("主持人A:"):
            content.append(PodcastScriptContent(speaker="主持人A", text=line[len("主持人A:"):].strip()))
        elif line.startswith("主持人B:"):
            content.append(PodcastScriptContent(speaker="主持人B", text=line[len("主持人B:"):].strip()))
    podcast_script = PodcastScript(
        title="Hakkast 哈客播新聞討論",
        hosts=["主持人A", "主持人B"],
        content=content
    )
    print(f"腳本字數：{sum(len(c.text) for c in content)}")
    return podcast_script