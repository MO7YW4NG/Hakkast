from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import logging
import subprocess
import os
from pathlib import Path
import re

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audio", tags=["audio"])

# Request/Response Models
class AudioFile(BaseModel):
    filename: str
    path: str
    size: int
    duration: Optional[float] = None

class AudioMergeRequest(BaseModel):
    file_paths: List[str] = Field(..., description="List of audio file paths to merge")
    output_filename: str = Field(..., description="Output filename for merged audio")
    sample_rate: int = Field(default=44100, description="Audio sample rate")
    cleanup_source_files: bool = Field(default=False, description="Delete source files after merge")

class AudioMergeResponse(BaseModel):
    success: bool
    output_path: str
    output_url: str
    file_size: int
    merged_files_count: int
    message: str

class AudioFormatRequest(BaseModel):
    input_path: str = Field(..., description="Input audio file path")
    output_path: str = Field(..., description="Output audio file path")
    sample_rate: int = Field(default=44100, description="Target sample rate")

class AudioFormatResponse(BaseModel):
    success: bool
    input_path: str
    output_path: str
    output_url: str
    message: str

@router.get("/files/{script_name}")
async def list_audio_files(
    script_name: str,
    speaker_code: Optional[str] = Query(None, description="Filter by speaker code (SXF, SXM, HLF, HLM)")
):
    """List audio files for a specific script"""
    try:
        audio_dir = Path("static/audio")
        if not audio_dir.exists():
            audio_dir.mkdir(parents=True, exist_ok=True)
            return {"files": [], "total_files": 0}
        
        # Pattern to match audio files for the script
        if speaker_code:
            pattern = f"{script_name}_{speaker_code}_*.wav"
        else:
            pattern = f"{script_name}_*.wav"
        
        files = []
        for file_path in audio_dir.glob(pattern):
            if file_path.is_file():
                try:
                    size = file_path.stat().st_size
                    files.append(AudioFile(
                        filename=file_path.name,
                        path=str(file_path),
                        size=size,
                        duration=None  # Could add audio duration calculation here
                    ))
                except Exception as e:
                    logger.warning(f"Could not get info for file {file_path}: {e}")
        
        # Sort files by filename
        files.sort(key=lambda x: x.filename)
        
        return {
            "script_name": script_name,
            "speaker_code": speaker_code,
            "files": files,
            "total_files": len(files),
            "total_size": sum(f.size for f in files)
        }
        
    except Exception as e:
        logger.error(f"Failed to list audio files: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list audio files: {str(e)}"
        )

@router.post("/merge", response_model=AudioMergeResponse)
async def merge_audio_files(request: AudioMergeRequest):
    """Merge multiple audio files into one"""
    try:
        # Validate input files exist
        valid_files = []
        for file_path in request.file_paths:
            path = Path(file_path)
            if path.exists() and path.is_file():
                valid_files.append(str(path.resolve()))
            else:
                logger.warning(f"File not found: {file_path}")
        
        if not valid_files:
            raise HTTPException(
                status_code=400,
                detail="No valid audio files found"
            )
        
        # Prepare output path
        audio_dir = Path("static/audio")
        audio_dir.mkdir(parents=True, exist_ok=True)
        output_path = audio_dir / request.output_filename
        
        # Create file list for FFmpeg
        filelist_path = audio_dir / f"temp_filelist_{request.output_filename}.txt"
        try:
            with open(filelist_path, "w", encoding="utf-8") as f:
                for file_path in valid_files:
                    f.write(f"file '{file_path}'\n")
            
            # Check if FFmpeg is available
            try:
                subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                raise HTTPException(
                    status_code=500,
                    detail="FFmpeg is not installed or not available"
                )
            
            # FFmpeg command to merge files
            cmd = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', str(filelist_path),
                '-ar', str(request.sample_rate),
                '-ac', '1',
                '-sample_fmt', 's16',
                '-y',  # Overwrite output file
                str(output_path)
            ]
            
            # Run FFmpeg
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise HTTPException(
                    status_code=500,
                    detail=f"FFmpeg merge failed: {result.stderr}"
                )
            
            # Check if output file was created
            if not output_path.exists() or output_path.stat().st_size == 0:
                raise HTTPException(
                    status_code=500,
                    detail="Merged audio file was not created or is empty"
                )
            
            file_size = output_path.stat().st_size
            
            # Cleanup source files if requested
            if request.cleanup_source_files:
                for file_path in valid_files:
                    try:
                        Path(file_path).unlink()
                        logger.info(f"Deleted source file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to delete source file {file_path}: {e}")
            
            return AudioMergeResponse(
                success=True,
                output_path=str(output_path),
                output_url=f"/static/audio/{output_path.name}",
                file_size=file_size,
                merged_files_count=len(valid_files),
                message=f"Successfully merged {len(valid_files)} audio files"
            )
            
        finally:
            # Clean up temporary filelist
            if filelist_path.exists():
                filelist_path.unlink()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Audio merge failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Audio merge failed: {str(e)}"
        )

