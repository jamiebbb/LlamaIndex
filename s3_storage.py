import boto3
import os
from botocore.exceptions import ClientError
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class S3Storage:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.bucket_name = os.getenv('AWS_BUCKET_NAME')
        
        # Create bucket if it doesn't exist
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError:
            self.s3_client.create_bucket(Bucket=self.bucket_name)
            logger.info(f"Created new S3 bucket: {self.bucket_name}")

    def upload_file(self, file_obj, filename):
        """Upload a file to S3"""
        try:
            # Generate a unique key for the file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            key = f"pdfs/{timestamp}_{filename}"
            
            # Upload the file
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket_name,
                key
            )
            
            # Get the file URL
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': key},
                ExpiresIn=3600  # URL expires in 1 hour
            )
            
            return {
                'key': key,
                'url': url,
                'filename': filename,
                'upload_date': datetime.now().isoformat()
            }
            
        except ClientError as e:
            logger.error(f"Error uploading file to S3: {str(e)}")
            raise

    def get_file_url(self, key):
        """Get a presigned URL for a file"""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': key},
                ExpiresIn=3600
            )
            return url
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            raise

    def list_files(self):
        """List all PDF files in the bucket"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix='pdfs/'
            )
            
            files = []
            for obj in response.get('Contents', []):
                if obj['Key'].endswith('.pdf'):
                    url = self.get_file_url(obj['Key'])
                    files.append({
                        'key': obj['Key'],
                        'url': url,
                        'filename': obj['Key'].split('/')[-1],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat()
                    })
            
            return files
            
        except ClientError as e:
            logger.error(f"Error listing files from S3: {str(e)}")
            raise

    def delete_file(self, key):
        """Delete a file from S3"""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return True
        except ClientError as e:
            logger.error(f"Error deleting file from S3: {str(e)}")
            raise 