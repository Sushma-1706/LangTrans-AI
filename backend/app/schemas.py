from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class JobState(str, Enum):
    queued = "queued"
    downloading = "downloading"
    processing_audio = "processing_audio"
    transcribing = "transcribing"
    translating = "translating"
    summarizing = "summarizing"
    completed = "completed"
    failed = "failed"

class TranscriptSegment(BaseModel):
    start: float = Field(ge=0)
    end: float = Field(ge=0)
    text: str

class Transcript(BaseModel):
    language: str
    segments: list[TranscriptSegment]

class Translation(BaseModel):
    language: str
    segments: list[TranscriptSegment]

class StructuredSummary(BaseModel):
    title: str
    key_points: list[str] = []
    topics: list[str] = []
    action_items: list[str] = []
    quotes: list[str] = []
    keywords: list[str] = []

class CompletedJobResult(BaseModel):
    transcript: Transcript
    translation: Optional[Translation] = None
    summary: StructuredSummary

class JobCreationResponse(BaseModel):
    job_id: str
    status: JobState
    progress: int = Field(ge=0, le=100)
    message: str

class JobStatusResponse(JobCreationResponse):
    source_name: Optional[str] = None
    result: Optional[CompletedJobResult] = None
    error: Optional[str] = None

class ErrorResponse(BaseModel):
    detail: str
