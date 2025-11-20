from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # AWS S3 Configuration
    aws_access_key_id: str
    aws_secret_access_key: str
    s3_bucket_name: str
    s3_region: str = "us-east-1"
    
    # Anthropic API Configuration
    anthropic_api_key: str
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()