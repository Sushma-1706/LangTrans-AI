
"""Grounded structured-summary generation."""

import json

from groq import Groq

from app.config import require_groq_key
from app.schemas import StructuredSummary


def generate_summary(transcript: str, language: str) -> StructuredSummary:
    if not transcript.strip():
        return StructuredSummary(title="No speech detected")

    prompt = f"""Create a factual JSON summary of this {language} transcript.
Do not infer facts. Quotes must be exact short excerpts.
Use empty arrays when unsupported.

Schema: {{"title":"string","key_points":["string"],"topics":["string"],"action_items":["string"],"quotes":["string"],"keywords":["string"]}}

Transcript:
{transcript[:50000]}"""

    response = Groq(
        api_key=require_groq_key()
    ).chat.completions.create(
        model="openai/gpt-oss-120b",
        temperature=0.1,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": "Return valid JSON only.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    try:
        content = response.choices[0].message.content
        return StructuredSummary.model_validate(json.loads(content))
    except (json.JSONDecodeError, ValueError) as exc:
        raise RuntimeError(
            "The summary model returned an invalid structured response. Please retry."
        ) from exc