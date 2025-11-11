import logging
import time
import base64
from typing import List

from app.services.s3_service import s3_service
from app.processing import preprocessing_pipeline
from app.schemas.scorecard import ProcessingStepResponse, ProcessScorecardResponse

logger = logging.getLogger(__name__)

async def process_scorecard(s3_key: str) -> ProcessScorecardResponse:
    """
    Process a scorecard through the full pipeline
    
    Args:
        s3_key: S3 key of the scorecard image
    
    Returns:
        ProcessScorecardResponse with all steps and results
    """
    total_start = time.time()
    
    # Generate unique ID
    scorecard_id = s3_service.generate_scorecard_id()
    processed_folder = s3_service.get_processed_folder_path(scorecard_id)
    
    steps_response = []
    completed_s3_paths = []
    
    # Step 0: Fetch from S3
    step_start = time.time()
    logger.info(f"Processing scorecard {scorecard_id} from {s3_key}")
    
    image_bytes, filename = await s3_service.download_file(s3_key)
    print(filename, scorecard_id)
    
    # Convert original to base64 for display
    original_base64 = f"data:image/jpeg;base64,{base64.b64encode(image_bytes).decode('utf-8')}"
    
    steps_response.append(ProcessingStepResponse(
        step_name="fetch_from_s3",
        status="success",
        image_base64=original_base64,
        s3_path=s3_key,
        data={
            "filename": filename,
            "size_bytes": len(image_bytes)
        },
        processing_time_ms=int((time.time() - step_start) * 1000)
    ))
    
    # Run preprocessing pipeline
    logger.info("Starting preprocessing pipeline")
    preprocessing_steps, final_image = preprocessing_pipeline.run_pipeline(
        image_bytes, 
        include_base64=True
    )
    
    # Upload each step to S3 and build response
    step_number = 1
    for step in preprocessing_steps:
        if step.status == "error":
            # Failed step - add to response and stop
            steps_response.append(ProcessingStepResponse(
                step_name=step.step_name,
                status="error",
                error=step.error,
                processing_time_ms=step.processing_time_ms
            ))
            break
        
        # Determine file extension
        file_extension = 'png' if step.step_name == 'deskewing' else 'jpg'
        s3_key = f"{processed_folder}{step_number}_{step.step_name}.{file_extension}"
        
        try:
            await s3_service.upload_file(
                step.image_bytes,
                s3_key,
                content_type=f"image/{'png' if file_extension == 'png' else 'jpeg'}"
            )
            completed_s3_paths.append(s3_key)
            
            steps_response.append(ProcessingStepResponse(
                step_name=step.step_name,
                status="success",
                image_base64=step.image_base64,
                s3_path=s3_key,
                data=step.data,
                processing_time_ms=step.processing_time_ms
            ))
            
            step_number += 1
            
        except Exception as e:
            logger.error(f"Failed to upload {s3_key}: {e}")
            steps_response.append(ProcessingStepResponse(
                step_name=step.step_name,
                status="error",
                error=f"S3 upload failed: {str(e)}",
                processing_time_ms=step.processing_time_ms
            ))
            break
    
    # Determine overall status
    all_successful = all(s.status == "success" for s in steps_response)
    status = "success" if all_successful else "partial_failure"
    
    total_time = int((time.time() - total_start) * 1000)
    
    return ProcessScorecardResponse(
        scorecard_id=scorecard_id,
        filename=filename,
        status=status,
        completed_steps=len([s for s in steps_response if s.status == "success"]) - 1,
        total_steps=5,
        steps=steps_response,
        s3_paths={
            "raw": s3_key,
            "processed_folder": processed_folder,
            "completed": completed_s3_paths
        },
        total_processing_time_ms=total_time
    )