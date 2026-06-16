import os
from s3_utils import upload_file

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

file_path = os.path.join(BASE_DIR, "pdfs", "test.txt")

print("Uploading:", file_path)

url = upload_file(
    file_path,
    "test-folder/test.txt"
)

print("Upload successful!")
print(url)