#!/usr/bin/env python3
"""
音檔合併工具 - 基於組織化檔名系統
這個工具可以根據有序的檔名將音檔合併成完整的播客
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AudioMerger:
    """基於組織化檔名的音檔合併工具"""
    
    def __init__(self, audio_dir: str = "static/audio"):
        self.audio_dir = Path(audio_dir)
        
    def get_organized_files(self, script_name: str, speaker: str = "SXF") -> List[Path]:
        """獲取指定腳本的所有音檔，按序號排序"""
        pattern = f"{script_name}_{speaker}_*.wav"
        files = list(self.audio_dir.glob(pattern))
        
        # 按序號排序
        def extract_number(filepath):
            try:
                # 從檔名中提取序號，例如：tech_news_3articles_SXF_101.wav -> 101
                name = filepath.stem
                parts = name.split('_')
                return int(parts[-1])  # 最後一部分是序號
            except (ValueError, IndexError):
                return 0
        
        files.sort(key=extract_number)
        return files
    
    def create_ffmpeg_concat_file(self, files: List[Path], concat_file: Path):
        """創建 FFmpeg 串接檔案列表"""
        with open(concat_file, 'w', encoding='utf-8') as f:
            for file in files:
                # FFmpeg 需要相對路徑或絕對路徑
                abs_path = file.resolve()
                f.write(f"file '{abs_path}'\n")
    
    def merge_audio_files(self, script_name: str, output_filename: str = None, speaker: str = "SXF") -> bool:
        """合併指定腳本的所有音檔"""
        try:
            # 獲取音檔列表
            files = self.get_organized_files(script_name, speaker)
            
            if not files:
                logger.error(f"找不到腳本 '{script_name}' 的音檔")
                return False
            
            logger.info(f"找到 {len(files)} 個音檔要合併")
            
            # 顯示前10個檔案作為預覽
            logger.info("音檔列表（前10個）:")
            for i, file in enumerate(files[:10]):
                logger.info(f"  {i+1:3d}. {file.name}")
            if len(files) > 10:
                logger.info(f"  ... 還有 {len(files) - 10} 個檔案")
            
            # 創建輸出檔名
            if not output_filename:
                output_filename = f"{script_name}_complete_{speaker}.wav"
            
            output_path = self.audio_dir / output_filename
            concat_file = self.audio_dir / f"{script_name}_concat_list.txt"
            
            # 創建 FFmpeg 串接清單
            self.create_ffmpeg_concat_file(files, concat_file)
            
            # 檢查是否安裝了 FFmpeg
            try:
                subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.error("FFmpeg 未安裝。請先安裝 FFmpeg 來合併音檔")
                logger.info("安裝方法：")
                logger.info("1. 下載 FFmpeg: https://ffmpeg.org/download.html")
                logger.info("2. 或使用 Chocolatey: choco install ffmpeg")
                logger.info("3. 或使用 winget: winget install Gyan.FFmpeg")
                return False
            
            # 使用 FFmpeg 合併音檔
            cmd = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', str(concat_file),
                '-c', 'copy',
                '-y',  # 覆蓋輸出檔案
                str(output_path)
            ]
            
            logger.info(f"開始合併音檔...")
            logger.info(f"FFmpeg 命令: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # 清理臨時檔案
                concat_file.unlink(missing_ok=True)
                
                # 檢查輸出檔案
                if output_path.exists():
                    file_size = output_path.stat().st_size
                    logger.info(f"✅ 合併完成！")
                    logger.info(f"📁 輸出檔案: {output_path}")
                    logger.info(f"📊 檔案大小: {file_size / 1024 / 1024:.2f} MB")
                    return True
                else:
                    logger.error("合併完成但找不到輸出檔案")
                    return False
            else:
                logger.error(f"FFmpeg 合併失敗:")
                logger.error(f"stdout: {result.stdout}")
                logger.error(f"stderr: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"合併過程中發生錯誤: {e}")
            return False
    
    def show_script_info(self, script_name: str, speaker: str = "SXF"):
        """顯示腳本的音檔資訊"""
        files = self.get_organized_files(script_name, speaker)
        
        if not files:
            logger.info(f"找不到腳本 '{script_name}' 的音檔")
            return
        
        logger.info(f"\n📋 腳本資訊: {script_name}")
        logger.info(f"🎤 說話者: {speaker}")
        logger.info(f"📁 音檔數量: {len(files)}")
        
        total_size = sum(f.stat().st_size for f in files if f.exists())
        logger.info(f"💾 總大小: {total_size / 1024 / 1024:.2f} MB")
        
        # 顯示序號範圍
        numbers = []
        for file in files:
            try:
                name = file.stem
                parts = name.split('_')
                numbers.append(int(parts[-1]))
            except (ValueError, IndexError):
                pass
        
        if numbers:
            logger.info(f"🔢 序號範圍: {min(numbers)} - {max(numbers)}")
        
        # 顯示檔案列表示例
        logger.info("\n📝 檔案列表示例:")
        for i, file in enumerate(files[:5]):
            size = file.stat().st_size if file.exists() else 0
            logger.info(f"  {file.name} ({size/1024:.1f} KB)")
        
        if len(files) > 5:
            logger.info(f"  ... 還有 {len(files) - 5} 個檔案")

def main():
    """主程式"""
    merger = AudioMerger()
    
    script_name = "tech_news_3articles"
    
    # 顯示腳本資訊
    merger.show_script_info(script_name)
    
    # 詢問是否要合併
    try:
        response = input("\n是否要合併這些音檔？(y/N): ").strip().lower()
        if response in ['y', 'yes', '是']:
            success = merger.merge_audio_files(script_name)
            if success:
                logger.info("🎉 音檔合併完成！")
            else:
                logger.error("❌ 音檔合併失敗")
        else:
            logger.info("取消合併操作")
    except KeyboardInterrupt:
        logger.info("\n操作已取消")

if __name__ == "__main__":
    main()
