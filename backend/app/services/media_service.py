import os
import subprocess
from pydub import AudioSegment

# 1. SETUP PATHS ABSOLUTELY
# This gets the folder where this script lives, then goes up one level to 'app', then 'backend'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FFMPEG_PATH = os.path.join(BASE_DIR, "ffmpeg.exe")
FFPROBE_PATH = os.path.join(BASE_DIR, "ffprobe.exe")

# Tell Pydub exactly where to look
AudioSegment.converter = FFMPEG_PATH
AudioSegment.ffprobe = FFPROBE_PATH

def extract_audio(input_path: str, output_path: str):
    """
    Extracts audio using the local ffmpeg.exe
    """
    # Check if files exist
    if not os.path.exists(FFMPEG_PATH):
        raise FileNotFoundError(f"CRITICAL: ffmpeg.exe not found at {FFMPEG_PATH}")

    print(f"Processing media with: {FFMPEG_PATH}")

    command = [
        FFMPEG_PATH,  # <--- USING FULL PATH
        "-i", input_path,
        "-ar", "16000",      
        "-ac", "1",          
        "-c:a", "pcm_s16le", 
        "-y",                
        output_path
    ]
    
    # Run and capture output in case of error
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FFmpeg failed: {e.stderr.decode()}")
        
    return output_path

def get_duration(file_path: str) -> float:
    # Use Pydub with the hardcoded paths
    if not os.path.exists(FFPROBE_PATH):
        print(f"WARNING: ffprobe.exe not found at {FFPROBE_PATH}. Duration check may fail.")
        
    try:
        audio = AudioSegment.from_file(file_path)
        return audio.duration_seconds
    except Exception as e:
        print(f"Error reading duration: {e}")
        return 0.0