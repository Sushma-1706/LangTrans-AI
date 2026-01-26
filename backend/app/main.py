import uuid
import os
import shutil
import traceback
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from app.services import media_service, stt_service, llm_service
from app.schemas import JobStatus

# --- FIX FOR WINDOWS FFMPEG ---
import os
current_dir = os.path.dirname(os.path.abspath(__file__)) 
backend_dir = os.path.dirname(current_dir)
os.environ["PATH"] += os.pathsep + backend_dir
# ------------------------------

app = FastAPI(title="Distill AI")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database
jobs_db = {}
TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

# --- BACKGROUND TASK ---
def process_file_task(job_id: str, file_path: str, original_filename: str, translate: bool):
    """
    Background task that runs the AI pipeline.
    Now accepts 'translate' boolean.
    """
    try:
        jobs_db[job_id]["status"] = "processing_audio"
        jobs_db[job_id]["progress"] = 10
        print(f"👉 [Job {job_id}] Processing Audio...")
        
        # 1. Media Handling
        audio_path = os.path.join(TEMP_DIR, f"{job_id}.wav")
        media_service.extract_audio(file_path, audio_path)
        duration = media_service.get_duration(audio_path)
        
        jobs_db[job_id]["status"] = "transcribing"
        jobs_db[job_id]["progress"] = 30
        print(f"👉 [Job {job_id}] Transcribing (Translate={translate})...")
        
        # 2. Transcription (Passes translate flag)
        transcript_segments, full_text = stt_service.transcribe_audio(audio_path, translate=translate)
        
        jobs_db[job_id]["status"] = "summarizing"
        jobs_db[job_id]["progress"] = 70
        print(f"👉 [Job {job_id}] Summarizing...")
        
        # 3. LLM Summarization
        summary_json = llm_service.generate_final_summary(full_text, duration)
        
        # 4. Finalize
        jobs_db[job_id]["result"] = summary_json
        jobs_db[job_id]["transcript"] = transcript_segments
        jobs_db[job_id]["status"] = "completed"
        jobs_db[job_id]["progress"] = 100
        print(f"✅ [Job {job_id}] Completed!")
        
    except Exception as e:
        print(f"❌ [Job {job_id}] FAILED: {e}")
        traceback.print_exc()
        jobs_db[job_id]["status"] = "failed"
        jobs_db[job_id]["error"] = str(e)
    finally:
        # Cleanup
        if os.path.exists(file_path): os.remove(file_path)
        if os.path.exists(audio_path): os.remove(audio_path)

# --- API ENDPOINTS ---

@app.post("/upload", response_model=JobStatus)
async def upload_file(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...),
    translate: bool = Form(False) # <--- Accepts the flag from Frontend
):
    job_id = str(uuid.uuid4())
    file_path = os.path.join(TEMP_DIR, f"{job_id}_{file.filename}")
    
    # Save uploaded file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Init Job
    jobs_db[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "progress": 0,
        "result": None
    }
    
    # Start Task (Passes translate flag)
    background_tasks.add_task(process_file_task, job_id, file_path, file.filename, translate)
    
    return jobs_db[job_id]

@app.get("/job/{job_id}", response_model=JobStatus)
def get_job_status(job_id: str):
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs_db[job_id]