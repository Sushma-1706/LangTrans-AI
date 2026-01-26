import os
import sys

print("\n" + "="*40)
print("🔍 DIAGNOSTIC TOOL FOR WINDOWS")
print("="*40)

# 1. CHECK CURRENT DIRECTORY
cwd = os.getcwd()
print(f"📂 Working Directory: {cwd}")

# 2. CHECK FFMPEG
print("\n[1] Checking FFmpeg...")
ffmpeg_path = os.path.join(cwd, "ffmpeg.exe")
ffprobe_path = os.path.join(cwd, "ffprobe.exe")

if os.path.exists(ffmpeg_path):
    print(f"   ✅ PASSED: ffmpeg.exe found.")
else:
    print(f"   ❌ FAILED: ffmpeg.exe NOT found in this folder.")
    print(f"      Expected location: {ffmpeg_path}")

if os.path.exists(ffprobe_path):
    print(f"   ✅ PASSED: ffprobe.exe found.")
else:
    print(f"   ❌ FAILED: ffprobe.exe NOT found.")

# 3. CHECK API KEY
print("\n[2] Checking OpenAI API Key...")
try:
    from dotenv import load_dotenv
    load_dotenv()
    key = os.getenv("OPENAI_API_KEY")
    
    if key and key.startswith("sk-"):
        print("   ✅ PASSED: API Key appears valid.")
    elif key:
        print("   ⚠️ WARNING: API Key found but doesn't start with 'sk-'. It might be invalid.")
    else:
        print("   ❌ FAILED: 'OPENAI_API_KEY' not found in .env file.")
except Exception as e:
    print(f"   ❌ ERROR reading .env: {e}")

# 4. CHECK MODEL DEPENDENCIES
print("\n[3] Checking AI Libraries...")
try:
    import faster_whisper
    print("   ✅ PASSED: faster_whisper is installed.")
except ImportError:
    print("   ❌ FAILED: faster_whisper is NOT installed.")

print("\n" + "="*40)