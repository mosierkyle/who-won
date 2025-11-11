import boto3
from botocore.exceptions import ClientError
import logging
import uuid
from typing import Tuple

from app.config import get_settings

logger = logging.getLogger(__name__)

class S3Service:
    def __init__(self):
        settings = get_settings()
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.s3_region
        )
        self.bucket_name = settings.s3_bucket_name
    
    def generate_scorecard_id(self) -> str:
        """Generate a unique UUID for scorecard"""
        return str(uuid.uuid4())
    
    def extract_filename(self, s3_key: str) -> str:
        """Extract original filename from S3 key"""
        return s3_key.split('/')[-1]
    
    def get_processed_folder_path(self, scorecard_id: str) -> str:
        """Get the S3 folder path for processed images"""
        return f"Processed/{scorecard_id}/"
    
    async def download_file(self, s3_key: str) -> Tuple[bytes, str]:
        """
        Download file from S3
        Returns: (file_bytes, original_filename)
        """
        try:
            logger.info(f"Downloading {s3_key} from S3")
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            file_bytes = response['Body'].read()
            original_filename = self.extract_filename(s3_key)
            logger.info(f"Downloaded {len(file_bytes)} bytes")
            return file_bytes, original_filename
        except ClientError as e:
            logger.error(f"Error downloading from S3: {e}")
            raise
    
    async def upload_file(
        self, 
        file_bytes: bytes, 
        s3_key: str, 
        content_type: str = "image/jpeg"
    ) -> str:
        """
        Upload file to S3
        Returns: S3 key
        """
        try:
            logger.info(f"Uploading to {s3_key}")
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_bytes,
                ContentType=content_type
            )
            logger.info(f"Upload successful: {s3_key}")
            return s3_key
        except ClientError as e:
            logger.error(f"Error uploading to S3: {e}")
            raise

s3_service = S3Service()