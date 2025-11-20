import csv
import io
from typing import List
from app.schemas.scorecard import ScorecardData, Player
import logging

logger = logging.getLogger(__name__)

def export_to_csv(data: ScorecardData) -> bytes:
    """
    Export scorecard data to CSV format
    
    Args:
        data: Scorecard data with players and scores
        
    Returns:
        CSV file as bytes
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header row 1: Course and date info
    if data.course or data.date:
        header_info = []
        if data.course:
            header_info.append(f"Course: {data.course}")
        if data.date:
            header_info.append(f"Date: {data.date}")
        writer.writerow(header_info)
        writer.writerow([])  # Empty row
    
    # Header row 2: Hole numbers
    hole_headers = ["Player", "Handicap"] + [f"Hole {i+1}" for i in range(18)] + ["Front 9", "Back 9", "Total"]
    writer.writerow(hole_headers)
    
    # Par row (if available)
    if data.par and any(p is not None for p in data.par):
        par_row = ["Par", ""] + [str(p) if p is not None else "-" for p in data.par]
        # Calculate par totals
        front_nine_par = sum(p for p in data.par[:9] if p is not None) if data.par else None
        back_nine_par = sum(p for p in data.par[9:18] if p is not None) if data.par else None
        total_par = sum(p for p in data.par if p is not None) if data.par else None
        par_row += [
            str(front_nine_par) if front_nine_par else "-",
            str(back_nine_par) if back_nine_par else "-",
            str(total_par) if total_par else "-"
        ]
        writer.writerow(par_row)
    
    # Player rows
    for player in data.players:
        player_row = [
            player.name,
            str(player.handicap) if player.handicap is not None else "-"
        ]
        # Add scores
        player_row += [str(s) if s is not None else "-" for s in player.scores]
        # Add totals
        player_row += [
            str(player.front_nine_total) if player.front_nine_total is not None else "-",
            str(player.back_nine_total) if player.back_nine_total is not None else "-",
            str(player.total) if player.total is not None else "-"
        ]
        writer.writerow(player_row)
    
    # Get CSV content as bytes
    csv_content = output.getvalue()
    output.close()
    
    logger.info(f"Generated CSV with {len(data.players)} players")
    
    return csv_content.encode('utf-8')

def export_to_excel(data: ScorecardData) -> bytes:
    """
    Export scorecard data to Excel format
    
    Args:
        data: Scorecard data with players and scores
        
    Returns:
        Excel file as bytes
        
    TODO: Implement using openpyxl (Phase 1.5)
    """
    raise NotImplementedError("Excel export coming in Phase 1.5")