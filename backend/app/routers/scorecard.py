from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import boto3
from botocore.exceptions import ClientError
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()

class ProcessScorecardRequest(BaseModel):
    s3_key: str

class ProcessScorecardResponse(BaseModel):
    message: str
    s3_key: str
    size_bytes: int
    bucket: str

@router.post("/process_scorecard")
async def process_scorecard(request: ProcessScorecardRequest):
    """
    Fetch a scorecard image from S3 and return basic info
    """

    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=settings.s3_region
    )

    try:
        logger.info(f"Fetching {request.s3_key} from S3")

        response = s3_client.get_object(
            Bucket=settings.s3_bucket_name,
            Key=request.s3_key
        )
        
        file_content = response['Body'].read()
        file_size = len(file_content)

        logger.info(f"Successfully fetched {file_size} bytes")

        return ProcessScorecardResponse(
            message="Successfully fetched scorecard from S3",
            s3_key=request.s3_key,
            size_bytes=file_size,
            bucket=settings.s3_bucket_name
        )
    
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logger.error(f"S3 Error: {error_code} - {error_message}")
        raise HTTPException(
            status_code=404 if error_code == 'NoSuchKey' else 500,
            detail=f"Failed to fetch from S3: {error_message}"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))