from pydantic import BaseModel
from typing import List, Optional

class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str

class SummaryResult(BaseModel):
    title: str
    duration: str
    executive_summary: str
    detailed_summary: str
    key_topics: List[str]
    key_points: List[str]
    important_quotes: List[str]
    action_items: List[str]
    keywords: List[str]
    summary_length: str
    compression_ratio: str

class JobStatus(BaseModel):
    job_id: str
    status: str  # "processing", "completed", "failed"
    progress: int # 0-100
    result: Optional[SummaryResult] = None
    transcript: Optional[List[TranscriptSegment]] = None
    error: Optional[str] = None