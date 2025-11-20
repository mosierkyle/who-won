from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # AWS S3 Configuration
    aws_access_key_id: str
    aws_secret_access_key: str
    s3_bucket_name: str
    s3_region: str = "us-west-1"

    anthropic_api_key: str = ""
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    """Cache settings so we only load once"""
    return Settings()