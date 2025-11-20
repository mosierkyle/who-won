from pydantic import BaseModel
from typing import Optional, List

class ProcessScorecardRequest(BaseModel):
    s3_key: str

class ProcessingStepResponse(BaseModel):
    step_name: str
    status: str
    image_base64: Optional[str] = None
    s3_path: Optional[str] = None
    data: Optional[dict] = None
    processing_time_ms: int
    error: Optional[str] = None

class OCRWordResult(BaseModel):
    text: str
    confidence: float
    bbox: List[int]  # [x, y, width, height]

class OCRStepData(BaseModel):
    total_words: int
    words: List[OCRWordResult]
    full_text: str
    avg_confidence: float
    low_confidence_count: int  # Words below 70%

class ProcessScorecardResponse(BaseModel):
    scorecard_id: str
    filename: str
    status: str
    completed_steps: int
    total_steps: int
    steps: List[ProcessingStepResponse]
    s3_paths: dict
    total_processing_time_ms: int

class ProcessScorecardClaudeRequest(BaseModel):
    s3_key: str

class ProcessScorecardClaudeResponse(BaseModel):
    scorecard_id: str
    filename: str
    method: str = "claude_api"
    players: list
    winner: str = None
    course: str = None
    date: str = None
    processing_time_ms: int