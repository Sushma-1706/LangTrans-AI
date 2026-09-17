"""FastAPI API and in-memory background job orchestration."""
import uuid
from pathlib import Path
from typing import Annotated
from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import CORS_ORIGINS, MAX_UPLOAD_BYTES, TEMP_DIR
from backend.app.schemas import CompletedJobResult, JobCreationResponse, JobState, JobStatusResponse, Transcript, Translation
from backend.app.services import llm_service, media_service, stt_service

app = FastAPI(title="LangTrans-AI", description="Multilingual audio and video intelligence API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["*"])
jobs_db: dict[str, dict] = {}
TEMP_DIR.mkdir(parents=True, exist_ok=True)

def update(job_id, status, progress, **values): jobs_db[job_id].update(status=status, progress=progress, **values)
def job(job_id, source):
    jobs_db[job_id] = {"job_id":job_id,"status":JobState.queued,"progress":0,"message":"Job accepted and queued.","source_name":source,"result":None,"error":None}; return jobs_db[job_id]
def process(job_id: str, input_path: Path, translate: bool, target_language: str):
    audio_path = TEMP_DIR / f"{job_id}.wav"
    try:
        update(job_id, JobState.processing_audio, 15, message="Preparing mono 16 kHz audio.")
        media_service.extract_audio(input_path, audio_path)
        update(job_id, JobState.transcribing, 40, message="Transcribing speech with Groq Whisper.")
        language, segments = stt_service.transcribe_audio(audio_path)
        if not segments: raise RuntimeError("No speech was detected in the media.")
        translation = None
        summary_text = " ".join(s.text for s in segments)
        if translate:
            update(job_id, JobState.translating, 70, message=f"Translating segments into {target_language}.")
            translated = stt_service.translate_segments(segments, target_language)
            translation = Translation(language=target_language, segments=translated)
            summary_text = " ".join(s.text for s in translated)
        update(job_id, JobState.summarizing, 85, message="Generating grounded structured insights.")
        result = CompletedJobResult(transcript=Transcript(language=language, segments=segments), translation=translation, summary=llm_service.generate_summary(summary_text, target_language if translate else language))
        update(job_id, JobState.completed, 100, message="Analysis complete.", result=result)
    except Exception as exc:
        update(job_id, JobState.failed, 100, message="Processing failed.", error=str(exc))
    finally:
        input_path.unlink(missing_ok=True); audio_path.unlink(missing_ok=True)
def process_url_task(job_id, url, translate, target):
    try:
        update(job_id, JobState.downloading, 5, message="Downloading remote media.")
        path, name = media_service.download_media_from_url(url, TEMP_DIR, job_id)
        jobs_db[job_id]["source_name"] = name
        process(job_id, path, translate, target)
    except Exception as exc: update(job_id, JobState.failed, 100, message="Download failed.", error=str(exc))

@app.get("/health")
def health(): return {"status":"ok"}
@app.post("/upload", response_model=JobCreationResponse, status_code=202)
async def upload(background_tasks: BackgroundTasks, file: Annotated[UploadFile, File(...)], translate: Annotated[bool, Form()] = False, target_language: Annotated[str, Form()] = "English"):
    try: media_service.validate_filename(file.filename or "")
    except media_service.MediaError as exc: raise HTTPException(415, str(exc))
    job_id = str(uuid.uuid4()); path = TEMP_DIR / f"{job_id}{Path(file.filename).suffix.lower()}"; size = 0
    with path.open("wb") as destination:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_UPLOAD_BYTES: path.unlink(missing_ok=True); raise HTTPException(413, "File exceeds the configured upload limit.")
            destination.write(chunk)
    record = job(job_id, file.filename or "upload")
    background_tasks.add_task(process, job_id, path, translate, target_language)
    return record
@app.post("/process-url", response_model=JobCreationResponse, status_code=202)
def process_url(background_tasks: BackgroundTasks, media_url: Annotated[str, Form(...)], translate: Annotated[bool, Form()] = False, target_language: Annotated[str, Form()] = "English"):
    try: media_service.validate_public_url(media_url)
    except media_service.MediaDownloadError as exc: raise HTTPException(422, str(exc))
    job_id = str(uuid.uuid4()); record = job(job_id, media_url)
    background_tasks.add_task(process_url_task, job_id, media_url, translate, target_language)
    return record
@app.get("/job/{job_id}", response_model=JobStatusResponse)
def get_job(job_id: str):
    if job_id not in jobs_db: raise HTTPException(404, "Job not found. Jobs are cleared when the backend restarts.")
    return jobs_db[job_id]
