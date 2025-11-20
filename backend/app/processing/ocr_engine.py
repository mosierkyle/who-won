import pytesseract
from PIL import Image
import numpy as np
from typing import List, Dict, Optional
import logging
import cv2

logger = logging.getLogger(__name__)


# ==================== PASS 1: ROW DETECTION ====================

def detect_player_rows(img: np.ndarray, cells: List) -> Dict[str, List[int]]:
    """PASS 1: Find player name rows by OCR-ing leftmost wide columns"""
    logger.info("=" * 60)
    logger.info("PASS 1: Scanning for player rows")
    logger.info("=" * 60)
    
    # Find wide cells in leftmost columns (likely name columns)
    wide_cells = [c for c in cells if c.col in [0, 1, 2, 3] and c.width > 80]
    logger.info(f"Found {len(wide_cells)} wide cells (width > 80px) in columns 0-3")
    
    # Keep only leftmost wide cell per row
    rows_dict = {}
    for cell in wide_cells:
        if cell.row not in rows_dict or cell.col < rows_dict[cell.row].col:
            rows_dict[cell.row] = cell
    
    player_rows = []
    player_names = []
    
    logger.info(f"Checking {len(rows_dict)} rows for player names...")
    
    for cell in sorted(rows_dict.values(), key=lambda c: c.row):
        logger.info(f"\n{'='*40}")
        logger.info(f"Row {cell.row}, Col {cell.col}, Cell size: {cell.width}x{cell.height}px")
        
        # Extract with 15% inflation
        cell_img = extract_cell_inflated(img, cell, inflation=0.15)
        logger.info(f"After inflation: {cell_img.shape[1]}x{cell_img.shape[0]}px")
        
        # Save BEFORE preprocessing
        save_debug_image(cell_img, f"name_row{cell.row}_1_RAW")
        
        # Preprocess
        cell_img_processed = preprocess_name_cell(cell_img)
        logger.info(f"After preprocessing: {cell_img_processed.shape[1]}x{cell_img_processed.shape[0]}px")
        
        # Save AFTER preprocessing
        save_debug_image(cell_img_processed, f"name_row{cell.row}_2_PROCESSED")
        
        # OCR
        text = ocr_cell(cell_img_processed, mode='name')
        logger.info(f"OCR result: '{text}'")
        
        if is_player_name(text, cell.row):
            player_rows.append(cell.row)
            player_names.append(text)
            logger.info(f"✅ VALID PLAYER")
        else:
            logger.info(f"❌ REJECTED")
    
    logger.info("\n" + "=" * 60)
    logger.info(f"PASS 1 COMPLETE: Found {len(player_rows)} players")
    for i, (row, name) in enumerate(zip(player_rows, player_names)):
        logger.info(f"  Player {i+1}: Row {row} - '{name}'")
    logger.info("=" * 60)
    
    return {'player_rows': player_rows, 'player_names': player_names}


def is_player_name(text: str, row_index: int) -> bool:
    """Validate if text is likely a player name"""
    if not text or len(text) < 2:
        logger.info(f"  Reason: Too short or None")
        return False
    
    # Skip header/footer rows
    if row_index < 5 or row_index > 15:
        logger.info(f"  Reason: Header/footer row")
        return False
    
    text_clean = text.strip().lower()
    
    # Banned golf keywords
    banned_keywords = {
        'handicap', 'hcp', 'hdcp', 'slope', 'rating', 'par',
        'blue', 'white', 'green', 'red', 'gold', 'black',
        'yards', 'yardage', 'tee', 'tees', 'hole', 'total',
        'front', 'back', 'in', 'out', 'gross', 'net', 'score',
        'team', 'date', 'scorer', 'attest', 'initials'
    }
    
    # Check for banned words
    words = text_clean.split()
    if any(word in banned_keywords for word in words):
        logger.info(f"  Reason: Contains banned keyword")
        return False
    
    # Must have letters
    letter_count = sum(c.isalpha() for c in text)
    if letter_count < 2:
        logger.info(f"  Reason: Too few letters")
        return False
    
    # Too long?
    if len(text) > 25:
        logger.info(f"  Reason: Too long")
        return False
    
    # Too many words? (names are 1-3 words)
    if len(words) > 3:
        logger.info(f"  Reason: Too many words")
        return False
    
    # Reject if mostly digits
    digit_count = sum(c.isdigit() for c in text)
    if digit_count > letter_count:
        logger.info(f"  Reason: More digits than letters")
        return False
    
    # Reject rare symbols (including | and _ from grid lines)
    rare_chars = '@©#$%^&*=+[]{}|\\<>_'
    if any(c in text for c in rare_chars):
        logger.info(f"  Reason: Contains rare symbols")
        return False
    
    return True


