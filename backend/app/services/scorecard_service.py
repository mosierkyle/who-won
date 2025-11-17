import logging
import time
import base64
import glob
import os
from typing import List

from app.services.s3_service import s3_service
from app.processing import preprocessing_pipeline
from app.processing import ocr_engine
from app.processing import table_detection
from app.processing import image_operations as ops
from app.schemas.scorecard import (
    ProcessingStepResponse, 
    ProcessScorecardResponse,
    OCRWordResult,
    OCRStepData
)

logger = logging.getLogger(__name__)


async def upload_debug_images(scorecard_id: str, processed_folder: str) -> List[str]:
    """
    Upload debug cell images from /tmp to S3 and return presigned URLs
    
    Returns:
        List of presigned URLs for debug images
    """
    debug_files = glob.glob("/tmp/debug_*.png")
    logger.info(f"Found {len(debug_files)} debug images to upload")
    
    presigned_urls = []
    
    for debug_file in sorted(debug_files):  # Sort for consistent ordering
        try:
            filename = os.path.basename(debug_file)
            s3_key = f"{processed_folder}debug/{filename}"
            
            # Upload to S3
            with open(debug_file, 'rb') as f:
                file_bytes = f.read()
                await s3_service.upload_file(
                    file_bytes,
                    s3_key,
                    content_type="image/png"
                )
            
            # Generate presigned URL (valid for 1 hour)
            presigned_url = s3_service.generate_presigned_url(s3_key, expiration=3600)
            presigned_urls.append(presigned_url)
            
            logger.info(f"Uploaded debug image: {s3_key}")
            
            # Clean up local file
            os.remove(debug_file)
            
        except Exception as e:
            logger.warning(f"Failed to upload debug image {debug_file}: {e}")
    
    return presigned_urls


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
    
    # Step 6: Table detection
    grid = None  # Initialize grid variable
    if final_preprocessed_img is not None:
        step_start = time.time()
        logger.info("Testing table detection")
        
        try:
            # Detect table structure
            grid = table_detection.detect_table(final_preprocessed_img)
            
            if grid:
                # Draw detected grid for visualization
                grid_vis_img = table_detection.draw_detected_grid(final_preprocessed_img, grid)
                
                # Convert to base64 and bytes
                grid_vis_bytes = ops.image_to_bytes(grid_vis_img, format='PNG')
                grid_vis_base64 = ops.image_to_base64(grid_vis_img, format='PNG')
                
                # Upload visualization
                s3_key_grid = f"{processed_folder}6_table_detection.png"
                await s3_service.upload_file(
                    grid_vis_bytes,
                    s3_key_grid,
                    content_type="image/png"
                )
                completed_s3_paths.append(s3_key_grid)
                
                steps_response.append(ProcessingStepResponse(
                    step_name="table_detection",
                    status="success",
                    image_base64=grid_vis_base64,
                    s3_path=s3_key_grid,
                    data={
                        "num_rows": grid.num_rows,
                        "num_cols": grid.num_cols,
                        "total_cells": len(grid.cells)
                    },
                    processing_time_ms=int((time.time() - step_start) * 1000)
                ))
                
                logger.info(f"Table detected: {grid.num_rows}x{grid.num_cols} = {len(grid.cells)} cells")
            else:
                logger.warning("Table detection failed")
                steps_response.append(ProcessingStepResponse(
                    step_name="table_detection",
                    status="error",
                    error="Could not detect table structure",
                    processing_time_ms=int((time.time() - step_start) * 1000)
                ))
                
        except Exception as e:
            logger.error(f"Table detection failed: {e}")
            steps_response.append(ProcessingStepResponse(
                step_name="table_detection",
                status="error",
                error=str(e),
                processing_time_ms=int((time.time() - step_start) * 1000)
            ))

    # Step 7: Scorecard extraction (two-pass OCR)
    if final_preprocessed_img is not None and grid is not None:
        step_start = time.time()
        logger.info("Starting two-pass OCR extraction")
        
        try:
            # Run two-pass OCR
            scorecard_data = ocr_engine.extract_scorecard_data(
                final_preprocessed_img,
                grid.cells
            )
            
            # Upload debug images and get presigned URLs
            debug_urls = await upload_debug_images(scorecard_id, processed_folder)
            logger.info(f"Generated {len(debug_urls)} presigned URLs for debug images")
            
            # Create visualization
            vis_img = ocr_engine.draw_scorecard_results(
                final_preprocessed_img,
                grid.cells,
                scorecard_data
            )
            
            # Convert to base64 and bytes
            img_bytes = ops.image_to_bytes(vis_img, format='PNG')
            img_base64 = ops.image_to_base64(vis_img, format='PNG')
            
            # Upload visualization
            s3_key_ocr = f"{processed_folder}7_scorecard_extraction.png"
            await s3_service.upload_file(
                img_bytes,
                s3_key_ocr,
                content_type="image/png"
            )
            completed_s3_paths.append(s3_key_ocr)
            
            # Build response data with presigned URLs
            ocr_data = {
                "total_players": scorecard_data['total_players'],
                "players": scorecard_data['players'],
                "grid_size": f"{grid.num_rows}x{grid.num_cols}",
                "debug_images": debug_urls  # Presigned URLs instead of S3 keys
            }
            
            steps_response.append(ProcessingStepResponse(
                step_name="scorecard_extraction",
                status="success",
                image_base64=img_base64,
                s3_path=s3_key_ocr,
                data=ocr_data,
                processing_time_ms=int((time.time() - step_start) * 1000)
            ))
            
            logger.info(f"Scorecard extraction complete: {scorecard_data['total_players']} players found")
            
        except Exception as e:
            logger.error(f"Scorecard extraction failed: {e}")
            steps_response.append(ProcessingStepResponse(
                step_name="scorecard_extraction",
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
        total_steps=8,
        steps=steps_response,
        s3_paths={
            "raw": s3_key,
            "processed_folder": processed_folder,
            "completed": completed_s3_paths
        },
        total_processing_time_ms=total_time
    )