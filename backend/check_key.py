from dotenv import load_dotenv
import os

load_dotenv()

key = os.getenv("GROQ_API_KEY")

print("-" * 30)
if key:
    print(f"✅ Key Found: {key[:8]}...{key[-4:]}")
    if not key.startswith("gsk_"):
        print("❌ ERROR: Key does not start with 'gsk_'. This is not a Groq key!")
    else:
        print("✅ Format looks correct (Starts with 'gsk_')")
else:
    print("❌ ERROR: Python cannot find 'GROQ_API_KEY' in .env")
print("-" * 30)