# ==================== PASS 2: FULL ROW EXTRACTION ====================

def extract_player_rows(img: np.ndarray, cells: List, player_rows: List[int]) -> List[Dict]:
    """PASS 2: Extract all cells in player rows with advanced preprocessing"""
    logger.info("=" * 60)
    logger.info(f"PASS 2: Extracting {len(player_rows)} player rows")
    logger.info("=" * 60)
    
    max_col = max(cell.col for cell in cells)
    player_data = []
    
    for player_row in player_rows:
        logger.info(f"Processing row {player_row}...")
        row_values = []
        
        for col in range(max_col + 1):
            cell = find_cell(cells, player_row, col)
            if not cell:
                row_values.append(None)
                continue
            
            # Extract with 20% inflation
            cell_img_raw = extract_cell_inflated(img, cell, inflation=0.20)
            cell_img_processed = preprocess_score_cell(cell_img_raw)
            
            # Save debug for first 12 columns
            if col < 12:
                save_debug_image(cell_img_raw, f"row{player_row}_col{col:02d}_raw")
                save_debug_image(cell_img_processed, f"row{player_row}_col{col:02d}_processed")
            
            # OCR
            cell_text = ocr_cell(cell_img_processed, mode='score')
            row_values.append(cell_text)
        
        non_empty = sum(1 for v in row_values if v)
        logger.info(f"  Extracted {non_empty}/{len(row_values)} non-empty cells")
        
        player_data.append({'row': player_row, 'all_values': row_values})
    
    logger.info("=" * 60)
    logger.info(f"PASS 2 COMPLETE")
    logger.info("=" * 60)
    
    return player_data


# ==================== CELL EXTRACTION ====================

def extract_cell_inflated(img: np.ndarray, cell, inflation: float = 0.20) -> np.ndarray:
    """Extract cell with percentage-based padding (inflation)"""
    inflate_x = int(cell.width * inflation)
    inflate_y = int(cell.height * inflation)
    
    x1 = max(0, cell.x - inflate_x)
    y1 = max(0, cell.y - inflate_y)
    x2 = min(img.shape[1], cell.x + cell.width + inflate_x)
    y2 = min(img.shape[0], cell.y + cell.height + inflate_y)
    
    return img[y1:y2, x1:x2]


# ==================== PREPROCESSING ====================

def preprocess_name_cell(cell_img: np.ndarray) -> np.ndarray:
    """
    Balanced preprocessing for name cells
    - Remove borders without destroying text
    """
    gray = to_grayscale(cell_img)
    
    # Step 1: CLAHE enhancement
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    
    # Step 2: Adaptive threshold (gentler)
    binary = cv2.adaptiveThreshold(
        enhanced, 255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        blockSize=15,  # Larger block = less aggressive
        C=3
    )
    
    # Step 3: Remove border strips (moderate)
    binary = remove_border_strips(binary, strip_width=5, threshold=0.6)
    
    # Step 4: Remove ONLY very strong grid lines
    binary = remove_strong_grid_lines(binary)
    
    # Step 5: Small noise removal
    kernel = np.ones((2, 2), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
    
    # Invert back for OCR
    return cv2.bitwise_not(binary)


def remove_strong_grid_lines(binary: np.ndarray) -> np.ndarray:
    """
    Remove ONLY very strong continuous lines (grid borders)
    More selective - only removes lines spanning 70%+ of image
    """
    h, w = binary.shape
    
    # Only process if image is large enough
    if h < 30 or w < 30:
        return binary
    
    # Detect horizontal lines (must span at least 70% of width)
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (int(w * 0.7), 1))
    horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel, iterations=1)
    
    # Detect vertical lines (must span at least 70% of height)
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, int(h * 0.7)))
    vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel, iterations=1)
    
    # Only remove detected lines
    lines = cv2.add(horizontal_lines, vertical_lines)
    result = cv2.subtract(binary, lines)
    
    return result


