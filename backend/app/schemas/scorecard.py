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

class ProcessScorecardResponse(BaseModel):
    scorecard_id: str
    filename: str
    status: str
    completed_steps: int
    total_steps: int
    steps: List[ProcessingStepResponse]
    s3_paths: dict
    total_processing_time_ms: int