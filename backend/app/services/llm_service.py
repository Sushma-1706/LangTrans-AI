"""Grounded structured-summary generation."""
import json
from groq import Groq
from backend.app.config import require_groq_key
from backend.app.schemas import StructuredSummary

def generate_summary(transcript: str, language: str) -> StructuredSummary:
    if not transcript.strip():
        return StructuredSummary(title="No speech detected")
    prompt = f"""Create a factual JSON summary of this {language} transcript. Do not infer facts. Quotes must be exact short excerpts; use empty arrays when unsupported.
Schema: {{"title":"string","key_points":["string"],"topics":["string"],"action_items":["string"],"quotes":["string"],"keywords":["string"]}}
Transcript:\n{transcript[:50000]}"""
    response = Groq(api_key=require_groq_key()).chat.completions.create(model="llama-3.3-70b-versatile", temperature=0.1, response_format={"type":"json_object"}, messages=[{"role":"system", "content":"Return valid JSON only."}, {"role":"user", "content":prompt}])
    try:
        return StructuredSummary.model_validate(json.loads(response.choices[0].message.content))
    except (json.JSONDecodeError, ValueError) as exc:
        raise RuntimeError("The summary model returned an invalid structured response. Please retry.") from exc