def preprocess_score_cell(cell_img: np.ndarray) -> np.ndarray:
    """
    Advanced preprocessing for score cells:
    1. Adaptive threshold
    2. Find largest connected component (the digit)
    3. Remove borders
    4. Resize to 64x64 with padding
    """
    gray = to_grayscale(cell_img)
    
    # Adaptive threshold (inverted: white ink on black)
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, 11, 2)
    
    # Find largest connected component
    binary = extract_largest_component(binary, margin=5)
    
    # Remove border strips
    binary = remove_border_strips(binary, strip_width=3, threshold=0.7)
    
    # Resize to 64x64 with aspect preservation
    binary = resize_with_padding(binary, target_size=64)
    
    # Invert back
    return cv2.bitwise_not(binary)


def extract_largest_component(binary: np.ndarray, margin: int = 5) -> np.ndarray:
    """Find largest connected component and crop to its bbox"""
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    
    if num_labels <= 1:  # Only background
        return binary
    
    # Find largest component (excluding background)
    areas = stats[1:, cv2.CC_STAT_AREA]
    largest_idx = np.argmax(areas) + 1
    
    # Get bbox
    x = stats[largest_idx, cv2.CC_STAT_LEFT]
    y = stats[largest_idx, cv2.CC_STAT_TOP]
    w = stats[largest_idx, cv2.CC_STAT_WIDTH]
    h = stats[largest_idx, cv2.CC_STAT_HEIGHT]
    
    # Add margin
    x = max(0, x - margin)
    y = max(0, y - margin)
    w = min(binary.shape[1] - x, w + 2 * margin)
    h = min(binary.shape[0] - y, h + 2 * margin)
    
    return binary[y:y+h, x:x+w]


def remove_border_strips(binary: np.ndarray, strip_width: int = 3, 
                        threshold: float = 0.7) -> np.ndarray:
    """Remove edge strips if they're mostly white (cell borders)"""
    h, w = binary.shape
    
    if h <= strip_width * 2 or w <= strip_width * 2:
        return binary
    
    result = binary.copy()
    
    # Check and remove each edge if it's a border
    edges = [
        (result[:strip_width, :], slice(None, strip_width), slice(None)),  # Top
        (result[-strip_width:, :], slice(-strip_width, None), slice(None)),  # Bottom
        (result[:, :strip_width], slice(None), slice(None, strip_width)),  # Left
        (result[:, -strip_width:], slice(None), slice(-strip_width, None))  # Right
    ]
    
    for strip, *slices in edges:
        if np.mean(strip) / 255 > threshold:
            result[slices[0], slices[1]] = 0
    
    return result


