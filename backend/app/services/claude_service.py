import anthropic
import base64
import logging
from typing import Dict
import json
import imghdr
from PIL import Image
import io

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
        image_type = imghdr.what(None, h=image_bytes)
        
        type_map = {
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp'
        }
        
        media_type = type_map.get(image_type, 'image/jpeg')
        logger.info(f"Detected image type: {media_type}")
        
        return media_type
    
    def _compress_image(self, image_bytes: bytes, max_size_mb: float = 4.5) -> bytes:
        """
        Compress image to under max_size_mb (default 4.5MB to be safe under 5MB limit)
        
        Args:
            image_bytes: Original image bytes
            max_size_mb: Maximum size in megabytes
            
        Returns:
            Compressed image bytes
        """
        max_size_bytes = int(max_size_mb * 1024 * 1024)
        
        # If already under limit, return as-is
        if len(image_bytes) <= max_size_bytes:
            logger.info(f"Image size OK: {len(image_bytes)} bytes")
            return image_bytes
        
        logger.info(f"Compressing image from {len(image_bytes)} bytes to under {max_size_bytes} bytes")
        
        # Open image
        img = Image.open(io.BytesIO(image_bytes))
        
        # Convert RGBA to RGB if needed
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        
        # Start with quality 85, reduce if needed
        quality = 85
        while quality > 20:
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=quality, optimize=True)
            compressed_bytes = output.getvalue()
            
            if len(compressed_bytes) <= max_size_bytes:
                logger.info(f"Compressed to {len(compressed_bytes)} bytes at quality {quality}")
                return compressed_bytes
            
            quality -= 10
        
        # If still too large, resize
        logger.info("Image still too large, resizing...")
        scale = 0.8
        while len(compressed_bytes) > max_size_bytes and scale > 0.3:
            new_width = int(img.width * scale)
            new_height = int(img.height * scale)
            resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            output = io.BytesIO()
            resized.save(output, format='JPEG', quality=85, optimize=True)
            compressed_bytes = output.getvalue()
            
            logger.info(f"Resized to {new_width}x{new_height}, size: {len(compressed_bytes)} bytes")
            scale -= 0.1
        
        return compressed_bytes
    
    async def extract_scorecard_data(self, image_bytes: bytes) -> Dict:
        """
        Extract scorecard data using Claude Vision API (Haiku model)
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Structured scorecard data
        """
        try:
            image_bytes = self._compress_image(image_bytes)
            
            media_type = self._detect_image_type(image_bytes)
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            logger.info(f"Sending image to Claude API (Haiku, type: {media_type})...")
            
            message = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=1500,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_base64,
                            },
                        },
                        {
                            "type": "text",
                            "text": """Extract all data from this golf scorecard.

Return ONLY valid JSON with this exact structure:
{
  "course": "Course Name or null",
  "date": "Date or null",
  "par": [par_hole_1, par_hole_2, ..., par_hole_18],
  "players": [
    {
      "name": "Player Name",
      "scores": [score_hole_1, ..., score_hole_18],
      "handicap": handicap_value_or_null
    }
  ]
}

RULES:
- Extract ALL players and their scores for all 18 holes
- If a score/par is empty or unreadable, use null
- If par row is not visible, use null for entire par array
- If handicap not shown, use null
- Clean player names (remove extra spaces/characters)
- DO NOT include markdown, backticks, or explanations
- Output MUST be valid JSON only
"""
                        }
                    ]
                }]
            )
            
            response_text = message.content[0].text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
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