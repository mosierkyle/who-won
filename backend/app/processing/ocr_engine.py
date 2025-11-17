import pytesseract
from PIL import Image
import numpy as np
from typing import List, Dict, Tuple, Optional
import logging
import cv2

logger = logging.getLogger(__name__)


# ==================== PASS 1: ROW DETECTION ====================

def detect_player_rows(img: np.ndarray, cells: List) -> Dict[str, List[int]]:
    """
    PASS 1: Quick OCR scan of leftmost WIDE columns to find player name rows
    """
    logger.info("=" * 60)
    logger.info("PASS 1: Scanning leftmost columns to detect player rows")
    logger.info("=" * 60)
    
    # Check columns 0-3 (in case there's an extra column on left)
    leftmost_cells = [cell for cell in cells if cell.col in [0, 1, 2, 3]]
    
    # Filter to only WIDE cells (likely name columns)
    wide_cells = [cell for cell in leftmost_cells if cell.width > 80]
    
    logger.info(f"Found {len(wide_cells)} wide cells (width > 80px) to check for player names")
    
    # Group by row, prioritize leftmost wide column in each row
    rows_dict = {}
    for cell in wide_cells:
        if cell.row not in rows_dict or cell.col < rows_dict[cell.row].col:
            rows_dict[cell.row] = cell
    
    # Sort by row
    sorted_cells = sorted(rows_dict.values(), key=lambda c: c.row)
    
    player_rows = []
    player_names = []
    
    logger.info(f"Checking {len(sorted_cells)} rows for player names...")
    logger.info("-" * 60)
    
    for cell in sorted_cells:
        # Extract cell image
        cell_img = extract_cell_image(img, cell, padding=2)
        
        logger.info(f"Row {cell.row}, Col {cell.col}: size={cell_img.shape}, cell_width={cell.width}px")
        
        # Quick check: does this cell have content?
        has_content = has_meaningful_content(cell_img)
        logger.info(f"  Has content: {has_content}")
        
        if not has_content:
            logger.info(f"  ❌ Skipped (no meaningful content)")
            logger.info("-" * 60)
            continue
        
        # Preprocess for name OCR
        cell_img_processed = preprocess_name_cell(cell_img)
        
        # OCR the cell (looking for player names)
        text = ocr_text_cell(cell_img_processed, mode='name')
        logger.info(f"  OCR Result: '{text}'")
        
        # Filter: is this a player name?
        is_player = is_player_name(text, cell.row)
        logger.info(f"  Is player name: {is_player}")
        
        if is_player:
            player_rows.append(cell.row)
            player_names.append(text)
            logger.info(f"  ✅ PLAYER FOUND: '{text}' at row {cell.row}")
        else:
            logger.info(f"  ❌ Not a player name")
        
        logger.info("-" * 60)
    
    logger.info("=" * 60)
    logger.info(f"PASS 1 COMPLETE: Found {len(player_rows)} players")
    for i, (row, name) in enumerate(zip(player_rows, player_names)):
        logger.info(f"  Player {i+1}: Row {row} - '{name}'")
    logger.info("=" * 60)
    
    return {
        'player_rows': player_rows,
        'player_names': player_names
    }


def has_meaningful_content(cell_img: np.ndarray, min_ratio: float = 0.03) -> bool:
    """Quick check: does cell have any content worth OCR?"""
    if cell_img.shape[0] < 15 or cell_img.shape[1] < 15:
        return False
    
    # Convert to grayscale
    if len(cell_img.shape) == 3:
        gray = cv2.cvtColor(cell_img, cv2.COLOR_BGR2GRAY)
    else:
        gray = cell_img
    
    # Check dark pixel ratio
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    dark_pixels = np.sum(binary < 128)
    content_ratio = dark_pixels / binary.size
    
    logger.info(f"  Content ratio: {content_ratio:.2%}")
    
    return min_ratio < content_ratio < 0.7


def is_player_name(text: str, row_index: int) -> bool:
    """
    Determine if OCR result is likely a player name
    """
    if not text or len(text) < 2:
        logger.info(f"    Reason: Text too short ('{text}')")
        return False
    
    # Skip header rows
    if row_index < 5:
        logger.info(f"    Reason: Header row (row {row_index} < 5)")
        return False
    
    text_clean = text.strip().lower()
    
    # Skip keywords
    skip_keywords = [
        'handicap', 'par', 'green', 'blue', 'white', 'gold', 'red',
        'team', 'hole', 'date', 'scorer', 'attest', 'rating', 'slope',
        'out', 'in', 'tot', 'hcp', 'net', 'initials'
    ]
    
    for keyword in skip_keywords:
        if keyword == text_clean or keyword in text_clean:
            logger.info(f"    Reason: Contains skip keyword '{keyword}'")
            return False
    
    # Must contain at least ONE space (names like "Brad D", "Bobley D")
    if ' ' not in text:
        logger.info(f"    Reason: No space (likely not a full name)")
        return False
    
    # Must have reasonable length (3-30 characters)
    if len(text) < 3 or len(text) > 30:
        logger.info(f"    Reason: Length {len(text)} outside 3-30 range")
        return False
    
    # Must contain letters
    has_letters = any(c.isalpha() for c in text)
    if not has_letters:
        logger.info(f"    Reason: No letters found")
        return False
    
    # Skip if mostly numbers
    digit_count = sum(c.isdigit() for c in text)
    if digit_count > len(text) * 0.5:
        logger.info(f"    Reason: Mostly numbers ({digit_count}/{len(text)} digits)")
        return False
    
    # Skip if too many special characters
    special_count = sum(1 for c in text if not c.isalnum() and c not in ' .-')
    if special_count > 2:
        logger.info(f"    Reason: Too many special chars ({special_count})")
        return False
    
    logger.info(f"    ✓ Passed all checks")
    return True


