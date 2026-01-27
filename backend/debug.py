import os
import sys
from dotenv import load_dotenv

print("\n" + "="*40)
print("🔍 DIAGNOSTIC TOOL (GROQ EDITION)")
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
    print(f"   ❌ FAILED: ffmpeg.exe NOT found.")

if os.path.exists(ffprobe_path):
    print(f"   ✅ PASSED: ffprobe.exe found.")
else:
    print(f"   ❌ FAILED: ffprobe.exe NOT found.")

# 3. CHECK GROQ API KEY
print("\n[2] Checking Groq API Key...")
try:
    load_dotenv()
    key = os.getenv("GROQ_API_KEY")
    
    if key and key.startswith("gsk_"):
        print("   ✅ PASSED: Groq API Key found and looks valid.")
    elif key:
        print(f"   ⚠️ WARNING: Key found but doesn't start with 'gsk_'. Check .env")
    else:
        print("   ❌ FAILED: 'GROQ_API_KEY' not found in .env file.")
except Exception as e:
    print(f"   ❌ ERROR reading .env: {e}")

# 4. CHECK LIBRARIES
print("\n[3] Checking Python Libraries...")
try:
    import groq
    print("   ✅ PASSED: 'groq' library is installed.")
except ImportError:
    print("   ❌ FAILED: 'groq' library is MISSING. Run: pip install groq")

print("\n" + "="*40)