import cv2
import numpy as np
import base64
from typing import Tuple, Dict
import logging
import pytesseract

logger = logging.getLogger(__name__)


def bytes_to_image(image_bytes: bytes) -> np.ndarray:
    """Convert image bytes to OpenCV format (numpy array)"""
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Failed to decode image")
    return img

def image_to_bytes(img: np.ndarray, format: str = 'JPEG') -> bytes:
    """Convert OpenCV image back to bytes"""
    is_success, buffer = cv2.imencode(f'.{format.lower()}', img)
    if not is_success:
        raise ValueError(f"Failed to encode image as {format}")
    return buffer.tobytes()

def image_to_base64(img: np.ndarray, format: str = 'JPEG') -> str:
    """
    Convert OpenCV image to base64 string for JSON transmission
    Base64 = Binary data encoded as text (so we can send images in JSON)
    """
    img_bytes = image_to_bytes(img, format)
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    return f"data:image/{format.lower()};base64,{img_base64}"

def grayscale(img: np.ndarray) -> Tuple[np.ndarray, Dict]:
    """
    Convert to grayscale
    Why: OCR doesn't need color, grayscale reduces data and improves accuracy
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    data = {
        "original_channels": img.shape[2] if len(img.shape) == 3 else 1,
        "output_channels": 1
    }
    return gray, data

def enhance_contrast(img: np.ndarray) -> Tuple[np.ndarray, Dict]:
    """
    Enhance contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization)
    Why: Makes faint handwriting more visible by enhancing local contrast
    Works on 8x8 tiles to handle varying lighting across the scorecard
    """
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(img)
    data = {
        "method": "CLAHE",
        "clip_limit": 2.0,
        "tile_grid_size": [8, 8]
    }
    return enhanced, data

def denoise(img: np.ndarray) -> Tuple[np.ndarray, Dict]:
    """
    Remove noise while preserving edges using bilateral filter
    Better for handwritten scorecards than fastNlMeans
    """
    # CHANGED: Bilateral filter preserves edges better for handwriting
    denoised = cv2.bilateralFilter(img, d=9, sigmaColor=75, sigmaSpace=75)
    data = {
        "method": "bilateralFilter",
        "d": 9,
        "sigmaColor": 75,
        "sigmaSpace": 75
    }
    return denoised, data

def binarize(img: np.ndarray) -> Tuple[np.ndarray, Dict]:
    """
    Convert to pure black and white
    Why: OCR works best on high contrast binary images
    Adaptive thresholding: Different threshold for different regions (handles shadows)
    """
    binary = cv2.adaptiveThreshold(
        img,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2
    )
    data = {
        "method": "adaptive_threshold",
        "block_size": 11,
        "constant": 2
    }
    return binary, data

def auto_rotate(img: np.ndarray) -> Tuple[np.ndarray, Dict]:
    """
    Auto-rotate using OSD on the top 20% of the image (header region).
    
    Scorecard headers usually have clear text (Player, Hole, Par, etc.)
    which OSD can detect reliably. The rest of the scorecard is mostly
    numbers and grid lines which confuse OSD.
    """
    import pytesseract
    from PIL import Image
    import time
    
    start = time.time()
    logger.info("Auto-rotation: Using OSD on header region")
    
    # Crop top 20% of image (where header text usually is)
    height, width = img.shape[:2]
    crop_height = int(height * 0.2)
    header_region = img[0:crop_height, :]
    
    logger.info(f"Cropped header region: {header_region.shape}")
    
    # Convert to PIL for Tesseract
    if len(header_region.shape) == 2:
        pil_img = Image.fromarray(header_region)
    else:
        pil_img = Image.fromarray(cv2.cvtColor(header_region, cv2.COLOR_BGR2RGB))
    
    try:
        # Run OSD on just the header
        osd = pytesseract.image_to_osd(pil_img, output_type=pytesseract.Output.DICT)
        detected_rotation = osd['rotate']
        confidence = osd['orientation_conf']
        
        logger.info(f"OSD on header: {detected_rotation}° (confidence: {confidence:.1f}%)")
        
        # Apply rotation if detected
        if detected_rotation == 0:
            logger.info("Image already correctly oriented")
            elapsed = time.time() - start
            return img, {
                "rotation_applied": 0,
                "detected_rotation": 0,
                "confidence": float(confidence),
                "method": "osd_header_crop",
                "skipped": True,
                "reason": "already_correct",
                "processing_time_ms": int(elapsed * 1000)
            }
        
        # Rotate full image
        logger.info(f"Rotating full image by {detected_rotation}°")
        
        if detected_rotation == 90:
            rotated = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
        elif detected_rotation == 180:
            rotated = cv2.rotate(img, cv2.ROTATE_180)
        elif detected_rotation == 270:
            rotated = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
        else:
            rotated = img
        
        elapsed = time.time() - start
        logger.info(f"Auto-rotation completed in {elapsed*1000:.0f}ms")
        
        return rotated, {
            "rotation_applied": int(detected_rotation),
            "detected_rotation": int(detected_rotation),
            "confidence": float(confidence),
            "method": "osd_header_crop",
            "skipped": False,
            "processing_time_ms": int(elapsed * 1000)
        }
        
    except Exception as e:
        logger.error(f"OSD on header failed: {e}")
        # Fallback to simple aspect ratio check
        return _aspect_ratio_fallback(img)


def _aspect_ratio_fallback(img: np.ndarray) -> Tuple[np.ndarray, Dict]:
    """
    Simple fallback: If image is landscape, rotate to portrait.
    Most scorecards are portrait orientation.
    """
    height, width = img.shape[:2]
    
    if width > height:
        logger.info(f"Fallback: Image is landscape ({width}x{height}), rotating 90° to portrait")
        rotated = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
        return rotated, {
            "rotation_applied": 90,
            "method": "aspect_ratio_fallback",
            "skipped": False,
            "reason": "landscape_to_portrait"
        }
    else:
        logger.info(f"Fallback: Image already portrait ({width}x{height})")
        return img, {
            "rotation_applied": 0,
            "method": "aspect_ratio_fallback",
            "skipped": True,
            "reason": "already_portrait"
        }
    
def deskew(img: np.ndarray) -> Tuple[np.ndarray, Dict]:
    """
    Detect and correct image rotation using projection profile analysis.
    
    How it works:
    1. Try different rotation angles (-10° to +10°)
    2. For each angle, calculate the "sharpness" of horizontal text lines
    3. The angle with sharpest lines is the correct orientation
    4. Rotate the image to that angle
    
    This is more robust than Hough line detection because it works even
    with complex layouts (tables, logos, etc.)
    """
    import time
    start = time.time()
    
    logger.info("Starting projection profile deskewing")
    
    # Calculate the best rotation angle
    best_angle = _find_best_rotation_angle(img)
    
    # Only rotate if angle is significant
    if abs(best_angle) < 0.5:
        logger.info(f"Angle too small ({best_angle:.2f}°), skipping rotation")
        return img, {
            "rotation_angle": float(best_angle),
            "skipped": True,
            "reason": f"angle_too_small ({best_angle:.2f}°)",
            "method": "projection_profile"
        }
    
    # Rotate the image
    logger.info(f"Rotating image by {best_angle:.2f}°")
    (h, w) = img.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, best_angle, 1.0)
    rotated = cv2.warpAffine(
        img,
        M,
        (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )
    
    elapsed = time.time() - start
    logger.info(f"Deskewing completed in {elapsed*1000:.0f}ms")
    
    return rotated, {
        "rotation_angle": float(best_angle),
        "skipped": False,
        "method": "projection_profile",
        "processing_time_ms": int(elapsed * 1000)
    }


def _find_best_rotation_angle(img: np.ndarray, angle_range: int = 10, angle_step: float = 0.25) -> float:
    """
    Find the rotation angle that maximizes projection profile variance.
    
    Args:
        img: Grayscale or binary image
        angle_range: Range of angles to test (+/- degrees)
        angle_step: Step size for angle testing (smaller = more precise but slower)
    
    Returns:
        Best rotation angle in degrees
    
    How it works:
    - Tests angles from -angle_range to +angle_range
    - For each angle, calculates horizontal projection variance
    - Returns the angle with maximum variance (sharpest text lines)
    """
    import time
    start = time.time()
    
    # Ensure grayscale
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Get image dimensions
    (h, w) = img.shape
    center = (w // 2, h // 2)
    
    # Test different angles
    angles = np.arange(-angle_range, angle_range + angle_step, angle_step)
    variances = []
    
    logger.info(f"Testing {len(angles)} angles from {-angle_range}° to {+angle_range}°")
    
    for angle in angles:
        # Rotate image
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR)
        
        # Calculate horizontal projection profile variance
        variance = _calculate_projection_variance(rotated)
        variances.append(variance)
    
    # Find angle with maximum variance (sharpest profile)
    best_idx = np.argmax(variances)
    best_angle = float(angles[best_idx])
    best_variance = variances[best_idx]
    
    elapsed = time.time() - start
    logger.info(f"Best angle: {best_angle:.2f}° (variance: {best_variance:.2f}) in {elapsed*1000:.0f}ms")
    
    return best_angle


def _calculate_projection_variance(img: np.ndarray) -> float:
    """
    Calculate the variance of the horizontal projection profile.
    
    Args:
        img: Grayscale image
    
    Returns:
        Variance value (higher = sharper text lines)
    
    How it works:
    1. Sum each row of pixels (horizontal projection)
    2. Calculate variance of these sums
    3. High variance = clear distinction between text rows and white space
    4. Low variance = blurry, rotated text
    
    Example:
    Straight document: [255, 255, 10, 10, 255, 255] → High variance
    Tilted document:   [150, 140, 130, 125, 140, 150] → Low variance
    """
    # Sum each row (horizontal projection)
    # This gives us a 1D array where each value = total "darkness" of that row
    projection = np.sum(img, axis=1, dtype=np.float64)
    
    # Normalize by image width (so different sized images are comparable)
    projection = projection / img.shape[1]
    
    # Calculate variance
    # variance = how spread out the values are
    # High variance = some rows very dark (text), some very light (whitespace)
    variance = float(np.var(projection))
    
    return variance