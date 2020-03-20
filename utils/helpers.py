import boto3
import logging
from botocore.exceptions import ClientError
from django.conf import settings

def create_presigned_post(bucket_name, object_name,
                          fields=None, conditions=None, 
                          expiration=3600):
  
    s3_client = boto3.client(
        's3', 
        region_name=settings.COGNITO_AWS_REGION, 
        aws_access_key_id = settings.AWS_ACCESS_KEY_ID, 
        aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY
    )
    
    try:
        return s3_client.generate_presigned_post(
            bucket_name,
            object_name,
            Fields=fields,
            Conditions=conditions,
            ExpiresIn=expiration
        )
    except ClientError as e:
        logging.error(e)
        return None


