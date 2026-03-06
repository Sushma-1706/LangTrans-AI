# backend/app/main.py
import os
import shutil
import traceback
import uuid

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from backend.app.schemas import JobStatus
from backend.app.services import llm_service, media_service, stt_service
from backend.app.services.media_service import MediaDownloadError

app = FastAPI(title="LangTrans AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

jobs_db = {}
TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)


def process_media_task(
    job_id: str,
    input_path: str,
    source_name: str,
    source_type: str,
    translate: bool,
):
    audio_path = os.path.join(TEMP_DIR, f"{job_id}.wav")
    try:
        jobs_db[job_id]["status"] = "processing_audio"
        jobs_db[job_id]["progress"] = 10

        media_service.extract_audio(input_path, audio_path)
        duration = media_service.get_duration(audio_path)

        jobs_db[job_id]["status"] = "transcribing"
        jobs_db[job_id]["progress"] = 30

        stt_result = stt_service.transcribe_audio(audio_path, translate=translate)

        jobs_db[job_id]["status"] = "summarizing"
        jobs_db[job_id]["progress"] = 75

        summary_json = llm_service.generate_final_summary(stt_result["summary_text"], duration)

        jobs_db[job_id]["result"] = summary_json
        jobs_db[job_id]["transcript"] = stt_result["transcript_segments"]
        jobs_db[job_id]["translation"] = stt_result["translation_segments"]
        jobs_db[job_id]["detected_language"] = stt_result["detected_language"]
        jobs_db[job_id]["source_type"] = source_type
        jobs_db[job_id]["source_name"] = source_name
        jobs_db[job_id]["status"] = "completed"
        jobs_db[job_id]["progress"] = 100
    except Exception as exc:
        traceback.print_exc()
        jobs_db[job_id]["status"] = "failed"
        jobs_db[job_id]["error"] = str(exc)
        jobs_db[job_id]["progress"] = 100
    finally:
        for path in (input_path, audio_path):
            if path and os.path.exists(path):
                os.remove(path)


def process_url_task(job_id: str, media_url: str, translate: bool):
    try:
        jobs_db[job_id]["status"] = "downloading"
        jobs_db[job_id]["progress"] = 5
        downloaded_path, derived_name = media_service.download_media_from_url(media_url, TEMP_DIR, job_id)
    except MediaDownloadError as exc:
        jobs_db[job_id]["status"] = "failed"
        jobs_db[job_id]["progress"] = 100
        jobs_db[job_id]["error"] = str(exc)
        return

    process_media_task(job_id, downloaded_path, derived_name, "url", translate)


@app.post("/upload", response_model=JobStatus)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    translate: bool = Form(False),
):
    job_id = str(uuid.uuid4())
    file_path = os.path.join(TEMP_DIR, f"{job_id}_{file.filename}")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    jobs_db[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "progress": 0,
        "result": None,
        "source_name": file.filename,
        "source_type": "file",
    }

    background_tasks.add_task(
        process_media_task,
        job_id,
        file_path,
        file.filename,
        "file",
        translate,
    )

    return jobs_db[job_id]


@app.post("/process-url", response_model=JobStatus)
async def process_url(
    background_tasks: BackgroundTasks,
    media_url: str = Form(...),
    translate: bool = Form(False),
):
    job_id = str(uuid.uuid4())
    jobs_db[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "progress": 0,
        "result": None,
        "source_name": media_url,
        "source_type": "url",
    }

    background_tasks.add_task(process_url_task, job_id, media_url, translate)
    return jobs_db[job_id]


@app.get("/job/{job_id}", response_model=JobStatus)
def get_job_status(job_id: str):
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs_db[job_id]