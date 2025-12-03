import cv2
import numpy as np
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class Cell:
    """Represents a single cell in the table"""
    def __init__(self, row: int, col: int, x: int, y: int, width: int, height: int):
        self.row = row          # Row index (0-based)
        self.col = col          # Column index (0-based)
        self.x = x              # X coordinate (left edge)
        self.y = y              # Y coordinate (top edge)
        self.width = width      # Cell width
        self.height = height    # Cell height
        self.text = ""          # OCR result (filled later)
        self.confidence = 0.0   # OCR confidence (filled later)

class TableGrid:
    """Represents the detected table structure"""
    def __init__(
        self, 
        horizontal_lines: List[Tuple[int, int, int, int]],
        vertical_lines: List[Tuple[int, int, int, int]],
        cells: List[Cell]
    ):
        self.horizontal_lines = horizontal_lines  # [(x1, y1, x2, y2), ...]
        self.vertical_lines = vertical_lines
        self.cells = cells
        self.num_rows = max(c.row for c in cells) + 1 if cells else 0
        self.num_cols = max(c.col for c in cells) + 1 if cells else 0

def detect_lines(img: np.ndarray, kernel_length: int, is_horizontal: bool) -> np.ndarray:
    """
    Detect either horizontal or vertical lines in an image using morphological operations.
    
    Args:
        img: Binary image (black background, white content)
        kernel_length: Length of the line detection kernel (longer = detects longer lines)
        is_horizontal: True for horizontal lines, False for vertical
    
    Returns:
        Binary image with only the detected lines
    
    How it works:
    1. Create a kernel (template) shaped like the lines we want to find
    2. Apply morphological operations to isolate those lines
    3. Everything else gets removed
    """
    # Create the kernel based on direction
    if is_horizontal:
        # Horizontal kernel: [1 1 1 1 1 ... 1]  (wide and short)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_length, 1))
    else:
        # Vertical kernel: [1; 1; 1; 1; ...]  (tall and narrow)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, kernel_length))
    
    # Morphological operation: erosion followed by dilation
    # This combo is called "opening" - it removes small objects but keeps lines
    eroded = cv2.erode(img, kernel, iterations=1)
    dilated = cv2.dilate(eroded, kernel, iterations=1)
    
    return dilated

