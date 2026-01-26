import os
from groq import Groq
from app.config import GROQ_API_KEY
from app.schemas import TranscriptSegment

# Initialize Groq Client
client = Groq(api_key=GROQ_API_KEY)

def transcribe_audio(audio_path: str, translate: bool = False):
    """
    1. Sends audio to Groq Whisper (Fast Transcription)
    2. If translating, sends text to Groq Llama 3 (Grammar Correction)
    """
    
    filename = os.path.basename(audio_path)
    
    try:
        # STEP 1: AUDIO -> TEXT (Whisper)
        with open(audio_path, "rb") as file:
            file_content = file.read()
            
            if translate:
                print(f"🌍 Mode: TRANSLATION (Whisper Large V3)")
                response = client.audio.translations.create(
                    file=(filename, file_content),
                    model="whisper-large-v3",
                    temperature=0.0 # Make it deterministic
                )
            else:
                print(f"🎤 Mode: TRANSCRIPTION (Whisper Large V3)")
                response = client.audio.transcriptions.create(
                    file=(filename, file_content),
                    model="whisper-large-v3",
                    temperature=0.0
                )

        raw_text = response.text
        
        # STEP 2: TEXT -> POLISHED TEXT (Llama 3)
        # Only do this if we translated, to fix "wrong" grammar
        final_text = raw_text
        
        if translate and raw_text:
            print("✨ Polishing translation with Llama 3...")
            try:
                completion = client.chat.completions.create(
                    model="llama3-70b-8192", # Very smart model
                    messages=[
                        {
                            "role": "system", 
                            "content": "You are a professional translator. The user will provide a raw transcript. Your job is to correct grammar, awkward phrasing, and translation errors while preserving the original meaning exactly. Do not summarize. Output ONLY the corrected text."
                        },
                        {
                            "role": "user", 
                            "content": raw_text
                        }
                    ],
                    temperature=0.3
                )
                final_text = completion.choices[0].message.content
            except Exception as e:
                print(f"⚠️ Polish step failed, using raw text: {e}")

        print("✅ Processing Complete!")

        # Create segment
        dummy_segment = TranscriptSegment(
            start=0.0,
            end=0.0, 
            text=final_text
        )
        
        return [dummy_segment], final_text.strip()

    except Exception as e:
        print(f"❌ Groq Audio Error: {e}")
        raise RuntimeError(f"Audio processing failed: {str(e)}")