
from dotenv import load_dotenv
import os
import boto3

load_dotenv()

BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)

def upload_file(local_file, s3_file):
    s3.upload_file(local_file, BUCKET_NAME, s3_file)

    return (
        f"https://{BUCKET_NAME}.s3."
        f"{os.getenv('AWS_REGION')}.amazonaws.com/{s3_file}"
    )