# ==================== PASS 2: FULL ROW EXTRACTION ====================

def extract_player_rows(
    img: np.ndarray,
    cells: List,
    player_rows: List[int]
) -> List[Dict]:
    """
    PASS 2: Extract ALL cells in each player row
    
    ADDED: Debug logging and cell image saving
    """
    logger.info("=" * 60)
    logger.info(f"PASS 2: Extracting full rows for {len(player_rows)} players")
    logger.info("=" * 60)
    
    # Find max column number
    max_col = max(cell.col for cell in cells)
    logger.info(f"Total columns detected: {max_col + 1} (0-{max_col})")
    
    player_data = []
    
    for player_row in player_rows:
        logger.info(f"Processing row {player_row}...")
        
        row_values = []
        
        # Extract ALL columns (0 to max_col)
        for col in range(0, max_col + 1):
            cell = find_cell(cells, player_row, col)
            if not cell:
                row_values.append(None)
                continue
            
            # Extract cell image
            cell_img = extract_cell_image(img, cell, padding=2)
            
            # ADDED: Save first 12 cells for debugging (columns 0-11)
            if col < 12:
                try:
                    # Save raw cell
                    debug_path_raw = f"/tmp/debug_row{player_row}_col{col:02d}_raw.png"
                    cv2.imwrite(debug_path_raw, cell_img)
                    logger.info(f"  Col {col}: shape={cell_img.shape}, saved to {debug_path_raw}")
                    
                    # Save preprocessed version
                    preprocessed = preprocess_score_cell(cell_img)
                    debug_path_proc = f"/tmp/debug_row{player_row}_col{col:02d}_processed.png"
                    cv2.imwrite(debug_path_proc, preprocessed)
                except Exception as e:
                    logger.warning(f"  Failed to save debug image: {e}")
            
            # Preprocess for handwritten scores
            cell_img_processed = preprocess_score_cell(cell_img)
            
            # OCR the cell
            cell_text = ocr_text_cell(cell_img_processed, mode='score')
            
            # ADDED: Log OCR result for first 12 cells
            if col < 12:
                logger.info(f"  Col {col} OCR result: '{cell_text}'")
            
            # Store result (None if OCR returns nothing)
            row_values.append(cell_text if cell_text else None)
        
        non_empty = sum(1 for v in row_values if v)
        logger.info(f"  Row {player_row}: Extracted {non_empty}/{len(row_values)} non-empty cells")
        logger.info(f"  Values: {row_values}")
        
        player_data.append({
            'row': player_row,
            'all_values': row_values
        })
    
    logger.info("=" * 60)
    logger.info(f"PASS 2 COMPLETE")
    logger.info("=" * 60)
    
    return player_data


# ==================== PREPROCESSING ====================

def preprocess_score_cell(cell_img: np.ndarray) -> np.ndarray:
    """
    Preprocess cell for handwritten score OCR
    
    CHANGED: Lighter preprocessing to preserve handwriting
    """
    # Convert to grayscale
    if len(cell_img.shape) == 3:
        gray = cv2.cvtColor(cell_img, cv2.COLOR_BGR2GRAY)
    else:
        gray = cell_img.copy()
    
    # CHANGED: Only resize if really small (lowered threshold from 50 to 40)
    min_size = 40
    if gray.shape[0] < min_size or gray.shape[1] < min_size:
        scale = max(min_size / gray.shape[0], min_size / gray.shape[1])
        new_width = int(gray.shape[1] * scale)
        new_height = int(gray.shape[0] * scale)
        gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
    
    # REMOVED: Heavy CLAHE enhancement (was destroying thin handwriting)
    # REMOVED: Bilateral filter denoising (was removing content)
    
    # CHANGED: Simple binary threshold instead of adaptive
    # Adaptive threshold can remove content in small cells
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return binary


def preprocess_name_cell(cell_img: np.ndarray) -> np.ndarray:
    """Preprocess cell for player name OCR (less aggressive)"""
    if len(cell_img.shape) == 3:
        gray = cv2.cvtColor(cell_img, cv2.COLOR_BGR2GRAY)
    else:
        gray = cell_img.copy()
    
    # Light enhancement only
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    
    return enhanced


