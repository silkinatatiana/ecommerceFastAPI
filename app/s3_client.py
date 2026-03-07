import logging

import boto3
from botocore.client import Config

from config import Config as AppConfig


logger = logging.getLogger(__name__)


class S3Client:
    def __init__(self):
        self.client = boto3.client(
            "s3",
            endpoint_url=AppConfig.S3_ENDPOINT_URL,
            aws_access_key_id=AppConfig.S3_ACCESS_KEY,
            aws_secret_access_key=AppConfig.S3_SECRET_KEY,
            region_name=AppConfig.S3_REGION_NAME,
            config=Config(signature_version="s3v4"),
        )
        self.bucket_name = AppConfig.S3_BUCKET_NAME
        self.public_url = AppConfig.S3_PUBLIC_URL

    def upload_fileobj(self, fileobj, key, extra_args=None):
        try:
            self.client.upload_fileobj(
                fileobj, self.bucket_name, key, ExtraArgs=extra_args
            )
            return f"{self.public_url}/{key}"
        except Exception as e:
            logger.error(f"Error uploading to S3: {e}")
            raise

    def generate_presigned_url(self, key, expires_in=3600):
        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": key},
                ExpiresIn=expires_in,
            )
            return url
        except Exception as e:
            logger.error(f"Error generating presigned URL: {e}")
            return None

    def delete_object(self, key):
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=key)
        except Exception as e:
            logger.error(f"Error deleting from S3: {e}")
            raise


s3_client = S3Client()
