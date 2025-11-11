import logging
import time
from typing import List, Optional, Tuple
from . import image_operations as ops

logger = logging.getLogger(__name__)

class PreprocessingStep:
    """Data container for a single preprocessing step result"""
    def __init__(
        self, 
        step_name: str, 
        status: str,
        image_bytes: Optional[bytes] = None,
        image_base64: Optional[str] = None,
        data: Optional[dict] = None,
        processing_time_ms: int = 0,
        error: Optional[str] = None
    ):
        self.step_name = step_name
        self.status = status
        self.image_bytes = image_bytes
        self.image_base64 = image_base64
        self.data = data or {}
        self.processing_time_ms = processing_time_ms
        self.error = error

def run_pipeline(
    image_bytes: bytes, 
    include_base64: bool = True
) -> Tuple[List[PreprocessingStep], Optional[bytes]]:
    """
    Run full preprocessing pipeline
    
    Args:
        image_bytes: Raw image data
        include_base64: Whether to include base64 encoded images in results
    
    Returns:
        (list of step results, final image bytes or None if failed)
    """
    steps = []
    
    try:
        # Convert bytes to OpenCV format
        img = ops.bytes_to_image(image_bytes)
        logger.info(f"Original image shape: {img.shape}")
        
        # Step 1: Grayscale conversion
        start = time.time()
        img, data = ops.grayscale(img)
        img_bytes = ops.image_to_bytes(img)
        img_base64 = ops.image_to_base64(img) if include_base64 else None
        
        steps.append(PreprocessingStep(
            step_name="grayscale",
            status="success",
            image_bytes=img_bytes,
            image_base64=img_base64,
            data=data,
            processing_time_ms=int((time.time() - start) * 1000)
        ))
        
        # Step 2: Contrast enhancement
        start = time.time()
        img, data = ops.enhance_contrast(img)
        img_bytes = ops.image_to_bytes(img)
        img_base64 = ops.image_to_base64(img) if include_base64 else None
        
        steps.append(PreprocessingStep(
            step_name="contrast_enhancement",
            status="success",
            image_bytes=img_bytes,
            image_base64=img_base64,
            data=data,
            processing_time_ms=int((time.time() - start) * 1000)
        ))
        
        # Step 3: Denoising
        start = time.time()
        img, data = ops.denoise(img)
        img_bytes = ops.image_to_bytes(img)
        img_base64 = ops.image_to_base64(img) if include_base64 else None
        
        steps.append(PreprocessingStep(
            step_name="denoising",
            status="success",
            image_bytes=img_bytes,
            image_base64=img_base64,
            data=data,
            processing_time_ms=int((time.time() - start) * 1000)
        ))
        
        # Step 4: Binarization
        start = time.time()
        img, data = ops.binarize(img)
        img_bytes = ops.image_to_bytes(img)
        img_base64 = ops.image_to_base64(img) if include_base64 else None
        
        steps.append(PreprocessingStep(
            step_name="binarization",
            status="success",
            image_bytes=img_bytes,
            image_base64=img_base64,
            data=data,
            processing_time_ms=int((time.time() - start) * 1000)
        ))
        
        # Step 5: Deskewing (save as PNG for final OCR input)
        start = time.time()
        img, data = ops.deskew(img)
        img_bytes = ops.image_to_bytes(img, format='PNG')
        img_base64 = ops.image_to_base64(img, format='PNG') if include_base64 else None
        
        steps.append(PreprocessingStep(
            step_name="deskewing",
            status="success",
            image_bytes=img_bytes,
            image_base64=img_base64,
            data=data,
            processing_time_ms=int((time.time() - start) * 1000)
        ))
        
        logger.info(f"Pipeline completed successfully with {len(steps)} steps")
        return steps, img_bytes
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        steps.append(PreprocessingStep(
            step_name=f"failed_at_step_{len(steps) + 1}",
            status="error",
            error=str(e),
            processing_time_ms=0
        ))
        return steps, None