# ==================== OCR FUNCTIONS ====================

def ocr_text_cell(cell_img: np.ndarray, mode: str = 'score') -> Optional[str]:
    """
    Run OCR on a cell with mode-specific configuration
    
    CHANGED: PSM 7 (single line) instead of PSM 10 (single char)
    """
    # Convert to PIL
    if len(cell_img.shape) == 2:
        pil_img = Image.fromarray(cell_img)
    else:
        pil_img = Image.fromarray(cell_img)
    
    try:
        if mode == 'score':
            # CHANGED: PSM 7 (single line) handles multi-digit scores better
            # PSM 10 was too restrictive for "35", "(3)", etc.
            config = '--psm 7 -c tessedit_char_whitelist=0123456789()'
            text = pytesseract.image_to_string(pil_img, config=config).strip()
            text = ''.join(c for c in text if c.isdigit() or c in '()')
            
        elif mode == 'name':
            # PSM 8 (single word) works better for short names like "Brad D"
            config = '--psm 8'
            text = pytesseract.image_to_string(pil_img, config=config).strip()
        
        else:
            text = pytesseract.image_to_string(pil_img).strip()
        
        return text if text else None
        
    except Exception as e:
        logger.warning(f"OCR failed for cell: {e}")
        return None


# ==================== VISUALIZATION ====================

def draw_scorecard_results(
    img: np.ndarray,
    cells: List,
    scorecard_data: Dict
) -> np.ndarray:
    """
    Draw visualization of extracted scorecard data
    
    ADDED: Show cell dimensions and mark empty cells with red border
    """
    # Convert to BGR
    if len(img.shape) == 2:
        vis_img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    else:
        vis_img = img.copy()
    
    for player in scorecard_data['players']:
        row = player['row']
        name = player['name']
        all_values = player['all_values']
        
        # Look for wide cells (name columns)
        name_cell = None
        for col in [0, 1, 2, 3]:
            cell = find_cell(cells, row, col)
            if cell and cell.width > 80:
                name_cell = cell
                break
        
        if name_cell:
            # Draw name cell in blue
            cv2.rectangle(
                vis_img,
                (name_cell.x, name_cell.y),
                (name_cell.x + name_cell.width, name_cell.y + name_cell.height),
                (255, 0, 0),  # Blue
                2
            )
            cv2.putText(
                vis_img,
                name,
                (name_cell.x + 5, name_cell.y + 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 0, 0),
                2
            )
        
        # Draw ALL cells - green if has value, red if None
        for col_idx, value in enumerate(all_values):
            cell = find_cell(cells, row, col_idx)
            if not cell:
                continue
            
            # CHANGED: Red border for empty cells, green for cells with values
            if value is None:
                color = (0, 0, 255)  # Red - OCR returned nothing
                thickness = 1
            else:
                color = (0, 255, 0)  # Green - OCR found something
                thickness = 2
            
            cv2.rectangle(
                vis_img,
                (cell.x, cell.y),
                (cell.x + cell.width, cell.y + cell.height),
                color,
                thickness
            )
            
            # ADDED: Show cell dimensions for first few columns
            if col_idx < 12:
                dim_text = f"{cell.width}x{cell.height}"
                cv2.putText(
                    vis_img,
                    dim_text,
                    (cell.x + 2, cell.y + 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.25,
                    (128, 128, 128),
                    1
                )
            
            # Show OCR value if present
            if value is not None:
                cv2.putText(
                    vis_img,
                    str(value)[:6],  # Truncate long values
                    (cell.x + 5, cell.y + cell.height - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.4,
                    color,
                    1
                )
    
    return vis_img


# ==================== HELPER FUNCTIONS ====================

def extract_cell_image(img: np.ndarray, cell, padding: int = 2) -> np.ndarray:
    """Extract a single cell from the image"""
    x1 = max(0, cell.x + padding)
    y1 = max(0, cell.y + padding)
    x2 = min(img.shape[1], cell.x + cell.width - padding)
    y2 = min(img.shape[0], cell.y + cell.height - padding)
    
    return img[y1:y2, x1:x2]


def find_cell(cells: List, row: int, col: int):
    """Find a cell by row/col index"""
    for cell in cells:
        if cell.row == row and cell.col == col:
            return cell
    return None


# ==================== MAIN ENTRY POINT ====================

def extract_scorecard_data(img: np.ndarray, cells: List) -> Dict:
    """
    Main function: Two-pass OCR to extract scorecard data
    """
    # PASS 1: Detect player rows
    detection_result = detect_player_rows(img, cells)
    player_rows = detection_result['player_rows']
    player_names = detection_result['player_names']
    
    # PASS 2: Extract full rows for those players
    player_data = extract_player_rows(img, cells, player_rows)
    
    # Combine names + row data
    players = []
    for i, data in enumerate(player_data):
        players.append({
            'row': data['row'],
            'name': player_names[i] if i < len(player_names) else 'Unknown',
            'all_values': data['all_values']
        })
    
    return {
        'players': players,
        'total_players': len(players)
    }