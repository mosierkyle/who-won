from typing import List, Optional, Tuple
from app.schemas.scorecard import Player
import logging

logger = logging.getLogger(__name__)

def calculate_totals(player: Player) -> Player:
    """
    Calculate total, front 9, and back 9 scores for a player
    Supports both 9-hole and 18-hole rounds
    
    Args:
        player: Player with scores
        
    Returns:
        Player with calculated totals
    """
    scores = player.scores
    num_holes = len(scores)
    
    # Calculate total (ignoring None values)
    valid_scores = [s for s in scores if s is not None]
    player.total = sum(valid_scores) if valid_scores else None
    
    # CHANGED: Handle 9-hole vs 18-hole rounds
    if num_holes == 9:
        # 9-hole round: all scores are "front nine"
        player.front_nine_total = player.total
        player.back_nine_total = None
    else:
        # 18-hole round
        # Calculate front 9 (holes 0-8 in 0-indexed array)
        front_nine = scores[:9]
        valid_front = [s for s in front_nine if s is not None]
        player.front_nine_total = sum(valid_front) if valid_front else None
        
        # Calculate back 9 (holes 9-17 in 0-indexed array)
        back_nine = scores[9:18]
        valid_back = [s for s in back_nine if s is not None]
        player.back_nine_total = sum(valid_back) if valid_back else None
    
    return player

def calculate_stroke_play_winner(players: List[Player]) -> Optional[str]:
    """
    Calculate winner for stroke play (lowest total score)
    
    Args:
        players: List of players with calculated totals
        
    Returns:
        Name of winner, or None if no valid scores
    """
    # Filter players with valid totals
    valid_players = [p for p in players if p.total is not None]
    
    if not valid_players:
        logger.warning("No players with valid total scores")
        return None
    
    # Find player with lowest score
    winner = min(valid_players, key=lambda p: p.total)
    
    logger.info(f"Stroke play winner: {winner.name} with score {winner.total}")
    
    return winner.name

def process_players(players: List[Player]) -> Tuple[List[Player], Optional[str]]:
    """
    Process all players: calculate totals and determine winner
    
    Args:
        players: Raw player data from Claude
        
    Returns:
        (players_with_totals, winner_name)
    """
    # Calculate totals for each player
    players_with_totals = [calculate_totals(player) for player in players]
    
    # Determine winner (stroke play for Phase 1)
    winner = calculate_stroke_play_winner(players_with_totals)
    
    return players_with_totals, winner