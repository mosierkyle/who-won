from pydantic import BaseModel, Field
from typing import List, Optional

# Request/Response Models

class UploadAndProcessRequest(BaseModel):
    """Request model for uploading image via backend (not needed for multipart, but good for docs)"""
    pass

class Player(BaseModel):
    """Player data with scores"""
    name: str
    scores: List[Optional[int]] = Field(..., min_length=18, max_length=18)
    handicap: Optional[int] = None
    total: Optional[int] = None  # Calculated on backend
    front_nine_total: Optional[int] = None  # NEW: Holes 1-9 total
    back_nine_total: Optional[int] = None   # NEW: Holes 10-18 total

class ScorecardData(BaseModel):
    """Complete scorecard data"""
    course: Optional[str] = None
    date: Optional[str] = None
    par: Optional[List[Optional[int]]] = Field(None, min_length=18, max_length=18)
    players: List[Player]

class ProcessScorecardResponse(BaseModel):
    """Response after processing scorecard"""
    scorecard_id: str
    data: ScorecardData
    winner: Optional[str] = None  # For stroke play
    processing_time_ms: int

class ExportRequest(BaseModel):
    """Request to export scorecard data"""
    data: ScorecardData
    format: str = Field(..., pattern="^(csv|excel)$")  # Only csv or excel