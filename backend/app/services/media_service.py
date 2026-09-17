"""Safe media ingestion and FFmpeg preprocessing."""
import ipaddress
import mimetypes
import shutil
import socket
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

import requests
from app.config import MAX_REMOTE_BYTES

SUPPORTED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".mp4", ".mov", ".mkv", ".webm", ".avi", ".mpeg", ".mpg"}

class MediaError(RuntimeError): pass
class MediaDownloadError(MediaError): pass

def _binary(name: str) -> str:
    found = shutil.which(name)
    if not found:
        raise MediaError(f"{name} is not installed or is not available on PATH. Install FFmpeg and retry.")
    return found

def validate_filename(filename: str) -> None:
    if Path(filename or "").suffix.lower() not in SUPPORTED_EXTENSIONS:
        allowed = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise MediaError(f"Unsupported media type. Supported extensions: {allowed}.")

def validate_public_url(media_url: str) -> str:
    parsed = urlparse(media_url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise MediaDownloadError("Enter a valid public HTTP or HTTPS media URL.")
    try:
        addresses = socket.getaddrinfo(parsed.hostname, parsed.port or 443, type=socket.SOCK_STREAM)
        for _, _, _, _, sockaddr in addresses:
            address = ipaddress.ip_address(sockaddr[0])
            if not address.is_global:
                raise MediaDownloadError("Private, local, and internal network URLs are not allowed.")
    except socket.gaierror as exc:
        raise MediaDownloadError("The media host could not be resolved.") from exc
    return media_url.strip()

def is_youtube_url(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return host == "youtu.be" or host.endswith("youtube.com")

def download_media_from_url(media_url: str, temp_dir: Path, job_id: str) -> tuple[Path, str]:
    validate_public_url(media_url)
    temp_dir.mkdir(parents=True, exist_ok=True)
    if is_youtube_url(media_url):
        command = [sys.executable, "-m", "yt_dlp", "--no-playlist", "-f", "bestaudio/best", "-o", str(temp_dir / f"{job_id}.%(ext)s"), media_url]
        result = subprocess.run(command, capture_output=True, text=True, timeout=300)
        files = [path for path in temp_dir.glob(f"{job_id}.*") if path.suffix != ".part"]
        if result.returncode or not files:
            raise MediaDownloadError("YouTube download failed. Confirm the video is public and yt-dlp is up to date.")
        return files[0], files[0].name
    try:
        response = requests.get(media_url, stream=True, timeout=(10, 120), allow_redirects=True)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise MediaDownloadError("Unable to download the supplied URL.") from exc
    content_type = response.headers.get("Content-Type", "").lower()
    if "text/html" in content_type or "application/json" in content_type:
        raise MediaDownloadError("The URL returned a webpage, not a media file.")
    extension = Path(urlparse(response.url).path).suffix or mimetypes.guess_extension(content_type.split(";", 1)[0]) or ".media"
    output = temp_dir / f"{job_id}{extension}"
    total = 0
    with output.open("wb") as destination:
        for chunk in response.iter_content(1024 * 1024):
            total += len(chunk)
            if total > MAX_REMOTE_BYTES:
                output.unlink(missing_ok=True)
                raise MediaDownloadError("Remote media exceeds the configured size limit.")
            destination.write(chunk)
    return output, Path(urlparse(response.url).path).name or output.name

def extract_audio(input_path: Path, output_path: Path) -> float:
    ffmpeg, ffprobe = _binary("ffmpeg"), _binary("ffprobe")
    probe = subprocess.run([ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(input_path)], capture_output=True, text=True)
    try: duration = float(probe.stdout.strip())
    except ValueError: raise MediaError("The uploaded file does not contain readable audio or video.")
    result = subprocess.run([ffmpeg, "-v", "error", "-i", str(input_path), "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", "-y", str(output_path)], capture_output=True, text=True)
    if result.returncode:
        raise MediaError("FFmpeg could not extract audio from this file.")
    return duration
