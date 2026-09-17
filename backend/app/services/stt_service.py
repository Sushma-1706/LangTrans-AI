"""Groq Whisper transcription and Llama-based segment translation."""
import math
import tempfile
from pathlib import Path
from groq import Groq
from langdetect import detect
from pydub import AudioSegment
from app.config import require_groq_key
from app.schemas import TranscriptSegment

CHUNK_DURATION_MS = 10 * 60 * 1000

def _client() -> Groq: return Groq(api_key=require_groq_key())
def _value(item, name, fallback): return item.get(name, fallback) if isinstance(item, dict) else getattr(item, name, fallback)

def transcribe_audio(audio_path: Path) -> tuple[str, list[TranscriptSegment]]:
    audio = AudioSegment.from_file(audio_path)
    segments, detected = [], None
    with tempfile.TemporaryDirectory() as temp:
        for index in range(max(1, math.ceil(len(audio) / CHUNK_DURATION_MS))):
            start_ms, end_ms = index * CHUNK_DURATION_MS, min((index + 1) * CHUNK_DURATION_MS, len(audio))
            chunk_path = Path(temp) / f"chunk-{index}.wav"
            audio[start_ms:end_ms].export(chunk_path, format="wav")
            with chunk_path.open("rb") as file:
                response = _client().audio.transcriptions.create(file=(chunk_path.name, file.read()), model="whisper-large-v3", response_format="verbose_json", timestamp_granularities=["segment"], temperature=0)
            detected = detected or _value(response, "language", None)
            raw = _value(response, "segments", []) or []
            if not raw and _value(response, "text", "").strip(): raw = [{"start": 0, "end": (end_ms-start_ms)/1000, "text": response.text}]
            for segment in raw:
                text = str(_value(segment, "text", "")).strip()
                if text:
                    start = start_ms / 1000 + float(_value(segment, "start", 0))
                    segments.append(TranscriptSegment(start=start, end=start_ms / 1000 + float(_value(segment, "end", 0)), text=text))
    joined = " ".join(segment.text for segment in segments)
    if not detected and joined:
        try: detected = detect(joined)
        except Exception: pass
    return detected or "unknown", segments

def translate_segments(segments: list[TranscriptSegment], target_language: str) -> list[TranscriptSegment]:
    if not segments: return []
    translated = []
    # Numbering gives us an auditable one-to-one segment mapping.
    for offset in range(0, len(segments), 50):
        batch = segments[offset:offset + 50]
        source = "\n".join(f"{number}. {segment.text}" for number, segment in enumerate(batch, 1))
        response = _client().chat.completions.create(model="openai/gpt-oss-120b", temperature=0,
            messages=[{"role":"system", "content":f"Translate every numbered line into {target_language}. Preserve line count, order, intent and names. Return numbered translations only; no commentary."}, {"role":"user", "content":source}])
        lines = response.choices[0].message.content.strip().splitlines()
        texts = []
        for line in lines:
            prefix, separator, body = line.partition(". ")
            if separator and prefix.strip().isdigit(): texts.append(body.strip())
        if len(texts) != len(batch):
            raise RuntimeError("Translation response did not preserve all transcript segments. Please retry.")
        translated.extend(TranscriptSegment(start=s.start, end=s.end, text=t) for s, t in zip(batch, texts))
    return translated
