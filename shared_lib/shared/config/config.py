from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file
import os


class Config:
    # Database configuration
    DATABASE_URL = os.getenv("DATABASE_URL")
    # RabbitMQ configuration
    RABBITMQ_URL = os.getenv("RABBITMQ_URL")
    RABBITMQ_DEFAULT_USER = os.getenv("RABBITMQ_DEFAULT_USER")
    RABBITMQ_DEFAULT_PASS = os.getenv("RABBITMQ_DEFAULT_PASS")
    # MinIO configuration
    MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
    MINIO_ENDPOINT = os.getenv("MINIO_URL")
    MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "license-plate-recognition-bucket")
    # Other configurations can be added here as needed
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
    REDIS_URL = os.getenv("REDIS_URL")
    FACE_MATCH_THRESHOLD = float(os.getenv("FACE_MATCH_THRESHOLD", 0.5))


config = Config()
