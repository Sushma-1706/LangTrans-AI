# backend/app/services/stt_service.py
import math
import os
import tempfile
from typing import Dict, List, Optional

from groq import Groq
from langdetect import detect
from pydub import AudioSegment

from backend.app.config import GROQ_API_KEY
from backend.app.schemas import TranscriptSegment

client = Groq(api_key=GROQ_API_KEY)
CHUNK_DURATION_MS = 10 * 60 * 1000
TRANSLATION_BATCH_SIZE = 80
TRANSLATION_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
]


def _detect_language(text: str, model_language: Optional[str]) -> str:
    if model_language:
        return model_language
    if not text.strip():
        return "unknown"
    try:
        return detect(text)
    except Exception:
        return "unknown"


def _segment_field(segment, field: str, default):
    if isinstance(segment, dict):
        return segment.get(field, default)
    return getattr(segment, field, default)


def _translate_batch(numbered_input: str, prompt: str) -> str:
    last_error = None
    for model_name in TRANSLATION_MODELS:
        try:
            response = client.chat.completions.create(
                model=model_name,
                temperature=0.1,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": numbered_input},
                ],
            )
            return response.choices[0].message.content.strip()
        except Exception as exc:
            last_error = exc
            continue

    raise RuntimeError(f"Translation model call failed for all configured models: {last_error}")


def _translate_segment_texts(segment_texts: List[str], source_language: str) -> List[str]:
    if not segment_texts:
        return []

    prompt = (
        "You are an expert translator. Translate each numbered line from the source language "
        f"({source_language}) to English while preserving meaning and tone. "
        "Return exactly one translated line per input line in the same order. "
        "Do not add notes."
    )

    translated_all: List[str] = []
    for batch_start in range(0, len(segment_texts), TRANSLATION_BATCH_SIZE):
        batch = segment_texts[batch_start : batch_start + TRANSLATION_BATCH_SIZE]
        numbered_input = "\n".join([f"{i + 1}. {text}" for i, text in enumerate(batch)])

        output = _translate_batch(numbered_input, prompt).splitlines()

        for index, original in enumerate(batch):
            if index < len(output):
                line = output[index].strip()
                if ". " in line and line.split(". ", 1)[0].isdigit():
                    line = line.split(". ", 1)[1]
                translated_all.append(line or original)
            else:
                translated_all.append(original)

    return translated_all


def transcribe_audio(audio_path: str, translate: bool = False) -> Dict[str, object]:
    audio = AudioSegment.from_file(audio_path)
    total_chunks = max(1, math.ceil(len(audio) / CHUNK_DURATION_MS))

    transcript_segments: List[TranscriptSegment] = []
    detected_language = None

    with tempfile.TemporaryDirectory() as tmp_dir:
        for idx in range(total_chunks):
            start_ms = idx * CHUNK_DURATION_MS
            end_ms = min((idx + 1) * CHUNK_DURATION_MS, len(audio))
            chunk = audio[start_ms:end_ms]
            chunk_path = os.path.join(tmp_dir, f"chunk_{idx}.wav")
            chunk.export(chunk_path, format="wav")

            with open(chunk_path, "rb") as f:
                response = client.audio.transcriptions.create(
                    file=(os.path.basename(chunk_path), f.read()),
                    model="whisper-large-v3",
                    response_format="verbose_json",
                    timestamp_granularities=["segment"],
                    temperature=0.0,
                )

            chunk_language = getattr(response, "language", None)
            if not detected_language and chunk_language:
                detected_language = chunk_language

            raw_segments = getattr(response, "segments", []) or []
            if not raw_segments and getattr(response, "text", "").strip():
                raw_segments = [{"start": 0, "end": (end_ms - start_ms) / 1000, "text": response.text}]

            for seg in raw_segments:
                rel_start = float(_segment_field(seg, "start", 0.0))
                rel_end = float(_segment_field(seg, "end", rel_start))
                text = str(_segment_field(seg, "text", "")).strip()
                if not text:
                    continue

                transcript_segments.append(
                    TranscriptSegment(
                        start=(start_ms / 1000.0) + rel_start,
                        end=(start_ms / 1000.0) + rel_end,
                        text=text,
                    )
                )

    transcript_text = " ".join(seg.text for seg in transcript_segments).strip()
    detected_language = _detect_language(transcript_text, detected_language)

    translation_segments = None
    summary_text = transcript_text

    if translate and transcript_segments:
        translated = _translate_segment_texts([seg.text for seg in transcript_segments], detected_language)
        translation_segments = [
            TranscriptSegment(start=seg.start, end=seg.end, text=translated[idx])
            for idx, seg in enumerate(transcript_segments)
        ]
        summary_text = " ".join(seg.text for seg in translation_segments).strip()

    return {
        "transcript_segments": transcript_segments,
        "translation_segments": translation_segments,
        "detected_language": detected_language,
        "summary_text": summary_text,
    }