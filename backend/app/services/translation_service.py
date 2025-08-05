import httpx
import logging
from typing import Dict, Any, Optional
from app.core.config import settings
from cn2an import an2cn  #記得 pip install cn2an ㄛ

logger = logging.getLogger(__name__)

class TranslationService:
    """Service for translating Traditional Chinese to Hakka using Hakka AI Hackathon API"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=15.0, verify=False)  # SSL verification disabled
        self.base_url = settings.HAKKA_TRANSLATE_API_URL
        self.username = settings.HAKKA_USERNAME
        self.password = settings.HAKKA_PASSWORD
        self.token = None
        self.headers = None
    
    async def login(self):
        """Authenticate and obtain bearer token for API requests"""
        try:
            login_payload = {
                'username': self.username,
                'password': self.password
            }
            
            response = await self.client.post(
                f'{self.base_url}/api/v1/tts/login',
                json=login_payload
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'token' in data:
                    self.token = data['token']
                    self.headers = {'Authorization': f'Bearer {self.token}'}
                    logger.info("Successfully authenticated with Hakka translation API")
                    return True
                    
        except Exception as e:
            logger.error(f"Login failed: {e}")
            
        return False

#根據 dialect (四縣/海陸)決定 endpoint。中文->客語漢字->調型符號/數字調
    def _convert_numbers_to_chinese(self, text: str) -> str:
        """
        將字串中的數字->中文
        """
        import re
        def repl(match):
            num = match.group()
            try:
                return an2cn(num)
            except Exception:
                return num
        converted = re.sub(r'\d+', repl, text)
        if converted != text:
            print(f"[數字轉中文] 原文: {text} -> 轉換後: {converted}")
        return converted

    async def translate_chinese_to_hakka(self, chinese_text: str, dialect: str = "sihxian") -> Dict[str, Any]:

        try:
            # 將數字轉為中文
            chinese_text = self._convert_numbers_to_chinese(chinese_text)

            # Ensure we're authenticated
            if not self.headers:
                await self.login()
            
            if not self.headers:
                logger.warning("Authentication failed, using fallback translation")
                return self._get_fallback_translation(chinese_text)
            
            # 根據腔調選擇 endpoint
            if dialect == "hailu":
                hanzi_endpoint = "/MT/translate/hakka_hailu_zh_hk"
                py_endpoint = "/MT/translate/hakka_hailu_hk_py"
                tone_endpoint = "/MT/translate/hakka_hailu_hk_py_tone"
            else:
                hanzi_endpoint = "/MT/translate/hakka_zh_hk"
                py_endpoint = "/MT/translate/hakka_hk_py"
                tone_endpoint = "/MT/translate/hakka_hk_py_tone"

            payload = {'input': chinese_text}
            # 中文→客語漢字
            response = await self.client.post(
                f'{self.base_url}{hanzi_endpoint}',
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == '200':
                    hakka_text = result.get('output', chinese_text)

                    # 客語漢字→數字調拼音
                    py_resp = await self.client.post(
                        f'{self.base_url}{py_endpoint}',
                        headers=self.headers,
                        json={"input": hakka_text}
                    )
                    if py_resp.status_code == 200:
                        romanization = py_resp.json().get("output", "")
                    else:
                        romanization = self._generate_romanization(hakka_text)

                    # 客語漢字→調型符號拼音
                    tone_resp = await self.client.post(
                        f'{self.base_url}{tone_endpoint}',
                        headers=self.headers,
                        json={"input": hakka_text}
                    )
                    if tone_resp.status_code == 200:
                        romanization_tone = tone_resp.json().get("output", "")
                    else:
                        romanization_tone = self._generate_tone_symbol_romanization(hakka_text)

                    return {
                        "hakka_text": hakka_text,
                        "romanization": romanization,
                        "romanization_tone": romanization_tone,
                        "original_chinese": chinese_text,
                        "api_response": result,
                        "tts_ready": True,
                        "text_length": len(hakka_text),
                        "estimated_speech_duration": max(5, len(hakka_text) * 0.5)
                    }
                else:
                    logger.error(f"Translation API returned error code: {result.get('code')}")
                    return self._get_fallback_translation(chinese_text)
            else:
                logger.error(f"Translation API error: {response.status_code}")
                return self._get_fallback_translation(chinese_text)
                
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return self._get_fallback_translation(chinese_text)
    
    def _get_fallback_translation(self, chinese_text: str) -> Dict[str, Any]:
        """Fallback translation when API is unavailable"""
        hakka_text = self._mock_translate_to_hakka(chinese_text)
        romanization = self._generate_romanization(hakka_text)
        
        return {
            "hakka_text": hakka_text,
            "romanization": romanization,
            "original_chinese": chinese_text,
            # TTS-ready metadata
            "tts_ready": True,
            "text_length": len(hakka_text),
            "estimated_speech_duration": max(5, len(hakka_text) * 0.5),  # seconds
            "fallback_used": True
        }
    
    def _mock_translate_to_hakka(self, chinese_text: str) -> str:
        """
        Mock translation for fallback when API is unavailable
        Provides basic Chinese to Hakka character mapping
        """
        # Enhanced Chinese to Hakka character mappings for podcast content
        hakka_mappings = {
            # Basic pronouns and common words
            '你': '你',  # Keep 你 for natural flow in some contexts
            '我': '𠊎',
            '他': '佢',
            '她': '佢',
            '這': '這',
            '那': '該',
            '什麼': '麼个',
            '怎麼': '仰般',
            '哪裡': '哪位',
            '多少': '幾多',
            '好': '好',
            '是': '係',
            '不': '毋',
            '沒有': '無',
            '有': '有',
            '要': '愛',
            '去': '去',
            '來': '來',
            
            # Enhanced colloquial expressions for podcast
            '哎呀': '𠊎話',  # More natural Hakka exclamation
            '搞不好': '無定著',
            '可能': '可能',
            '或許': '抑係',
            '當然': '當然',
            '非常': '當',
            '真的': '正經',
            '確實': '確實',
            '其實': '其實',
            '而且': '摎',
            '但是': '毋過',
            '不過': '毋過',
            '所以': '所以',
            '因為': '因為',
            '如果': '假使',
            '雖然': '雖然',
            '還是': '還係',
            '應該': '應該',
            '必須': '一定愛',
            
            # Action verbs
            '吃': '食',
            '喝': '飲',
            '說': '講',
            '看': '看',
            '聽': '聽',
            '做': '做',
            '買': '買',
            '賣': '賣',
            '想': '想',
            '覺得': '感覺',
            '認為': '認為',
            '希望': '希望',
            '需要': '愛',
            '可以': '做得',
            '能夠': '做得',
            
            # Descriptive words
            '大': '大',
            '小': '細',
            '高': '高',
            '低': '低',
            '新': '新',
            '舊': '舊',
            '快': '緊',
            '慢': '慢',
            '美': '靚',
            '醜': '醜',
            '重要': '重要',
            '特別': '特別',
            '一般': '一般',
            '普通': '普通',
            '困難': '難',
            '容易': '好做',
            '複雜': '複雜',
            '簡單': '簡單',
            
            # Time expressions  
            '今天': '今晡日',
            '昨天': '昨晡日',  
            '明天': '天光日',
            '現在': '這下',
            '以前': '頭前',
            '以後': '下擺',
            '將來': '未來',
            '過去': '過去',
            '未來': '未來',
            '最近': '最近',
            
            # Polite expressions
            '好吃': '好食',
            '謝謝': '承蒙',
            '對不起': '失禮',
            '再見': '正來尞',
            '請問': '請問',
            '麻煩': '麻煩',
            '不好意思': '毋好意思',
            
            # Technology and modern terms (keep original + add context)
            'AI': 'AI',
            '數位': '數位',
            '科技': '科技',
            '技術': '技術',
            '系統': '系統',
            '網路': '網路',
            '資料': '資料',
            '資訊': '資訊',
            '電腦': '電腦',
            '手機': '手機',
            '應用': '應用',
            '服務': '服務',
            '平台': '平台',
            '功能': '功能',
            '效率': '效率',
            '品質': '品質',
            '安全': '安全',
            '隱私': '隱私',
            '創新': '創新',
            '發展': '發展',
            '改善': '改善',
            '提升': '提升',
            
            # Enhanced medical and tech terminology
            '人工智慧': '人工智慧',
            '機器學習': '機器學習', 
            '深度學習': '深層學習',
            '數據分析': '數據分析',
            '雲端運算': '雲端運算',
            '物聯網': '物聯網',
            '區塊鏈': '區塊鏈',
            '虛擬實境': '虛擬實境',
            '擴增實境': '擴增實境',
            '數位轉型': '數位轉型',
            'AI素養': 'AI素養',
            '數據偏誤': '數據偏差',
            '內部運作機制': '內部運作機制',
            '批判性思維': '批判性思考',
            '協作權威': '協作權威',
            '差分隱私': '差分隱私',
            '同態加密': '同態加密',
            '匿名性': '無名性',
            '安全性': '安全性',
            '診斷': '診斷',
            '醫護': '醫護',
            '病患': '病人',
            '症狀': '症狀',
            '治療': '治療',
            '手術': '手術',
            '藥物': '藥物',
            '檢查': '檢查',
            '醫學系': '醫學系',
            '解剖': '解剖',
            '醫師': '醫師',
            '護理': '護理',
            '醫院': '醫院',
            '精準': '精準',
            '溫暖': '溫暖',
            '安慰': '安慰',
            '同理心': '同理心',
            '調解': '調解',
            '權威': '權威',
            '責任': '責任',
            '全局': '全局',
            '掌握': '掌握',
            
            # Podcast specific expressions
            '主持人': '主持人',
            '聽眾': '聽眾',
            '節目': '節目',
            '播客': '播客',
            '討論': '討論',
            '話題': '話題',
            '觀點': '觀點',
            '意見': '意見',
            '經驗': '經驗',
            '故事': '故事',
            '分享': '分享',
            '介紹': '介紹',
            '歡迎': '歡迎',
            '收聽': '收聽',
        }
        
        # Simple word replacement
        hakka_text = chinese_text
        for chinese_word, hakka_word in hakka_mappings.items():
            hakka_text = hakka_text.replace(chinese_word, hakka_word)
        
        return hakka_text
    
    def _generate_romanization(self, hakka_text: str) -> str:
        """
        Generate basic romanization for Hakka text
        This is a simplified implementation - in production, you'd want more sophisticated phonetic mapping
        """
        # Enhanced Hakka character to romanization mapping (四縣腔)
        romanization_map = {
            # Basic pronouns and common words
            '汝': 'ngi²', '你': 'ngi²',
            '𠊎': 'ngai²', '我': 'ngai²',
            '佢': 'gi²', '他': 'gi²', '她': 'gi²',
            '這': 'lia²', '個': 'ge⁵',
            '該': 'gai⁵', '那': 'gai⁵',
            '麼个': 'ma¹ ge⁵',
            '仰般': 'ngiong² pan¹',
            '哪位': 'na² vi¹',
            '幾多': 'gi¹ do¹',
            
            # Core verbs and adjectives
            '好': 'ho²',
            '係': 'he⁵', '是': 'he⁵',
            '毋': 'm²', '不': 'm²',
            '無': 'mo²', '沒': 'mo²',
            '有': 'yu²',
            '愛': 'oi⁵', '要': 'oi⁵',
            '去': 'ki⁵',
            '來': 'loi²',
            '食': 'sit⁸', '吃': 'sit⁸',
            '飲': 'yim²', '喝': 'yim²',
            '講': 'gong²', '說': 'gong²',
            '看': 'kon⁵',
            '聽': 'tiang¹',
            '做': 'zo⁵',
            '買': 'mai²',
            '賣': 'mai⁵',
            
            # Size and quality descriptors
            '大': 'tai⁵',
            '細': 'se⁵', '小': 'se⁵',
            '高': 'go¹',
            '低': 'tai¹',
            '新': 'xin¹',
            '舊': 'kiu⁵',
            '緊': 'gin²', '快': 'gin²',
            '慢': 'man⁶',
            '靚': 'liang⁵', '美': 'liang⁵',
            '醜': 'cug²',
            
            # Time expressions  
            '今': 'gin¹',
            '晡': 'pu¹',
            '日': 'ngit⁸',
            '天': 'tien¹',
            '時': 'sii²',
            '當': 'dong¹',
            '下': 'ha⁶',
            '擺': 'bai²',
            '未': 'vi⁶',
            '頭': 'teu²',
            '前': 'qien²',
            
            # Common phrases
            '好食': 'ho² sit⁸',
            '承蒙': 'sang² mung²',
            '失禮': 'shit⁷ le²',
            '正來尞': 'zang⁵ loi² liau²',
            '今晡日': 'gin¹ pu¹ ngit⁸',
            '昨晡日': 'qia⁵ pu¹ ngit⁸',
            '天光日': 'tien¹ gong¹ ngit⁸',
            '這下': 'lia² ha⁶',
            
            # Numbers and basic counting
            '一': 'yit⁷',
            '二': 'ngi⁶', '兩': 'liong²',
            '三': 'sam¹',
            '四': 'sii⁵',
            '五': 'ng²',
            '六': 'liug⁸',
            '七': 'qit⁷',
            '八': 'bat⁷',
            '九': 'giu²',
            '十': 'sip⁸',
            
            # Colloquial expressions
            '哎': 'ai¹',
            '呀': 'ya¹',
            '啊': 'a¹',
            '哦': 'o¹',
            '嗎': 'ma¹',
            '吧': 'pa¹',
            '呢': 'ne¹',
            '咧': 'le¹',
            '嗬': 'ho¹',
            '吓': 'ha¹',
            '唉': 'ai¹',
            
            # Family and people
            '人': 'ngin²',
            '家': 'ga¹',
            '主': 'zu²',
            '持': 'cii²',
            '員': 'yuen²',
            '生': 'sang¹',
            '師': 'sii¹',
            '醫': 'yi¹',
            '護': 'fu⁶',
            '病': 'piang⁶',
            
            # Body parts and health
            '目': 'mug⁸',
            '神': 'siin²',
            '心': 'xim¹',
            '手': 'su²',
            '體': 'ti²',
            
            # Actions and movement  
            '開': 'koi¹',
            '工': 'gung¹',
            '吵': 'cau²',
            '起': 'ki²',
            '面': 'mien⁶',
            '對': 'dui⁵',
            '得': 'det⁷',
            '著': 'to²',
            '分': 'pun¹',
            '帶': 'tai⁵',
            '等': 'den²',
            '摎': 'lau¹', '和': 'lau¹', '與': 'lau¹',
            
            # Technology and modern terms
            'A': 'A',
            'I': 'I',
            'AI': 'A I',
            
            # Particles and connectors
            '个': 'ge⁵', '的': 'ge⁵',
            '都': 'du¹',
            '在': 'cai⁶',
            '中': 'zung¹',
            '裡': 'li²',
            '上': 'song⁶',
            '也': 'ya²', '乜': 'ya²',
            '還': 'han²',
            '就': 'ciu⁶',
            '但': 'tan⁶',
            '如': 'yi²',
            '果': 'go²',
            '像': 'xiong⁶',
            '比': 'pi²',
            '較': 'kau⁵',
            '最': 'zui⁵',
            '很': 'hen²',
            '更': 'kang⁵',
            '太': 'tai⁵',
            '非': 'fui¹',
            '常': 'song²',
            '真': 'zin¹',
            '正': 'zang⁵',
            '經': 'gin¹',
        }
        
        # Generate romanization by character/word mapping
        romanization_parts = []
        i = 0
        while i < len(hakka_text):
            # Try to match longer phrases first
            matched = False
            for length in range(min(3, len(hakka_text) - i), 0, -1):
                substring = hakka_text[i:i+length]
                if substring in romanization_map:
                    romanization_parts.append(romanization_map[substring])
                    i += length
                    matched = True
                    break
            
            if not matched:
                # If no mapping found, keep original character
                romanization_parts.append(hakka_text[i])
                i += 1
        return ' '.join(romanization_parts)
    #我是調型符號:D
    def _generate_tone_symbol_romanization(self, hakka_text: str) -> str:
        tone_symbol_map = {
            '𠊎': 'ngâi',
            '食': 'si̍t',
        }
        result = []
        i = 0
        while i < len(hakka_text):
            matched = False
            for length in range(min(3, len(hakka_text) - i), 0, -1):
                substring = hakka_text[i:i+length]
                if substring in tone_symbol_map:
                    result.append(tone_symbol_map[substring])
                    i += length
                    matched = True
                    break
            if not matched:
                result.append(hakka_text[i])
                i += 1
        return ' '.join(result)

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()