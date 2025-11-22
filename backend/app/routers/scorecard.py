from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
import logging
import time
import io

from app.schemas.scorecard import ProcessScorecardResponse, ScorecardData, Player, ExportRequest
from app.services.s3_service import s3_service
from app.services.claude_service import get_claude_service
from app.services.game_modes import process_players
from app.services.export_service import export_to_csv

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/upload-and-process", response_model=ProcessScorecardResponse)
async def upload_and_process_scorecard(file: UploadFile = File(...)):
    """
    Upload scorecard image and process it with Claude API
    """
    try:
        start_time = time.time()
        
        logger.info(f"Received file: {file.filename}, content_type: {file.content_type}")
        
        # Validate file type
        if not file.content_type.startswith('image/'):
            logger.error(f"Invalid file type: {file.content_type}")
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Generate scorecard ID
        scorecard_id = s3_service.generate_scorecard_id()
        logger.info(f"Processing scorecard {scorecard_id}")
        
        # Read file bytes
        file_bytes = await file.read()
        logger.info(f"Read {len(file_bytes)} bytes from upload")
        
        # Upload to S3
        s3_key = f"uploads/{scorecard_id}/{file.filename}"
        await s3_service.upload_file(file_bytes, s3_key, file.content_type)
        logger.info(f"Uploaded to S3: {s3_key}")
        
        # Extract data using Claude
        logger.info("Sending to Claude API...")
        claude = get_claude_service()
        raw_data = await claude.extract_scorecard_data(file_bytes)
        logger.info(f"Claude response: {raw_data}")
        
        # Convert to Pydantic models
        players = [Player(**p) for p in raw_data.get('players', [])]
        logger.info(f"Converted {len(players)} players")
        
        # Calculate totals and winner
        players_with_totals, winner = process_players(players)
        logger.info(f"Winner: {winner}")
        
        # Build scorecard data
        scorecard_data = ScorecardData(
            course=raw_data.get('course'),
            date=raw_data.get('date'),
            par=raw_data.get('par'),
            players=players_with_totals
        )
        
        # Calculate processing time
        processing_time = int((time.time() - start_time) * 1000)
        
        logger.info(f"✅ Processed scorecard {scorecard_id} in {processing_time}ms")
        
        return ProcessScorecardResponse(
            scorecard_id=scorecard_id,
            data=scorecard_data,
            winner=winner,
            processing_time_ms=processing_time
        )
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail="Claude API not configured. Please set ANTHROPIC_API_KEY environment variable."
        )
    except Exception as e:
        logger.error(f"❌ Error processing scorecard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export")
async def export_scorecard(request: ExportRequest):
    """
    Export scorecard data to CSV or Excel
    
    Args:
        request: Scorecard data and format (csv or excel)
        
    Returns:
        File download
    """
    try:
        if request.format == "csv":
            csv_bytes = export_to_csv(request.data)
            
            return StreamingResponse(
                io.BytesIO(csv_bytes),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=scorecard.csv"}
            )
        
        elif request.format == "excel":
            # TODO: Implement Excel export in Phase 1.5
            raise HTTPException(status_code=501, detail="Excel export not yet implemented")
        
        else:
            raise HTTPException(status_code=400, detail="Invalid format. Use 'csv' or 'excel'")
            
    except Exception as e:
        logger.error(f"Error exporting scorecard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))