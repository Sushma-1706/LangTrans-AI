import os
import json
from groq import Groq
from backend.app.config import GROQ_API_KEY

# Initialize Groq Client
client = Groq(api_key=GROQ_API_KEY)

def generate_final_summary(full_text_or_summaries, duration_seconds):
    """
    Generates a summary using Groq (Cloud Llama 3).
    It is FREE and extremely FAST.
    """
    
    minutes = int(duration_seconds // 60)
    seconds = int(duration_seconds % 60)
    duration_str = f"{minutes}m {seconds}s"
    
    print("🚀 Sending transcript to Groq Cloud...")

    try:
        # Prompt
        prompt = f"""
        Analyze the following transcript and generate a structured JSON summary.
        
        TRANSCRIPT:
        {full_text_or_summaries[:15000]}
        
        INSTRUCTIONS:
        Output strictly valid JSON matching this schema:
        {{
          "title": "Short Title",
          "executive_summary": "High-level summary",
          "detailed_summary": "Detailed summary",
          "key_topics": ["Topic 1", "Topic 2"],
          "key_points": ["Point 1", "Point 2"],
          "important_quotes": ["Quote 1"],
          "action_items": ["Action 1"],
          "keywords": ["Keyword 1"]
        }}
        """

        # Call Groq API (Using Llama-3.3-70b or similar)
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful AI analyst. Output JSON only."
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.3-70b-versatile", # Very smart, very fast model
            response_format={"type": "json_object"},
        )

        # Parse Response
        result_content = chat_completion.choices[0].message.content
        data = json.loads(result_content)
        
        # Add Metadata
        data['duration'] = duration_str
        data['summary_length'] = f"{len(data.get('detailed_summary', '').split())} words"
        data['compression_ratio'] = "Groq AI"
        
        return data

    except Exception as e:
        print(f"❌ Groq Error: {e}")
        return {
            "title": "Error Generating Summary",
            "duration": duration_str,
            "executive_summary": f"Failed to connect to Groq: {str(e)}",
            "detailed_summary": "Check your API Key in .env",
            "key_topics": [],
            "action_items": [],
            "important_quotes": [],
            "keywords": [],
            "summary_length": "0",
            "compression_ratio": "Error"
        }