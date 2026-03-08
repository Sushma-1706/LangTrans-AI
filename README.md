# 🌍 LangTrans-AI

LangTrans-AI is a full-stack application that converts audio/video into structured insights using Groq.

It supports:
- file upload **or** URL-based media ingestion,
- multilingual speech-to-text transcription,
- optional translation to English (segment-by-segment with timestamps),
- AI-generated JSON summaries (title, key points, topics, actions, quotes, keywords).

---

## ✨ What this project does

1. Accepts media from:
   - Local file upload (`/upload`)
   - HTTP/HTTPS URL (`/process-url`), including YouTube links
2. Extracts mono 16k WAV audio with FFmpeg
3. Transcribes chunked audio with Groq Whisper (`whisper-large-v3`)
4. Optionally translates transcript segments to English
5. Generates a structured summary JSON with Groq Llama
6. Exposes progress + result through a polling job API  

---
## 🚀 Features

- 🎧 Upload audio/video files
- 🌐 Process media via URL (YouTube supported)
- 🧠 Multilingual speech transcription
- 🔄 Optional English translation
- 📊 AI-generated structured summaries
- ⏱ Timestamped transcript segments
- 📦 JSON output for downstream analysis
  
    ---

## 🧱 Tech stack

### Frontend
- React 19 + Vite
- Axios
- Lucide icons
- Custom CSS


### Backend
- FastAPI
- Groq Python SDK
- pydub + FFmpeg/FFprobe
- yt-dlp (for YouTube/media URL handling)
- langdetect



## 📁 Project structure

```text
LangTrans-AI/
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI app + async job orchestration
│   │   ├── config.py              # Environment config (GROQ_API_KEY)
│   │   ├── schemas.py             # Pydantic response models
│   │   └── services/
│   │       ├── media_service.py   # Download + ffmpeg extraction
│   │       ├── stt_service.py     # Whisper transcription + translation
│   │       └── llm_service.py     # Structured summary generation
│   ├── requirements.txt
│   ├── check_key.py               # API key quick check
│   └── debug.py                   # local diagnostics script
├── frontend/
│   ├── src/App.jsx                # Main UI and API interactions
│   ├── src/App.css
│   └── package.json
└── README.md
```
---

## 🔐 Environment variables

Create `backend/.env`:

```env
GROQ_API_KEY=your_api_key_here
```
> `PORT` is not currently consumed by backend config; run `uvicorn` with `--port` if needed.
---
## ✅ Prerequisites

- Python 3.10+
- Node.js 18+
- FFmpeg + FFprobe available either:
  - as local binaries in `backend/` named `ffmpeg.exe` and `ffprobe.exe`, **or**
  - installed on system `PATH` as `ffmpeg`/`ffprobe`
- (Recommended) `yt-dlp` installed for robust URL/YouTube ingestion
  
  ---
  
## 🚀 Local setup

### 1) Clone

```bash
git clone https://github.com/Sushma-1706/LangTrans-AI.git
cd LangTrans-AI
```

---

### 2) Backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows PowerShell/CMD
pip install -r requirements.txt
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend runs at: `http://127.0.0.1:8000`

---

### 3) Frontend setup

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: `http://localhost:5173`

---

## 🔌 API overview

### `POST /upload`
Multipart form:
- `file`: audio/video file
- `translate`: `true|false` (optional; default `false`)

Returns job metadata including `job_id`.

### `POST /process-url`
Multipart form:
- `media_url`: HTTP/HTTPS URL (supports YouTube handling)
- `translate`: `true|false` (optional)

Returns job metadata including `job_id`.

### `GET /job/{job_id}`
Poll this endpoint for status updates and final payload.

#### Job status lifecycle
`queued → downloading/processing_audio → transcribing → summarizing → completed`

`failed` includes an error string.

---
## 🧪 Useful diagnostics
From `backend/`:
```bash
python check_key.py   # validates that GROQ_API_KEY is visible + expected format
python debug.py       # checks ffmpeg binaries, API key, and groq package
```

---

## ⚠️ Notes / limitations

- Jobs are stored in in-memory `jobs_db`; restarting backend clears history.
- Temporary media files are processed in `temp/` and cleaned per job.
- Large media can take time because transcription is chunked.
- If URL download fails, ensure the link is a direct media file or supported YouTube URL.
---
## 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Open a Pull Request
---
## 📜 License

MIT (frontend includes MIT license file). Third-party APIs/tools have their own licenses and terms.

---

## 👩‍💻 Author

**Sushma Damacharla**  
AI & Frontend Developer
