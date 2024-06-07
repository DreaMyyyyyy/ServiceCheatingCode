from minio import Minio
from minio.error import S3Error
import os

# Настройки Minio
MINIO_CLIENT = Minio(
    os.getenv('MINIO_URL', 'localhost:9000'),
    access_key=os.getenv('MINIO_ACCESS_KEY', 'minio'),
    secret_key=os.getenv('MINIO_SECRET_KEY', 'minio123'),
    secure=False
)

BUCKET_NAME = os.getenv('MINIO_BUCKET_NAME', 'code-reports')

def get_file_from_minio(doc_version_id):
    try:
        response = MINIO_CLIENT.get_object(BUCKET_NAME, f"{doc_version_id}.ipynb")
        file_content = response.read().decode('utf-8')
        response.close()
        response.release_conn()
        return file_content
    except S3Error as exc:
        print(f"Error occurred: {exc}")
        return None

