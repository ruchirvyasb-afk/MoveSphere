from dotenv import load_dotenv
import os

load_dotenv()

print("Bucket:", os.getenv("AWS_BUCKET_NAME"))
print("Region:", os.getenv("AWS_REGION"))
print("Access Key Found:", bool(os.getenv("AWS_ACCESS_KEY_ID")))
print("Secret Key Found:", bool(os.getenv("AWS_SECRET_ACCESS_KEY")))