def find_line_positions(lines_img: np.ndarray, is_horizontal: bool, min_length: int = 50) -> List[int]:
    """
    Find the Y positions (for horizontal) or X positions (for vertical) of detected lines.
    
    Args:
        lines_img: Binary image containing only lines
        is_horizontal: True for horizontal lines (returns Y positions)
        min_length: Minimum length for a line to be considered valid
    
    Returns:
        List of positions sorted in ascending order
    """
    # Find contours (outlines of white regions)
    contours, _ = cv2.findContours(lines_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    logger.info(f"Found {len(contours)} contours for {'horizontal' if is_horizontal else 'vertical'} lines")
    
    positions = []
    for idx, contour in enumerate(contours):
        # Get bounding box: (x, y, width, height)
        x, y, w, h = cv2.boundingRect(contour)
        
        if is_horizontal:
            # For horizontal lines, check if width is long enough
            if w >= min_length:
                # Use the center Y position
                positions.append(y + h // 2)
                if idx < 5:  # Log first 5 for debugging
                    logger.debug(f"  H-line contour {idx}: y={y}, w={w}, h={h}")
        else:
            # For vertical lines, check if height is tall enough
            if h >= min_length:
                # Use the center X position
                positions.append(x + w // 2)
                if idx < 5:  # Log first 5 for debugging
                    logger.debug(f"  V-line contour {idx}: x={x}, w={w}, h={h}")
    
    logger.info(f"After filtering by min_length={min_length}: {len(positions)} lines remain")
    
    # Sort and remove duplicates (lines close to each other)
    positions = sorted(set(positions))
    
    filtered = []
    for pos in positions:
        if not filtered or abs(pos - filtered[-1]) > 20: 
            filtered.append(pos)
    
    logger.info(f"After duplicate removal: {len(filtered)} unique lines")
    
    return filtered

def extract_cells_from_grid(
    img: np.ndarray,
    horizontal_positions: List[int],
    vertical_positions: List[int]
) -> List[Cell]:
    """
    Create Cell objects for each intersection in the grid.
    
    Args:
        img: Original image
        horizontal_positions: Y coordinates of horizontal lines
        vertical_positions: X coordinates of vertical lines
    
    Returns:
        List of Cell objects with their coordinates
    
    How it works:
    Each cell is defined by:
    - Top edge: horizontal_positions[row]
    - Bottom edge: horizontal_positions[row + 1]
    - Left edge: vertical_positions[col]
    - Right edge: vertical_positions[col + 1]
    """
    cells = []
    
    # For each row (between consecutive horizontal lines)
    for row_idx in range(len(horizontal_positions) - 1):
        y1 = horizontal_positions[row_idx]
        y2 = horizontal_positions[row_idx + 1]
        
        # For each column (between consecutive vertical lines)
        for col_idx in range(len(vertical_positions) - 1):
            x1 = vertical_positions[col_idx]
            x2 = vertical_positions[col_idx + 1]
            
            # Create cell
            cell = Cell(
                row=row_idx,
                col=col_idx,
                x=x1,
                y=y1,
                width=x2 - x1,
                height=y2 - y1
            )
            cells.append(cell)
    
    logger.info(f"Extracted {len(cells)} cells ({len(horizontal_positions)-1} rows × {len(vertical_positions)-1} cols)")
    return cells

def detect_table(img: np.ndarray, debug: bool = False) -> Optional[TableGrid]:
    """
    Main function: Detect table structure in an image.
    """
    logger.info("Starting table detection")
    logger.info(f"Image shape: {img.shape}, dtype: {img.dtype}")
    
    # Ensure image is grayscale
    if len(img.shape) == 3:
        logger.info("Converting image to grayscale for table detection")
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Invert image: black background, white lines and text
    inverted = cv2.bitwise_not(img)
    
    # Get image dimensions
    height, width = img.shape[:2]
    logger.info(f"Image dimensions: {width}x{height}")
    
    # Scorecards often have thinner lines than documents
    h_kernel_length = max(width // 15, 40)
    v_kernel_length = max(height // 15, 40)
    
    logger.info(f"Using kernel lengths: horizontal={h_kernel_length}, vertical={v_kernel_length}")
    
    # Detect horizontal lines
    horizontal_lines_img = detect_lines(inverted, h_kernel_length, is_horizontal=True)
    h_line_count = cv2.countNonZero(horizontal_lines_img)
    logger.info(f"Horizontal lines detected: {h_line_count} pixels")
    
    # Detect vertical lines
    vertical_lines_img = detect_lines(inverted, v_kernel_length, is_horizontal=False)
    v_line_count = cv2.countNonZero(vertical_lines_img)
    logger.info(f"Vertical lines detected: {v_line_count} pixels")
    
    # Find positions of lines
    min_h_length = width // 8 
    min_v_length = height // 8
    
    logger.info(f"Minimum line lengths: horizontal={min_h_length}, vertical={min_v_length}")
    
    horizontal_positions = find_line_positions(
        horizontal_lines_img, 
        is_horizontal=True, 
        min_length=min_h_length
    )
    vertical_positions = find_line_positions(
        vertical_lines_img, 
        is_horizontal=False, 
        min_length=min_v_length
    )
    
    logger.info(f"Detected {len(horizontal_positions)} horizontal lines at positions: {horizontal_positions[:10]}...")
    logger.info(f"Detected {len(vertical_positions)} vertical lines at positions: {vertical_positions[:10]}...")
    
    # Need at least 2 lines in each direction to form cells
    if len(horizontal_positions) < 2 or len(vertical_positions) < 2:
        logger.warning(f"Not enough lines detected to form a table. H={len(horizontal_positions)}, V={len(vertical_positions)}")
        return None
    
    # Extract cells
    cells = extract_cells_from_grid(img, horizontal_positions, vertical_positions)
    
    # Create line coordinates for visualization
    h_lines = [(0, y, width, y) for y in horizontal_positions]
    v_lines = [(x, 0, x, height) for x in vertical_positions]
    
    return TableGrid(
        horizontal_lines=h_lines,
        vertical_lines=v_lines,
        cells=cells
    )

def draw_detected_grid(img: np.ndarray, grid: TableGrid) -> np.ndarray:
    """
    Visualize the detected grid by drawing lines and cell numbers.
    
    Args:
        img: Original image
        grid: Detected TableGrid
    
    Returns:
        Image with grid visualization
    """
    # Convert grayscale to BGR for colored lines
    if len(img.shape) == 2:
        vis_img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    else:
        vis_img = img.copy()
    
    # Draw horizontal lines (blue)
    for x1, y1, x2, y2 in grid.horizontal_lines:
        cv2.line(vis_img, (x1, y1), (x2, y2), (255, 0, 0), 2)
    
    # Draw vertical lines (green)
    for x1, y1, x2, y2 in grid.vertical_lines:
        cv2.line(vis_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
    
    # Draw cell indices
    for cell in grid.cells:
        # Cell center
        cx = cell.x + cell.width // 2
        cy = cell.y + cell.height // 2
        
        # Label with row, col
        label = f"({cell.row},{cell.col})"
        cv2.putText(vis_img, label, (cx - 30, cy), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
    
    return vis_img

def extract_cell_image(img: np.ndarray, cell: Cell, padding: int = 2) -> np.ndarray:
    """
    Extract a single cell from the image and clean it.
    
    Args:
        img: Full image
        cell: Cell object with coordinates
        padding: Pixels to remove from edges (removes line fragments)
    
    Returns:
        Cropped and cleaned cell image
    """
    # Add padding to remove border lines
    x1 = max(0, cell.x + padding)
    y1 = max(0, cell.y + padding)
    x2 = min(img.shape[1], cell.x + cell.width - padding)
    y2 = min(img.shape[0], cell.y + cell.height - padding)
    
    # Crop the cell
    cell_img = img[y1:y2, x1:x2]
    
    return cell_img