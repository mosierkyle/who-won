import logging
import time
import base64
from typing import List

from app.services.s3_service import s3_service
from app.processing import preprocessing_pipeline
from app.processing import ocr_engine
from app.processing import image_operations as ops
from app.schemas.scorecard import (
    ProcessingStepResponse, 
    ProcessScorecardResponse,
    OCRWordResult,
    OCRStepData
)

logger = logging.getLogger(__name__)

async def process_scorecard(s3_key: str) -> ProcessScorecardResponse:
    """
    Process a scorecard through the full pipeline including OCR
    
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
    preprocessing_steps, final_image_bytes = preprocessing_pipeline.run_pipeline(
        image_bytes, 
        include_base64=True
    )
    
    # Upload each preprocessing step to S3
    step_number = 1
    final_preprocessed_img = None  # Save for OCR
    
    for step in preprocessing_steps:
        if step.status == "error":
            steps_response.append(ProcessingStepResponse(
                step_name=step.step_name,
                status="error",
                error=step.error,
                processing_time_ms=step.processing_time_ms
            ))
            break
        
        # Determine file extension
        file_extension = 'png' if step.step_name == 'deskewing' else 'jpg'
        s3_key_step = f"{processed_folder}{step_number}_{step.step_name}.{file_extension}"
        
        try:
            await s3_service.upload_file(
                step.image_bytes,
                s3_key_step,
                content_type=f"image/{'png' if file_extension == 'png' else 'jpeg'}"
            )
            completed_s3_paths.append(s3_key_step)
            
            steps_response.append(ProcessingStepResponse(
                step_name=step.step_name,
                status="success",
                image_base64=step.image_base64,
                s3_path=s3_key_step,
                data=step.data,
                processing_time_ms=step.processing_time_ms
            ))
            
            # Save final preprocessed image for OCR
            if step.step_name == 'deskewing':
                final_preprocessed_img = ops.bytes_to_image(step.image_bytes)
            
            step_number += 1
            
        except Exception as e:
            logger.error(f"Failed to upload {s3_key_step}: {e}")
            steps_response.append(ProcessingStepResponse(
                step_name=step.step_name,
                status="error",
                error=f"S3 upload failed: {str(e)}",
                processing_time_ms=step.processing_time_ms
            ))
            break
    
    # NEW: Step 6 - OCR
    if final_preprocessed_img is not None:
        step_start = time.time()
        logger.info("Starting OCR")
        
        try:
            # Run OCR
            ocr_words, full_text = ocr_engine.extract_text_from_image(
                final_preprocessed_img,
                confidence_threshold=0.0  # Get everything, filter later
            )
            
            # Draw bounding boxes on image
            img_with_boxes = ocr_engine.draw_bounding_boxes(
                final_preprocessed_img,
                ocr_words,
                confidence_threshold=70.0
            )
            
            # Convert to base64 and bytes
            img_with_boxes_bytes = ops.image_to_bytes(img_with_boxes, format='PNG')
            img_with_boxes_base64 = ops.image_to_base64(img_with_boxes, format='PNG')
            
            # Upload visualization to S3
            s3_key_ocr = f"{processed_folder}6_ocr_visualization.png"
            await s3_service.upload_file(
                img_with_boxes_bytes,
                s3_key_ocr,
                content_type="image/png"
            )
            completed_s3_paths.append(s3_key_ocr)
            
            # Calculate statistics
            confidences = [w.confidence for w in ocr_words]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            low_conf_count = len([c for c in confidences if c < 70])
            
            # Build OCR data
            ocr_data = OCRStepData(
                total_words=len(ocr_words),
                words=[
                    OCRWordResult(
                        text=w.text,
                        confidence=w.confidence,
                        bbox=list(w.bbox)
                    )
                    for w in ocr_words
                ],
                full_text=full_text,
                avg_confidence=round(avg_confidence, 2),
                low_confidence_count=low_conf_count
            )
            
            steps_response.append(ProcessingStepResponse(
                step_name="ocr",
                status="success",
                image_base64=img_with_boxes_base64,
                s3_path=s3_key_ocr,
                data=ocr_data.model_dump(),
                processing_time_ms=int((time.time() - step_start) * 1000)
            ))
            
            logger.info(f"OCR complete: {len(ocr_words)} words, avg confidence {avg_confidence:.1f}%")
            
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            steps_response.append(ProcessingStepResponse(
                step_name="ocr",
                status="error",
                error=str(e),
                processing_time_ms=int((time.time() - step_start) * 1000)
            ))
    
    # Determine overall status
    all_successful = all(s.status == "success" for s in steps_response)
    status = "success" if all_successful else "partial_failure"
    
    total_time = int((time.time() - total_start) * 1000)
    
    return ProcessScorecardResponse(
        scorecard_id=scorecard_id,
        filename=filename,
        status=status,
        completed_steps=len([s for s in steps_response if s.status == "success"]) - 1,  # -1 for fetch
        total_steps=6,
        steps=steps_response,
        s3_paths={
            "raw": s3_key,
            "processed_folder": processed_folder,
            "completed": completed_s3_paths
        },
        total_processing_time_ms=total_time
    )