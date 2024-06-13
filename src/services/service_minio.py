from minio import S3Error

from src.config.config import config
from src.config.storage import MinioClient


def get_file_from_minio(doc_version_id):
    try:
        response = MinioClient.get_object(config.minio_bucket_name, f"{doc_version_id}.ipynb")
        file_content = response.read().decode('utf-8')
        response.close()
        response.release_conn()
        return file_content
    except S3Error as exc:
        print(f"Error occurred: {exc}")
        return None