def resize_with_padding(binary: np.ndarray, target_size: int = 64) -> np.ndarray:
    """Resize to target_size x target_size with aspect preservation"""
    h, w = binary.shape
    
    if h == 0 or w == 0:
        return np.zeros((target_size, target_size), dtype=np.uint8)
    
    # Scale to target height
    scale = target_size / h
    new_w = int(w * scale)
    new_h = target_size
    
    resized = cv2.resize(binary, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
    
    # Pad width to square
    if new_w < target_size:
        pad_left = (target_size - new_w) // 2
        pad_right = target_size - new_w - pad_left
        resized = cv2.copyMakeBorder(resized, 0, 0, pad_left, pad_right, 
                                     cv2.BORDER_CONSTANT, value=0)
    elif new_w > target_size:
        start = (new_w - target_size) // 2
        resized = resized[:, start:start+target_size]
    
    return resized


# ==================== OCR ====================

def ocr_cell(cell_img: np.ndarray, mode: str = 'score') -> Optional[str]:
    """Run OCR on preprocessed cell"""
    pil_img = Image.fromarray(cell_img)
    
    try:
        if mode == 'score':
            # PSM 10 (single character) for digits
            config = '--psm 10 -c tessedit_char_whitelist=0123456789()'
            text = pytesseract.image_to_string(pil_img, config=config).strip()
            text = ''.join(c for c in text if c.isdigit() or c in '()')
        else:  # name
            # PSM 7 (single line) for names
            config = '--psm 7'
            text = pytesseract.image_to_string(pil_img, config=config).strip()
        
        return text if text else None
    except Exception as e:
        logger.warning(f"OCR failed: {e}")
        return None


# ==================== VISUALIZATION ====================

def draw_scorecard_results(img: np.ndarray, cells: List, scorecard_data: Dict) -> np.ndarray:
    """Draw visualization with color-coded cells"""
    vis_img = img.copy() if len(img.shape) == 3 else cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    
    for player in scorecard_data['players']:
        row = player['row']
        name = player['name']
        all_values = player['all_values']
        
        # Draw name cell in blue
        name_cell = next((find_cell(cells, row, col) for col in [0, 1, 2, 3] 
                         if find_cell(cells, row, col) and find_cell(cells, row, col).width > 80), None)
        
        if name_cell:
            cv2.rectangle(vis_img, (name_cell.x, name_cell.y),
                         (name_cell.x + name_cell.width, name_cell.y + name_cell.height),
                         (255, 0, 0), 2)
            cv2.putText(vis_img, name, (name_cell.x + 5, name_cell.y + 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        
        # Draw score cells: green = has value, red = empty
        for col_idx, value in enumerate(all_values):
            cell = find_cell(cells, row, col_idx)
            if not cell:
                continue
            
            color = (0, 255, 0) if value else (0, 0, 255)
            thickness = 2 if value else 1
            
            cv2.rectangle(vis_img, (cell.x, cell.y),
                         (cell.x + cell.width, cell.y + cell.height), color, thickness)
            
            if value:
                cv2.putText(vis_img, str(value)[:6], (cell.x + 5, cell.y + cell.height - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
    
    return vis_img


# ==================== UTILITIES ====================

def to_grayscale(img: np.ndarray) -> np.ndarray:
    """Convert to grayscale if needed"""
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img.copy()


def find_cell(cells: List, row: int, col: int):
    """Find cell by row/col index"""
    return next((c for c in cells if c.row == row and c.col == col), None)


def save_debug_image(img: np.ndarray, name: str):
    """Save debug image to /tmp"""
    try:
        cv2.imwrite(f"/tmp/debug_{name}.png", img)
    except Exception as e:
        pass  # Silently fail on debug image saves


# ==================== MAIN ENTRY POINT ====================

def extract_scorecard_data(img: np.ndarray, cells: List) -> Dict:
    """Main function: Two-pass OCR to extract scorecard data"""
    # PASS 1: Detect player rows
    detection = detect_player_rows(img, cells)
    player_rows = detection['player_rows']
    player_names = detection['player_names']
    
    # PASS 2: Extract full rows
    player_data = extract_player_rows(img, cells, player_rows)
    
    # Combine
    players = [
        {
            'row': data['row'],
            'name': player_names[i] if i < len(player_names) else 'Unknown',
            'all_values': data['all_values']
        }
        for i, data in enumerate(player_data)
    ]
    
    return {'players': players, 'total_players': len(players)}