@router.post("/format-fix", response_model=AudioFormatResponse)
async def fix_audio_format(request: AudioFormatRequest):
    """Fix/convert audio file format using FFmpeg"""
    try:
        input_path = Path(request.input_path)
        output_path = Path(request.output_path)
        
        # Validate input file exists
        if not input_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Input file not found: {request.input_path}"
            )
        
        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if FFmpeg is available
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise HTTPException(
                status_code=500,
                detail="FFmpeg is not installed or not available"
            )
        
        # FFmpeg command to fix format
        cmd = [
            'ffmpeg',
            '-y',  # Overwrite output file
            '-i', str(input_path),
            '-ar', str(request.sample_rate),
            '-ac', '1',
            '-sample_fmt', 's16',
            str(output_path)
        ]
        
        # Run FFmpeg
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"FFmpeg format fix failed: {result.stderr}"
            )
        
        # Check if output file was created
        if not output_path.exists() or output_path.stat().st_size == 0:
            raise HTTPException(
                status_code=500,
                detail="Fixed audio file was not created or is empty"
            )
        
        return AudioFormatResponse(
            success=True,
            input_path=str(input_path),
            output_path=str(output_path),
            output_url=f"/static/audio/{output_path.name}" if "static/audio" in str(output_path) else "",
            message="Audio format fixed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Audio format fix failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Audio format fix failed: {str(e)}"
        )

@router.delete("/cleanup")
async def cleanup_audio_files(
    script_name: Optional[str] = Query(None, description="Script name to cleanup (optional)"),
    pattern: Optional[str] = Query(None, description="File pattern to match (optional)"),
    confirm: bool = Query(False, description="Confirm deletion")
):
    """Clean up temporary or old audio files"""
    try:
        if not confirm:
            raise HTTPException(
                status_code=400,
                detail="Must set confirm=true to delete files"
            )
        
        audio_dir = Path("static/audio")
        if not audio_dir.exists():
            return {"message": "Audio directory does not exist", "deleted_files": 0}
        
        deleted_files = []
        deleted_count = 0
        
        if script_name:
            # Delete files for specific script
            patterns = [f"{script_name}_*.wav", f"temp_{script_name}_*.wav"]
        elif pattern:
            # Delete files matching pattern
            patterns = [pattern]
        else:
            # Delete temporary files only
            patterns = ["temp_*.wav", "*_fixed.wav", "temp_filelist_*.txt"]
        
        for file_pattern in patterns:
            for file_path in audio_dir.glob(file_pattern):
                if file_path.is_file():
                    try:
                        file_path.unlink()
                        deleted_files.append(file_path.name)
                        deleted_count += 1
                        logger.info(f"Deleted file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to delete file {file_path}: {e}")
        
        return {
            "message": f"Cleanup completed. Deleted {deleted_count} files.",
            "deleted_files": deleted_files,
            "deleted_count": deleted_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Audio cleanup failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Audio cleanup failed: {str(e)}"
        )

@router.get("/info/{filename}")
async def get_audio_info(filename: str):
    """Get information about an audio file"""
    try:
        audio_dir = Path("static/audio")
        file_path = audio_dir / filename
        
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Audio file not found: {filename}"
            )
        
        # Get basic file info
        stat = file_path.stat()
        info = {
            "filename": filename,
            "path": str(file_path),
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "url": f"/static/audio/{filename}"
        }
        
        # Try to get audio duration using FFprobe if available
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_entries', 'format=duration',
                str(file_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                import json
                probe_data = json.loads(result.stdout)
                duration = float(probe_data.get('format', {}).get('duration', 0))
                info['duration'] = duration
        except Exception as e:
            logger.debug(f"Could not get audio duration for {filename}: {e}")
            info['duration'] = None
        
        return info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get audio info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get audio info: {str(e)}"
        )

@router.get("/scripts")
async def list_audio_scripts():
    """List all script names that have audio files"""
    try:
        audio_dir = Path("static/audio")
        if not audio_dir.exists():
            return {"scripts": []}
        
        # Find all audio files and extract script names
        scripts = set()
        for file_path in audio_dir.glob("*.wav"):
            if file_path.is_file():
                # Extract script name from filename pattern: script_name_speaker_index.wav
                match = re.match(r'^([^_]+(?:_[^_]+)*)_[A-Z]{2,3}_\d+.*\.wav$', file_path.name)
                if match:
                    script_name = match.group(1)
                    scripts.add(script_name)
        
        script_list = []
        for script_name in sorted(scripts):
            # Count files for each script
            file_count = len(list(audio_dir.glob(f"{script_name}_*.wav")))
            script_list.append({
                "name": script_name,
                "file_count": file_count
            })
        
        return {
            "scripts": script_list,
            "total_scripts": len(script_list)
        }
        
    except Exception as e:
        logger.error(f"Failed to list audio scripts: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list audio scripts: {str(e)}"
        )