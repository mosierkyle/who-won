import anthropic
import base64
import logging
from typing import Dict
import json
import imghdr  # NEW: For detecting image type

logger = logging.getLogger(__name__)

class ClaudeService:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def _detect_image_type(self, image_bytes: bytes) -> str:
        """
        Detect the image format from bytes
        
        Returns:
            Media type string (e.g., 'image/png', 'image/jpeg')
        """
        # Try to detect using imghdr
        image_type = imghdr.what(None, h=image_bytes)
        
        # Map to media types
        type_map = {
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp'
        }
        
        media_type = type_map.get(image_type, 'image/jpeg')  # Default to jpeg
        logger.info(f"Detected image type: {media_type}")
        
        return media_type
    
    async def extract_scorecard_data(self, image_bytes: bytes) -> Dict:
        """
        Extract scorecard data using Claude Vision API
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Structured scorecard data
        """
        try:
            # Detect image type
            media_type = self._detect_image_type(image_bytes)
            
            # Encode image to base64
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            logger.info(f"Sending image to Claude API (type: {media_type})...")
            
            # Call Claude API
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,  # CHANGED: Use detected type
                                "data": image_base64,
                            },
                        },
                        {
                            "type": "text",
                            "text": """Analyze this golf scorecard and extract ALL player data.

CRITICAL INSTRUCTIONS:
1. Extract EVERY player's name and ALL 18 hole scores
2. Calculate the total score for each player
3. Identify the winner (lowest total score)
4. Return ONLY valid JSON, no other text

JSON FORMAT (STRICT):
{
  "players": [
    {
      "name": "Player Full Name",
      "scores": [score_hole_1, score_hole_2, ..., score_hole_18],
      "total": total_score
    }
  ],
  "winner": "Winner Name",
  "course": "Course Name (if visible)",
  "date": "Date (if visible)"
}

RULES:
- If a cell is empty, use null
- Include circled scores as regular numbers
- Names should be clean (no special characters unless part of name)
- DO NOT include any markdown, explanations, or backticks
- Output MUST be valid JSON only
"""
                        }
                    ]
                }]
            )
            
            # Extract response text
            response_text = message.content[0].text.strip()
            
            # Remove markdown code blocks if present (just in case)
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            # Parse JSON
            result = json.loads(response_text)
            
            logger.info(f"Claude API extracted {len(result.get('players', []))} players")
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response as JSON: {e}")
            logger.error(f"Response was: {response_text}")
            raise ValueError(f"Claude returned invalid JSON: {str(e)}")
        
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise

# Singleton instance
claude_service = None

def get_claude_service() -> ClaudeService:
    """Get or create Claude service instance"""
    global claude_service
    if claude_service is None:
        from app.config import get_settings
        settings = get_settings()
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY not set in environment")
        claude_service = ClaudeService(api_key=settings.anthropic_api_key)
    return claude_service