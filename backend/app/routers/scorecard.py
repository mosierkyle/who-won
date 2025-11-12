from fastapi import APIRouter, HTTPException
from app.config import get_settings
import logging

from app.schemas.scorecard import ProcessScorecardRequest, ProcessScorecardResponse
from app.services import scorecard_service


logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


@router.post("/process-scorecard", response_model=ProcessScorecardResponse)
async def process_scorecard(request: ProcessScorecardRequest):
    """
    Process a scorecard from S3 through the full preprocessing pipeline
    """
    try:
        result = await scorecard_service.process_scorecard(request.s3_key)
        return result
    except Exception as e:
        logger.error(f"Error processing scorecard: {e}")
        raise HTTPException(status_code=500, detail=str(e))