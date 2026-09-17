# LangTrans-AI

**LangTrans-AI** turns long-form audio and video into a timestamped, multilingual transcript, an optional translation in a language you select, and factual structured insights. It is a React/Vite client paired with a FastAPI service that uses Groq Whisper and Groq-hosted Llama models.

## What it solves

Meetings, lectures, interviews, and videos are difficult to search and reuse. Submit a local media file or a public direct-media/YouTube URL and follow the actual asynchronous job lifecycle while LangTrans-AI prepares audio, transcribes speech, optionally translates every timestamped segment, and produces reusable JSON.

## Features

- Drag-and-drop or browse upload, with format and size feedback.
- HTTP/HTTPS and public YouTube URL processing via `yt-dlp`.
- Whisper `whisper-large-v3` multilingual transcription with segment timestamps and ten-minute chunks.
- Optional translation into English, Spanish, French, German, Portuguese, Hindi, Japanese, Korean, Chinese, Arabic, Italian, Russian, Turkish, or Indonesian; original speech is always retained.
- Grounded Llama JSON summary: title, key points, topics, action items, exact quotes, and keywords.
- Job polling with real `queued → downloading/processing_audio → transcribing → translating → summarizing → completed` states and readable failure messages.
- Copy and TXT/JSON exports based on the completed job response.
- URL SSRF protection for private/local IP destinations, format allowlisting, bounded upload/download sizes, unique temp paths, and cleanup.

## Architecture

```text
React workspace → FastAPI POST /upload or /process-url → in-memory job
  → yt-dlp/direct download → FFmpeg mono 16 kHz WAV → chunked Groq Whisper
  → optional Groq Llama translation → grounded Groq Llama JSON → polling UI
```

Jobs are deliberately in-memory for this first version. Restarting the backend clears their history; replace `jobs_db` with Redis/Celery/database-backed jobs for multi-instance production deployments.

## Tech stack

- **Client:** React 19, Vite, Axios, Lucide React, custom responsive CSS
- **Server:** Python 3.10+, FastAPI, Pydantic, Groq SDK, pydub, FFmpeg/FFprobe, yt-dlp, langdetect

## Repository layout

```text
backend/app/             FastAPI routes, schemas, configuration, services
backend/app/services/    media ingestion, STT/translation, summary generation
frontend/src/            React UI and API client
backend/.env.example     safe environment template
```

## Prerequisites

- Python 3.10 or later and Node.js 18 or later.
- FFmpeg and FFprobe available on `PATH` (`ffmpeg -version`, `ffprobe -version`).
- A Groq API key with access to Whisper and Llama models.

On macOS use `brew install ffmpeg`; on Debian/Ubuntu use `sudo apt install ffmpeg`; on Windows use `winget install Gyan.FFmpeg` (then open a new terminal). Install Node/Python through their official installers when needed.

## Local setup

### Backend

```bash
cd backend
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell
# .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env  # Windows: copy .env.example .env
# Edit .env and add GROQ_API_KEY
cd ..
python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

The API documentation is at [http://localhost:8000/docs](http://localhost:8000/docs) and health check is `GET /health`.

### Frontend

```bash
cd frontend
npm install
# optional: echo VITE_API_URL=http://localhost:8000 > .env
npm run dev
```

Only `VITE_API_URL` belongs in the frontend environment. **Never** put `GROQ_API_KEY` in a Vite variable or client code.

## Environment configuration

| Variable | Required | Meaning |
| --- | --- | --- |
| `GROQ_API_KEY` | Yes for processing | Server-side Groq credential |
| `MAX_UPLOAD_BYTES` | No | Local upload cap, default 500 MB |
| `MAX_REMOTE_BYTES` | No | Direct-download cap, default 500 MB |
| `CORS_ORIGINS` | No | Comma-delimited allowed frontend origins |
| `VITE_API_URL` | No | Client API base URL, defaults to localhost:8000 |

Missing Groq configuration results in a failed job with a clear setup message; it is never silently replaced by fabricated AI output.

## API

### `POST /upload` (202)

Multipart fields: `file` (supported audio/video), `translate` (`false` by default), and `target_language` (used when translation is enabled).

### `POST /process-url` (202)

Multipart fields: `media_url` (public HTTP/HTTPS URL) plus the same translation fields.

### `GET /job/{job_id}`

Returns the current real status; after completion, `result` follows this shape:

```json
{
  "job_id": "...",
  "status": "completed",
  "progress": 100,
  "result": {
    "transcript": {"language": "es", "segments": [{"start": 0, "end": 2.4, "text": "..."}]},
    "translation": {"language": "English", "segments": [{"start": 0, "end": 2.4, "text": "..."}]},
    "summary": {"title": "...", "key_points": [], "topics": [], "action_items": [], "quotes": [], "keywords": []}
  }
}
```

`translation` is `null` when disabled. Unknown IDs return 404. Invalid URLs, unsupported formats, oversize uploads, FFmpeg/download errors, rate limits, malformed model results, and processing errors return safe user-facing errors without keys or stack traces.

## Supported inputs and limitations

Supported file extensions are MP3, WAV, M4A, AAC, OGG, FLAC, MP4, MOV, MKV, WEBM, AVI, MPEG, and MPG. A remote URL must be public and resolve to a global address; private/internal networks are blocked. Public YouTube availability depends on yt-dlp and source restrictions. Actual model limits/rate limits and available FFmpeg codecs apply; this project does not promise unlimited size or concurrency.

## Deployment

Deploy `frontend/` to Vercel or another static host and set `VITE_API_URL` to the deployed API. Deploy the server to Render or similar using `python -m uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`, install system FFmpeg/FFprobe, and configure `GROQ_API_KEY` and a restricted `CORS_ORIGINS` in the host’s secrets. Ensure ephemeral temp storage suits expected job duration.

## Future improvements

Add persisted jobs (Redis/Celery), authenticated workspaces, durable object storage, more translation targets, progress by chunk, automated mocked API/component tests, and deploy health monitoring.

## Contributing and license

Open an issue or PR with focused changes and tests. This repository is available under the MIT license (see the frontend license file).
