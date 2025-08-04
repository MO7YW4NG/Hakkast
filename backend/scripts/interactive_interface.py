#!/usr/bin/env python3
"""
Hakkast 互動式播客生成系统
用戶可選擇主題 → 爬取相關文章 → AI生成播客腳本
"""

import asyncio
from app.services.crawl4ai_service import crawl_news
#from app.services.pydantic_ai_service import PydanticAIService
#from app.models.podcast import PodcastGenerationRequest
from app.services.ai_service import AIService
import json
from app.services.translation_service import TranslationService
from app.services.tts_service import TTSService

TOPIC_OPTIONS = {
    "1": {
        "key": "technology_news",
        "name": "Technology",
        "description": "Latest technology trends, AI, cloud computing, digital transformation, and related topics."
    },
    "2": {
        "key": "finance_economics", 
        "name": "Finance",
        "description": "Financial markets, economic policies, investment trend analysis."
    },
    "3": {
        "key": "research_deep_learning",
        "name": "AI Research",
        "description": "Latest AI research papers and breakthroughs in machine learning."
    }
}

async def interactive_podcast_generator():
    """
    互動式播客生成主程式
    """
    print("歡迎使用 Hakkast")
    
    # 添加測試模式選項
    print("\n請選擇模式：")
    print("1. 完整模式 (爬蟲 → 生成腳本 → 翻譯 → 音頻生成)")
    print("2. 測試模式 (跳到音頻生成，使用現有腳本)")
    
    while True:
        mode_choice = input("請輸入選項 (1-2): ").strip()
        if mode_choice in ['1', '2']:
            break
        else:
            print("無效選項，請輸入 1 或 2")
    
    if mode_choice == '2':
        # 測試模式：直接跳到音頻生成
        await audio_generation_test_mode()
        return

    # 完整模式繼續原有流程
    print("\n=== 完整模式 ===")

    # 顯示主題選項
    print("請選擇你想要的主題：")
    print()
    for key, value in TOPIC_OPTIONS.items():
        print(f"{key}. {value['name']}")
        print(f"{value['description']}")
        print()
    
    # user選擇主題
    while True:
        choice = input("請輸入選項 (1-3) 或 'q' 退出: ").strip()
        
        if choice.lower() == 'q':
            print("感謝使用 Hakkast")
            return
        
        if choice in TOPIC_OPTIONS:
            selected_topic = TOPIC_OPTIONS[choice]
            break
        else:
            print("無效選項，請輸入 1、2、3 或 'q'")
            continue
        
    print(f"已選擇主題: {selected_topic['name']}")

    
    # 爬蟲*3
    start_crawl = input("是否開始爬取新聞？(y/N): ").strip().lower()
    if start_crawl not in ['y', 'yes', '是']:
        print("任務完成！")
        return

    max_articles = 3
    topic_key = selected_topic['key']

    print(f"開始爬取 {selected_topic['name']} 相關文章...")

    
    # 爬取新聞
    try:
        # 選擇腔調
        print("請選擇客語腔調：")
        print("1. 四縣腔")
        print("2. 海陸腔")
        while True:
            dialect_choice = input("請輸入選項: ").strip()
            if dialect_choice == "1":
                dialect = "sihxian"
                break
            elif dialect_choice == "2":
                dialect = "hailu"
                break
            else:
                print("無效選項，請輸入 1 或 2")
                continue

        crawled_articles = await crawl_news(topic_key, max_articles)
        
        if not crawled_articles:
            print("沒有抓到任何文章，請稍後再試")
            return
        

        print(f"成功爬取 {len(crawled_articles)} 篇文章")
 
        
        # 顯示爬取結果
        for i, article in enumerate(crawled_articles, 1):
            print(f"{i}. {article.title}")
            print(f"來源: {article.source}")
            print(f"發佈日期: {article.published_at.strftime('%Y-%m-%d')}")
            print(f"摘要: {article.summary[:100]}...")
            print(f"授權網址: {getattr(article, 'license_url', '')}")
            print(f"授權類型: {getattr(article, 'license_type', '')}")
            print()
        
        # 確認是否繼續生成腳本
        continue_choice = input("是否要繼續生成腳本？(y/N): ").strip().lower()
        
        if continue_choice not in ['y', 'yes', '是']:
            print("任務完成")
            return
        
        print("開始生成腳本...")

        # 使用第一篇文章的標題為主標題
        main_title = crawled_articles[0].title
        
        # 合併文章內容
        combined_content = "\n\n".join([
            f"標題: {article.title}\n內容: {article.content or article.summary}\n來源: {article.url}"
            for article in crawled_articles
        ])
        
        # 產生腳本
        ai_service = AIService()
        result = await ai_service.generate_podcast_script_with_agents(crawled_articles, max_minutes=25)
        
        # 從返回的字典中取出原始腳本
        podcast_script = result["tts_ready_script"]
        print("\n腳本生成完成")
        print("進行客語翻譯...")

        # 傳 dialect 給 add_hakka_translation_to_script
        podcast_script = await add_hakka_translation_to_script(podcast_script, dialect=dialect)
        print("翻譯完成")
        print(podcast_script.model_dump_json(indent=2))
       
        print(f"腳本字數：{len(podcast_script.content)}")
        print("\n完整播客腳本：\n")
        for item in podcast_script.content:
            print(f"{item.speaker}: {item.text} -> {item.hakka_text}")

        # 儲存腳本
        save_choice = input("是否要保存腳本到文件？(y/N): ").strip().lower()
        
        filename = f"podcast_script_{topic_key}_{len(crawled_articles)}articles.json"
        filepath = None
        
        if save_choice in ['y', 'yes', '是']:
            import os
            # 確保 json 資料夾存在
            json_dir = "json"
            os.makedirs(json_dir, exist_ok=True)
            
            filepath = os.path.join(json_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(podcast_script.model_dump_json(indent=2))
            print(f"腳本已保存至: {filepath}")
        
        # 生成音頻
        audio_choice = input("是否要生成客語音頻？(y/N): ").strip().lower()
        if audio_choice in ['y', 'yes', '是']:
            print("開始生成客語音頻...")
            
            # 選擇音頻處理模式
            print("\n請選擇音頻處理模式：")
            print("1. 僅生成音檔")
            print("2. 生成音檔 + 自動合併為完整播客")
            print("3. 使用整合音檔管理器")
            
            while True:
                audio_mode = input("請輸入選項 (1-3): ").strip()
                if audio_mode in ['1', '2', '3']:
                    break
                else:
                    print("無效選項，請輸入 1、2 或 3")
            
            if audio_mode == '1':
                # 原有的音頻生成方式
                await generate_podcast_audio_with_voices(podcast_script, dialect, filename.replace('.json', ''))
            
            elif audio_mode == '2':
                # 生成 + 自動合併為完整播客
                await generate_and_merge_podcast_audio(podcast_script, dialect, filename.replace('.json', ''), auto_merge=True)
            
            elif audio_mode == '3':
                # 使用整合音檔管理器
                await use_integrated_audio_manager(filepath or f"json/{filename}")
        
        print("播客製作完成！感謝使用 Hakkast 🎉")
     
    except Exception as e:
        print(f"發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()

async def audio_generation_test_mode():
    """音頻生成測試模式 - 跳過爬蟲和腳本生成"""
    print("=== 音頻生成測試模式 ===")
    
    # 檢查是否有現有的腳本檔案
    import os
    from pathlib import Path
    
    json_dir = Path("json")
    if not json_dir.exists():
        print("❌ 找不到 json 資料夾，請先執行完整模式生成一些腳本")
        return
    
    script_files = list(json_dir.glob("podcast_script_*.json"))
    
    if not script_files:
        print("❌ 沒有找到播客腳本文件，請先執行完整模式生成一些腳本")
        return
    
    print("找到以下腳本文件：")
    for i, file in enumerate(script_files, 1):
        print(f"{i}. {file.name}")
    
    # 選擇腳本文件
    while True:
        try:
            choice = input(f"請選擇腳本文件 (1-{len(script_files)}): ").strip()
            file_index = int(choice) - 1
            if 0 <= file_index < len(script_files):
                selected_file = script_files[file_index]
                break
            else:
                print(f"請輸入 1 到 {len(script_files)} 之間的數字")
        except ValueError:
            print("請輸入有效的數字")
    
    print(f"已選擇腳本: {selected_file.name}")
    
    # 讀取腳本文件
    try:
        with open(selected_file, 'r', encoding='utf-8') as f:
            script_data = json.load(f)
        print("✅ 腳本讀取成功")
    except Exception as e:
        print(f"❌ 讀取腳本失敗: {str(e)}")
        return
    
    # 檢查腳本是否已經有客語翻譯
    has_hakka_translation = False
    if 'content' in script_data and script_data['content']:
        first_item = script_data['content'][0]
        has_hakka_translation = 'hakka_text' in first_item and first_item.get('hakka_text')
    
    print(f"腳本翻譯狀態: {'已翻譯' if has_hakka_translation else '未翻譯'}")
    
    if not has_hakka_translation:
        print("❌ 該腳本尚未翻譯成客語，請使用完整模式先進行翻譯")
        return
    
    # 從檔名或詢問使用者選擇腔調
    if "sihxian" in selected_file.name or "四縣" in selected_file.name:
        dialect = "sihxian"
        print(f"從檔名推斷腔調: 四縣腔")
    elif "hailu" in selected_file.name or "海陸" in selected_file.name:
        dialect = "hailu"
        print(f"從檔名推斷腔調: 海陸腔")
    else:
        # 詢問腔調
        print("請確認客語腔調：")
        print("1. 四縣腔")
        print("2. 海陸腔")
        while True:
            dialect_choice = input("請輸入選項: ").strip()
            if dialect_choice == "1":
                dialect = "sihxian"
                break
            elif dialect_choice == "2":
                dialect = "hailu"
                break
            else:
                print("無效選項，請輸入 1 或 2")
                continue
    
    # 重建腳本對象
    from app.models.podcast import PodcastScript, PodcastScriptContent
    
    segments = []
    for item in script_data['content']:
        segment = PodcastScriptContent(
            speaker=item['speaker'],
            text=item['text'],
            hakka_text=item.get('hakka_text', ''),
            romanization=item.get('romanization', ''),
            romanization_tone=item.get('romanization_tone', '')
        )
        segments.append(segment)
    
    podcast_script = PodcastScript(
        title=script_data.get('title', '客語播客'),
        hosts=script_data.get('hosts', ['佳昀', '敏權']),
        content=segments
    )
    
    # 顯示腳本預覽
    print(f"\n=== 腳本內容預覽 (共 {len(script_data['content'])} 段) ===")
    for i, item in enumerate(script_data['content'][:3], 1):  # 只顯示前3段
        print(f"{i}. {item['speaker']}: {item['text'][:50]}...")
        if 'hakka_text' in item:
            print(f"   客語: {item['hakka_text'][:50]}...")
        print()
    
    if len(script_data['content']) > 3:
        print(f"... (還有 {len(script_data['content']) - 3} 段)")
    
    # 提取腳本名稱
    script_name = selected_file.stem
    
    print(f"\n=== 開始音頻生成測試 ===")
    print(f"腔調: {dialect}")
    print(f"腳本名稱: {script_name}")
    
    # 選擇音頻處理模式
    print("\n請選擇音頻處理模式：")
    print("1. 僅生成音檔")
    print("2. 生成音檔 + 自動合併為完整播客")
    print("3. 使用整合音檔管理器")
    
    while True:
        audio_mode = input("請輸入選項 (1-3): ").strip()
        if audio_mode in ['1', '2', '3']:
            break
        else:
            print("無效選項，請輸入 1、2 或 3")
    
    try:
        if audio_mode == '1':
            # 原有的音頻生成方式
            await generate_podcast_audio_with_voices(podcast_script, dialect, script_name)
        
        elif audio_mode == '2':
            # 生成 + 自動合併為完整播客
            await generate_and_merge_podcast_audio(podcast_script, dialect, script_name, auto_merge=True)
        
        elif audio_mode == '3':
            # 使用整合音檔管理器
            await use_integrated_audio_manager(str(selected_file))
        
        print("🎉 音頻生成測試完成！")
        
    except Exception as e:
        print(f"❌ 音頻生成過程發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()

#將 content 裡 text 翻譯成客語漢字，並產生羅馬拼音（四縣腔/海陸腔）
async def add_hakka_translation_to_script(podcast_script, dialect="sihxian"):
    service = TranslationService()
    ai_service = AIService()
    
    for item in podcast_script.content:
        print(f"[處理前] {item.speaker}: {item.text}")
        if not service.headers:
            await service.login()
        result = await service.translate_chinese_to_hakka(item.text, dialect=dialect)
        item.hakka_text = result.get("hakka_text", "")
        item.romanization = result.get("romanization", "")
        item.romanization_tone = result.get("romanization_tone", "")
    await service.close()
    return podcast_script

async def generate_and_merge_podcast_audio(podcast_script, dialect, script_name, auto_merge=False):
    """生成音頻並可選擇性合併
    
    Args:
        podcast_script: 播客腳本對象
        dialect: 腔調 ('sihxian' 或 'hailu') 
        script_name: 腳本名稱
        auto_merge: 是否自動合併音檔
    """
    print(f"=== 使用整合音檔管理器生成音頻 ===")
    
    # 先用原有方式生成音頻
    await generate_podcast_audio_with_voices(podcast_script, dialect, script_name)
    
    # 使用音檔管理器進行後續處理，確保音檔目錄正確
    manager = PodcastAudioManager()
    # 確保音檔目錄設置正確
    from pathlib import Path
    manager.audio_dir = Path("static/audio").resolve()
    
    try:
        # 檢查生成的音檔
        print(f"\n檢查生成的音檔...")
        print(f"音檔目錄: {manager.audio_dir}")
        
        # 檢查所有可能的說話者代碼
        speaker_codes = ["SXF", "SXM", "HLF", "HLM"]  # 四縣女/男，海陸女/男
        available_speakers = []
        
        for code in speaker_codes:
            files = manager.get_organized_files(script_name, code)
            if files:
                available_speakers.append((code, len(files)))
                print(f"發現 {code} 說話者音檔: {len(files)} 個")
        
        if not available_speakers:
            print("沒有找到可合併的音檔")
            print(f"嘗試查找模式: {script_name}_*_*.wav")
            # 手動檢查音檔目錄
            all_files = list(manager.audio_dir.glob(f"{script_name}_*.wav"))
            print(f"音檔目錄中找到的所有相關檔案: {len(all_files)}")
            for f in all_files[:5]:  # 只顯示前5個
                print(f"  - {f.name}")
            return
        
        # 顯示詳細資訊
        for code, count in available_speakers:
            manager.show_script_info(script_name, code)
        
        # 決定是否合併
        should_merge = auto_merge
        if not auto_merge:
            merge_choice = input(f"\n是否要將音檔合併為完整播客？(y/N): ").strip().lower()
            should_merge = merge_choice in ['y', 'yes', '是']
        
        if should_merge:
            print("正在將所有說話者音檔合併為完整播客...")
            
            # 使用 PodcastAudioManager 的現有功能進行多說話者合併
            success = await merge_all_speakers(script_name, available_speakers, manager)
            
            if success:
                print("🎉 完整播客合併完成！")
            else:
                print("❌ 播客合併失敗")
        else:
            print("跳過音檔合併")
            
    except Exception as e:
        print(f"❌ 音檔管理過程發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()

async def merge_all_speakers(script_name, available_speakers, manager):
    """將多個說話者的音檔按順序合併為單一完整播客
    使用 PodcastAudioManager 的現有方法來實現多說話者合併
    
    Args:
        script_name: 腳本名稱
        available_speakers: [(speaker_code, file_count), ...] 
        manager: PodcastAudioManager 實例
    """
    try:
        print("正在準備多說話者合併...")
        
        # 收集所有說話者的音檔，按照 segment_index 排序
        all_files = []
        for code, count in available_speakers:
            # 使用 PodcastAudioManager 的方法獲取音檔
            files = manager.get_organized_files(script_name, code)
            for file in files:
                # 提取段落序號進行排序
                try:
                    name_parts = file.stem.split('_')
                    segment_index = int(name_parts[-1])  # 最後一部分是序號
                    all_files.append((segment_index, file))
                except (ValueError, IndexError):
                    # 如果無法解析序號，放到最後
                    all_files.append((9999, file))
        
        # 按段落序號排序
        all_files.sort(key=lambda x: x[0])
        sorted_files = [file for _, file in all_files]
        
        print(f"準備合併 {len(sorted_files)} 個音檔...")
        
        # 創建合併清單和輸出檔案路徑
        concat_file = manager.audio_dir / f"{script_name}_all_speakers_concat.txt"
        output_file = manager.audio_dir / f"{script_name}_complete_all_speakers.wav"
        
        # 使用 PodcastAudioManager 的方法創建 FFmpeg 合併清單
        manager.create_ffmpeg_concat_file(sorted_files, concat_file)
        
        # 使用與 PodcastAudioManager.merge_audio_files 相同的邏輯
        import subprocess
        
        # 檢查是否安裝了 FFmpeg
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ FFmpeg 未安裝。請先安裝 FFmpeg 來合併音檔")
            print("安裝方法：")
            print("1. 下載 FFmpeg: https://ffmpeg.org/download.html")
            print("2. 或使用 Chocolatey: choco install ffmpeg")
            print("3. 或使用 winget: winget install Gyan.FFmpeg")
            return False
        
        # 使用 FFmpeg 合併（與 PodcastAudioManager 相同的命令）
        cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(concat_file),
            '-c', 'copy',
            '-y',
            str(output_file)
        ]
        
        print("執行多說話者音檔合併...")
        print(f"FFmpeg 命令: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            # 清理臨時檔案
            concat_file.unlink(missing_ok=True)
            
            if output_file.exists():
                file_size = output_file.stat().st_size
                print(f"🎉 多說話者播客合併完成！")
                print(f"📁 輸出檔案: {output_file}")
                print(f"📊 檔案大小: {file_size / 1024 / 1024:.2f} MB")
                print(f"🎵 總音檔數: {len(sorted_files)}")
                return True
            else:
                print("❌ 合併完成但找不到輸出檔案")
                return False
        else:
            print(f"❌ FFmpeg 合併失敗:")
            print(f"stdout: {result.stdout}")
            print(f"stderr: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 多說話者合併過程發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def use_integrated_audio_manager(script_file_path):
    """使用整合的音檔管理器處理播客
    
    Args:
        script_file_path: 腳本檔案路徑
    """
    print(f"=== 使用整合音檔管理器 ===")
    
    manager = PodcastAudioManager()
    # 確保音檔目錄設置正確
    from pathlib import Path
    manager.audio_dir = Path("static/audio").resolve()
    
    try:
        # 提取腳本名稱
        script_name = Path(script_file_path).stem
        
        print(f"腳本檔案: {script_file_path}")
        print(f"腳本名稱: {script_name}")
        print(f"音檔目錄: {manager.audio_dir}")
        
        # 檢查所有可能的說話者代碼的現有音檔
        speaker_codes = ["SXF", "SXM", "HLF", "HLM"]  # 四縣女/男，海陸女/男
        all_existing_files = {}
        total_files = 0
        
        for code in speaker_codes:
            files = manager.get_organized_files(script_name, code)
            if files:
                all_existing_files[code] = files
                total_files += len(files)
                print(f"發現 {code} 說話者音檔: {len(files)} 個")
        
        if all_existing_files:
            print(f"\n總共發現 {total_files} 個現有音檔，涵蓋 {len(all_existing_files)} 個說話者")
            
            # 顯示詳細資訊
            for code in all_existing_files:
                manager.show_script_info(script_name, code)
            
            # 詢問是否使用現有音檔還是重新生成
            print("\n請選擇操作：")
            print("1. 合併現有音檔為完整播客")
            print("2. 重新生成音檔")
            print("3. 重新生成 + 自動合併為完整播客")
            
            while True:
                action = input("請輸入選項 (1-3): ").strip()
                if action in ['1', '2', '3']:
                    break
                else:
                    print("無效選項，請輸入 1、2 或 3")
            
            if action == '1':
                # 僅合併現有音檔 - 直接合併所有說話者為完整播客
                print("\n正在將所有說話者音檔合併為完整播客...")
                available_speakers = [(code, len(files)) for code, files in all_existing_files.items()]
                success = await merge_all_speakers(script_name, available_speakers, manager)
                
                if success:
                    print("🎉 完整播客合併完成！")
                else:
                    print("❌ 播客合併失敗")
                return
            
            elif action in ['2', '3']:
                # 重新生成音檔
                auto_merge = (action == '3')
                result = await manager.generate_podcast_audio(script_file_path)
                
                if result.get('success'):
                    print(f"✅ 音檔生成成功！共 {result['total_audio_files']} 個音檔")
                    
                    if auto_merge:
                        # 自動合併所有說話者為完整播客
                        print("正在自動合併所有說話者音檔為完整播客...")
                        await auto_merge_all_speakers(script_name, manager)
                else:
                    print(f"❌ 音檔生成失敗: {result.get('error')}")
        else:
            # 沒有現有音檔，直接使用完整流程
            print("沒有找到現有音檔，將執行完整生成流程...")
            
            result = await manager.generate_and_merge_podcast(
                script_file=script_file_path,
                script_name=script_name,
                speaker=None,  # 不指定特定說話者，讓它處理所有說話者
                auto_merge=False  # 詢問用戶
            )
            
            if result.get('success'):
                print(f"✅ {result.get('message')}")
            else:
                print(f"❌ 處理失敗: {result.get('error')}")
                
    except Exception as e:
        print(f"❌ 整合音檔管理器執行錯誤: {str(e)}")
        import traceback
        traceback.print_exc()

async def generate_podcast_audio_with_voices(podcast_script, dialect, script_name):
    """根據說話者性別和腔調生成音頻
    
    Args:
        podcast_script: 播客腳本對象
        dialect: 腔調 ('sihxian' 或 'hailu')
        script_name: 腳本名稱，用於生成音檔名稱
    """
    from pathlib import Path
    import json
    
    print(f"=== 開始生成音頻 (腔調: {dialect}) ===")
    
    # 初始化 TTS 服務
    tts_service = TTSService()
    
    try:
        # 登入 TTS API
        print("正在登入 TTS API...")
        login_success = await tts_service.login()
        if not login_success:
            print("❌ TTS API 登入失敗，將使用 fallback 模式")
        else:
            print("✅ TTS API 登入成功")
        
        # 獲取可用的 TTS 模型和說話者
        models_info = await tts_service.get_models()
        print("正在獲取可用的語音模型...")
        
        # 說話者配置：根據性別和腔調選擇
        speaker_config = get_speaker_config(dialect)
        print(f"說話者配置: {speaker_config}")
        
        # 處理每個對話段落
        audio_results = []
        total_duration = 0
        successful_segments = 0
        
        for i, content_item in enumerate(podcast_script.content):
            speaker_name = content_item.speaker
            hakka_text = content_item.hakka_text
            romanization = content_item.romanization
            original_text = content_item.text
            
            print(f"\n--- 處理段落 {i+1}: {speaker_name} ---")
            print(f"原文: {original_text[:50]}...")
            print(f"客語: {hakka_text[:50]}...")
            
            # 根據說話者選擇語音模型和檔名說話者代碼
            if speaker_name == "敏權":
                selected_speaker_id = speaker_config["male"]
                file_speaker_code = "SXM" if dialect == "sihxian" else "HLM"  # 男聲代碼
                print(f"✅ 說話者 '{speaker_name}' 使用男聲: {selected_speaker_id}")
            elif speaker_name == "佳昀":
                selected_speaker_id = speaker_config["female"]
                file_speaker_code = "SXF" if dialect == "sihxian" else "HLF"  # 女聲代碼
                print(f"✅ 說話者 '{speaker_name}' 使用女聲: {selected_speaker_id}")
            else:
                # 默認使用女聲
                selected_speaker_id = speaker_config["female"]
                file_speaker_code = "SXF" if dialect == "sihxian" else "HLF"
                print(f"⚠️ 未知說話者 '{speaker_name}'，使用默認女聲: {selected_speaker_id}")
            
            print(f"使用語音模型: {selected_speaker_id}")
            print(f"檔名說話者代碼: {file_speaker_code}")
            
            # 文本分段處理（避免過長文本導致TTS超時）
            text_segments = split_long_text(hakka_text, romanization)
            segment_audio_results = []
            
            for j, (segment_hakka, segment_romanization) in enumerate(text_segments):
                # 使用統一的命名格式，與 PodcastAudioManager 相容
                segment_index = (i + 1) * 100 + (j + 1)  # 例如：101, 102, 201, 202
                
                print(f"  子段落 {j+1}/{len(text_segments)}: {segment_hakka[:30]}...")
                
                try:
                    # 調用 TTS API，使用統一的命名格式
                    audio_result = await tts_service.generate_hakka_audio(
                        hakka_text=segment_hakka,
                        romanization=segment_romanization,
                        speaker=selected_speaker_id,
                        segment_index=segment_index,  # 使用新的段落索引
                        script_name=script_name
                    )
                    
                    if audio_result.get('audio_id'):
                        if audio_result.get('voice_model') != 'fallback':
                            print(f"  ✅ 音頻合成成功 (真實TTS)")
                            successful_segments += 1
                        else:
                            print(f"  ⚠️ 使用 Fallback 模式")
                        
                        segment_audio_results.append(audio_result)
                        total_duration += audio_result.get('duration', 0)
                    else:
                        print(f"  ❌ 音頻合成失敗")
                        
                except Exception as e:
                    print(f"  ❌ 音頻合成錯誤: {str(e)}")
            
            # 將該說話者的所有音頻段落記錄
            if segment_audio_results:
                audio_results.append({
                    'segment_index': i + 1,
                    'speaker': speaker_name,
                    'speaker_id': selected_speaker_id,
                    'file_speaker_code': file_speaker_code,  # 添加檔名說話者代碼
                    'original_text': original_text,
                    'hakka_text': hakka_text,
                    'audio_segments': segment_audio_results,
                    'total_segments': len(segment_audio_results)
                })
        
        # 生成播放列表
        playlist_data = {
            'title': f'客語播客 - {script_name}',
            'dialect': dialect,
            'total_segments': len(audio_results),
            'total_duration': total_duration,
            'successful_tts_calls': successful_segments,
            'success_rate': f"{successful_segments / max(1, sum(len(item['audio_segments']) for item in audio_results)) * 100:.1f}%",
            'audio_segments': audio_results
        }
        
        # 保存播放列表
        playlist_dir = Path("static/audio")
        playlist_dir.mkdir(parents=True, exist_ok=True)
        playlist_file = playlist_dir / f"{script_name}_playlist.json"
        
        with open(playlist_file, 'w', encoding='utf-8') as f:
            json.dump(playlist_data, f, ensure_ascii=False, indent=2)
        
        # 結果統計
        print(f"\n=== 音頻生成完成 ===")
        print(f"總對話段落: {len(podcast_script.content)}")
        print(f"成功處理段落: {len(audio_results)}")
        print(f"總音頻片段: {sum(len(item['audio_segments']) for item in audio_results)}")
        print(f"成功 TTS 調用: {successful_segments}")
        print(f"預估總時長: {total_duration:.1f} 秒 ({total_duration/60:.1f} 分鐘)")
        print(f"播放列表已保存: {playlist_file}")
        
        # 顯示音頻文件列表
        print(f"\n📁 生成的音頻文件:")
        for result in audio_results:
            print(f"  {result['speaker']} (段落 {result['segment_index']}):")
            for j, audio in enumerate(result['audio_segments']):
                if audio.get('audio_path'):
                    filename = Path(audio['audio_path']).name
                    duration = audio.get('duration', 0)
                    print(f"    {j+1}. {filename} ({duration}s)")
        
        # 登出
        await tts_service.logout()
        print("\n✅ 已登出 TTS API")
        
    except Exception as e:
        print(f"❌ 音頻生成過程發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        await tts_service.close()
        print("TTS 服務已關閉")

def get_speaker_config(dialect):
    """根據腔調獲取說話者配置
    
    Args:
        dialect: 'sihxian' (四縣腔) 或 'hailu' (海陸腔)
    
    Returns:
        dict: 包含 male 和 female 說話者 ID 的字典
    """
    if dialect == "sihxian":
        # 四縣腔配置
        return {
            "male": "hak-xi-TW-vs2-M01",    # 四縣男聲
            "female": "hak-xi-TW-vs2-F01"   # 四縣女聲
        }
    elif dialect == "hailu":
        # 海陸腔配置 
        return {
            "male": "hak-hoi-TW-vs2-M01",   # 海陸男聲  
            "female": "hak-hoi-TW-vs2-F01"  # 海陸女聲
        }
    else:
        # 默認使用四縣腔
        print(f"⚠️ 未知腔調 '{dialect}'，使用四縣腔")
        return {
            "male": "hak-xi-TW-vs2-M01",
            "female": "hak-xi-TW-vs2-F01"
        }

def split_long_text(hakka_text, romanization, max_length=60):
    """將長文本分段處理，避免TTS超時
    
    Args:
        hakka_text: 客語漢字文本
        romanization: 羅馬拼音
        max_length: 每段最大長度
    
    Returns:
        list: [(hakka_segment, romanization_segment), ...]
    """
    import re
    
    # 如果文本不長，直接返回
    if len(hakka_text) <= max_length:
        return [(hakka_text, romanization)]
    
    # 按標點符號分句
    sentences = re.split(r'([。！？；，])', hakka_text)
    romanization_sentences = re.split(r'([。！？；，])', romanization) if romanization else [''] * len(sentences)
    
    # 確保兩個列表長度一致
    while len(romanization_sentences) < len(sentences):
        romanization_sentences.append('')
    
    segments = []
    current_hakka = ""
    current_romanization = ""
    
    for i in range(0, len(sentences), 2):  # 每兩個元素為一組（句子+標點）
        sentence = sentences[i] if i < len(sentences) else ''
        punctuation = sentences[i + 1] if i + 1 < len(sentences) else ''
        
        rom_sentence = romanization_sentences[i] if i < len(romanization_sentences) else ''
        rom_punctuation = romanization_sentences[i + 1] if i + 1 < len(romanization_sentences) else ''
        
        full_sentence = sentence + punctuation
        full_rom_sentence = rom_sentence + rom_punctuation
        
        # 檢查加入此句子是否會超過長度限制
        if len(current_hakka + full_sentence) <= max_length:
            current_hakka += full_sentence
            current_romanization += full_rom_sentence
        else:
            # 保存當前段落
            if current_hakka.strip():
                segments.append((current_hakka.strip(), current_romanization.strip()))
            
            # 開始新段落
            current_hakka = full_sentence
            current_romanization = full_rom_sentence
    
    # 添加最後一段
    if current_hakka.strip():
        segments.append((current_hakka.strip(), current_romanization.strip()))
    
    return segments if segments else [(hakka_text, romanization)]

def main():
    try:
        asyncio.run(interactive_podcast_generator())
    except KeyboardInterrupt:
        print("\n\n用戶中斷")
    except Exception as e:
        print(f"\n系統錯誤: {str(e)}")

async def auto_merge_all_speakers(script_name, manager):
    """自動合併所有找到的說話者音檔為完整播客
    
    Args:
        script_name: 腳本名稱
        manager: PodcastAudioManager 實例
    """
    # 確保音檔目錄設置正確
    from pathlib import Path
    manager.audio_dir = Path("static/audio").resolve()
    
    speaker_codes = ["SXF", "SXM", "HLF", "HLM"]  # 四縣女/男，海陸女/男
    available_speakers = []
    
    # 檢查所有說話者代碼，找到有音檔的
    for code in speaker_codes:
        files = manager.get_organized_files(script_name, code)
        if files:
            available_speakers.append((code, len(files)))
            print(f"發現 {code} 說話者音檔: {len(files)} 個")
    
    if not available_speakers:
        print("❌ 沒有找到可合併的音檔")
        print(f"音檔目錄: {manager.audio_dir}")
        # 手動檢查音檔目錄
        all_files = list(manager.audio_dir.glob(f"{script_name}_*.wav"))
        print(f"音檔目錄中找到的所有相關檔案: {len(all_files)}")
        return
    
    # 直接將所有說話者的音檔合併為完整播客
    print("\n正在將所有說話者音檔合併為完整播客...")
    success = await merge_all_speakers(script_name, available_speakers, manager)
    
    if success:
        print("🎉 完整播客製作完成！")
    else:
        print("❌ 播客合併失敗")

if __name__ == "__main__":
    main()