# backend/app/services/media_service.py
import mimetypes
import os
import shutil
import subprocess
import sys
from urllib.parse import urlparse
from typing import List, Tuple

import requests
from pydub import AudioSegment

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class MediaDownloadError(RuntimeError):
    pass


def _resolve_binary(local_name: str, system_name: str) -> str:
    local_path = os.path.join(BASE_DIR, local_name)
    if os.path.exists(local_path):
        return local_path

    resolved = shutil.which(system_name)
    if resolved:
        return resolved

    raise FileNotFoundError(f"Required binary not found: {local_name} or {system_name} in PATH")


def _is_youtube_url(media_url: str) -> bool:
    host = (urlparse(media_url).netloc or "").lower()
    return any(domain in host for domain in ["youtube.com", "youtu.be", "m.youtube.com"])


def _run_ytdlp_command(command: List[str]) -> Tuple[bool, str]:
    try:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True, result.stderr.decode(errors="ignore")
    except subprocess.CalledProcessError as exc:
        return False, exc.stderr.decode(errors="ignore")


def _download_with_ytdlp(media_url: str, temp_dir: str, job_id: str):
    output_template = os.path.join(temp_dir, f"{job_id}_download.%(ext)s")
    commands = []

    ytdlp_bin = shutil.which("yt-dlp")
    if ytdlp_bin:
        commands.append([
            ytdlp_bin,
            "--no-playlist",
            "-f",
            "bestaudio/best",
            "-o",
            output_template,
            media_url,
        ])

    # Fallback for environments where the script entry-point is not on PATH.
    commands.append([
        sys.executable,
        "-m",
        "yt_dlp",
        "--no-playlist",
        "-f",
        "bestaudio/best",
        "-o",
        output_template,
        media_url,
    ])

    last_error = ""
    for command in commands:
        ok, stderr = _run_ytdlp_command(command)
        if ok:
            prefix = f"{job_id}_download."
            for filename in os.listdir(temp_dir):
                if filename.startswith(prefix):
                    return os.path.join(temp_dir, filename), filename
            last_error = "yt-dlp finished but did not produce an output file."
            continue
        last_error = stderr[-500:]

    raise MediaDownloadError(
        "Failed to download YouTube URL. Ensure yt-dlp is installed and up-to-date. "
        f"Details: {last_error or 'yt-dlp unavailable'}"
    )


FFMPEG_PATH = _resolve_binary("ffmpeg.exe", "ffmpeg")
FFPROBE_PATH = _resolve_binary("ffprobe.exe", "ffprobe")

AudioSegment.converter = FFMPEG_PATH
AudioSegment.ffprobe = FFPROBE_PATH


def extract_audio(input_path: str, output_path: str):
    command = [
        FFMPEG_PATH,
        "-i",
        input_path,
        "-ar",
        "16000",
        "-ac",
        "1",
        "-c:a",
        "pcm_s16le",
        "-y",
        output_path,
    ]
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        error_tail = e.stderr.decode(errors="ignore")[-500:]
        raise RuntimeError(
            "FFmpeg could not decode this input. Ensure the URL points to a real audio/video file or use a supported source. "
            f"Details: {error_tail}"
        ) from e
    return output_path


def get_duration(file_path: str) -> float:
    try:
        audio = AudioSegment.from_file(file_path)
        return audio.duration_seconds
    except Exception:
        return 0.0


def _download_direct_file(media_url: str, temp_dir: str, job_id: str):
    try:
        response = requests.get(media_url, stream=True, timeout=120, allow_redirects=True)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise MediaDownloadError(f"Unable to download URL: {exc}") from exc

    content_type = (response.headers.get("Content-Type", "").split(";")[0]).strip().lower()
    if content_type.startswith("text/") or content_type in {"application/json", "application/xml", "text/html"}:
        raise MediaDownloadError(
            f"URL returned '{content_type}', not raw media. Use a direct audio/video file URL or a supported YouTube link."
        )

    parsed = urlparse(response.url)
    ext = os.path.splitext(parsed.path)[1]
    if not ext:
        ext = mimetypes.guess_extension(content_type) or ".bin"

    filename = os.path.basename(parsed.path) or f"source{ext}"
    output_path = os.path.join(temp_dir, f"{job_id}_download{ext}")

    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)

    return output_path, filename


def download_media_from_url(media_url: str, temp_dir: str, job_id: str):
    parsed = urlparse(media_url)
    if parsed.scheme not in {"http", "https"}:
        raise MediaDownloadError("Only HTTP/HTTPS URLs are supported.")

    if _is_youtube_url(media_url):
        return _download_with_ytdlp(media_url, temp_dir, job_id)

    return _download_direct_file(media_url, temp_dir, job_id)