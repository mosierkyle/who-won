import cv2
import numpy as np
import base64
from typing import Tuple, Dict

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
    Remove noise while preserving edges
    Why: Camera noise and scanning artifacts confuse OCR
    Algorithm: Finds similar pixels nearby and averages them
    """
    denoised = cv2.fastNlMeansDenoising(
        img, 
        None, 
        h=10,
        templateWindowSize=7,
        searchWindowSize=21
    )
    data = {
        "method": "fastNlMeansDenoising",
        "h_parameter": 10
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

def deskew(img: np.ndarray) -> Tuple[np.ndarray, Dict]:
    """
    Detect and correct image rotation
    Why: Even slight rotation (5°) can hurt OCR accuracy
    How: 
    1. Find edges using Canny
    2. Detect lines using Hough transform
    3. Calculate median angle of all lines
    4. Rotate image to straighten
    """
    # Detect edges
    edges = cv2.Canny(img, 50, 150, apertureSize=3)
    
    # Detect lines
    lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)
    
    if lines is None:
        return img, {"rotation_angle": 0, "skipped": True}
    
    # Calculate angles of detected lines
    angles = []
    for rho, theta in lines[:, 0]:
        angle = np.degrees(theta) - 90
        angles.append(angle)
    
    # Use median angle (robust to outliers)
    median_angle = np.median(angles)
    
    # Only rotate if angle is significant
    if abs(median_angle) < 0.5:
        return img, {"rotation_angle": median_angle, "skipped": True}
    
    # Rotate image
    (h, w) = img.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
    rotated = cv2.warpAffine(
        img, 
        M, 
        (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )
    
    data = {
        "rotation_angle": float(median_angle),
        "lines_detected": len(lines),
        "skipped": False
    }
    return rotated, data