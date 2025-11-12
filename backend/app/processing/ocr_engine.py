import pytesseract
from PIL import Image
import numpy as np
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class OCRWord:
    """Data container for a single OCR word result"""
    def __init__(
        self,
        text: str,
        confidence: float,
        bbox: Tuple[int, int, int, int],  # (x, y, width, height)
        level: int  # Tesseract hierarchy level (5 = word)
    ):
        self.text = text
        self.confidence = confidence
        self.bbox = bbox
        self.level = level

def extract_text_from_image(
    img: np.ndarray,
    confidence_threshold: float = 0.0
) -> Tuple[List[OCRWord], str]:
    """
    Extract text from an image using Tesseract OCR
    
    Args:
        img: OpenCV image (numpy array)
        confidence_threshold: Minimum confidence to include (0-100)
    
    Returns:
        (list of OCRWord objects, full text string)
    

    """
    logger.info("Running Tesseract OCR")
    
    # Convert OpenCV (BGR) to PIL (RGB) format
    if len(img.shape) == 2:
        # Grayscale
        pil_img = Image.fromarray(img)
    else:
        # Color - OpenCV uses BGR, PIL uses RGB
        pil_img = Image.fromarray(img)
    
    # Get detailed OCR data
    # Output is a dict with keys: level, page_num, block_num, line_num, word_num,
    # left, top, width, height, conf, text
    ocr_data = pytesseract.image_to_data(
        pil_img,
        output_type=pytesseract.Output.DICT,
        config='--psm 6'  # PSM 6 = Assume a single uniform block of text
    )
    
    # Parse results into OCRWord objects
    words = []
    n_boxes = len(ocr_data['text'])
    
    for i in range(n_boxes):
        text = ocr_data['text'][i].strip()
        conf = float(ocr_data['conf'][i])
        
        # Skip empty text or low confidence
        if not text or conf < confidence_threshold:
            continue
        
        # Extract bounding box
        x = ocr_data['left'][i]
        y = ocr_data['top'][i]
        w = ocr_data['width'][i]
        h = ocr_data['height'][i]
        
        words.append(OCRWord(
            text=text,
            confidence=conf,
            bbox=(x, y, w, h),
            level=ocr_data['level'][i]
        ))
    
    # Get full text (simple string output)
    full_text = pytesseract.image_to_string(pil_img, config='--psm 6')
    
    logger.info(f"OCR extracted {len(words)} words")
    return words, full_text.strip()

def draw_bounding_boxes(
    img: np.ndarray,
    words: List[OCRWord],
    confidence_threshold: float = 70.0
) -> np.ndarray:
    """
    Draw bounding boxes on image to visualize OCR results
    
    Args:
        img: OpenCV image
        words: List of OCRWord objects
        confidence_threshold: Flag boxes below this confidence in red
    
    Returns:
        Image with bounding boxes drawn
    
    Color coding:
    - Green: High confidence (>= threshold)
    - Red: Low confidence (< threshold)
    """
    import cv2
    
    # Make a copy so we don't modify original
    img_with_boxes = img.copy()
    
    # Convert grayscale to BGR for colored boxes
    if len(img_with_boxes.shape) == 2:
        img_with_boxes = cv2.cvtColor(img_with_boxes, cv2.COLOR_GRAY2BGR)
    
    for word in words:
        x, y, w, h = word.bbox
        
        # Color based on confidence
        color = (0, 255, 0) if word.confidence >= confidence_threshold else (0, 0, 255)
        
        # Draw rectangle
        cv2.rectangle(img_with_boxes, (x, y), (x + w, y + h), color, 2)
        
        # Add confidence score label
        label = f"{word.confidence:.0f}%"
        cv2.putText(
            img_with_boxes,
            label,
            (x, y - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            color,
            1
        )
    
    return img_with_boxes