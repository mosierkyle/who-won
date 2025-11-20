from fastapi import APIRouter, HTTPException
from app.config import get_settings
import logging

from app.schemas.scorecard import ProcessScorecardRequest, ProcessScorecardResponse, ProcessScorecardClaudeRequest, ProcessScorecardClaudeResponse
from app.services import scorecard_service
from app.services.s3_service import s3_service
from app.services.claude_ocr_service import get_claude_service



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


@router.post("/process-scorecard-claude", response_model=ProcessScorecardClaudeResponse)
async def process_scorecard_claude_endpoint(request: ProcessScorecardClaudeRequest):
    """Process scorecard using Claude Vision API"""
    try:
        import time
        start_time = time.time()
        
        # Generate scorecard ID
        scorecard_id = s3_service.generate_scorecard_id()
        
        # Download image from S3
        logger.info(f"Processing scorecard {scorecard_id} with Claude API")
        image_bytes, filename = await s3_service.download_file(request.s3_key)
        
        # Extract data using Claude
        claude = get_claude_service()
        result = await claude.extract_scorecard_data(image_bytes)
        
        # Calculate processing time
        processing_time = int((time.time() - start_time) * 1000)
        
        # Build response
        return ProcessScorecardClaudeResponse(
            scorecard_id=scorecard_id,
            filename=filename,
            players=result.get('players', []),
            winner=result.get('winner'),
            course=result.get('course'),
            date=result.get('date'),
            processing_time_ms=processing_time
        )
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise HTTPException(status_code=500, detail="Claude API not configured. Please set ANTHROPIC_API_KEY environment variable.")
    except Exception as e:
        logger.error(f"Error processing scorecard with Claude: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))