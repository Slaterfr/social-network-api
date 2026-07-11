import os
from pathlib import Path
from dotenv import load_dotenv

# Load dotenv from app/.env relative to this file
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    """Application configuration from environment variables."""
    SQLALCHEMY_DATABASE_URL = os.getenv('SQLALCHEMY_DATABASE_URL') or os.getenv('DATABASE_URL')
    SECRET_KEY = os.getenv('SECRET_KEY')
    AWS_ACCESS_KEY_ID=os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY=os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_REGION=os.getenv('AWS_REGION')
    AWS_BUCKET_NAME=os.getenv('AWS_BUCKET_NAME')
    AWS_PUBLIC_BASE_URL=os.getenv('AWS_PUBLIC_BASE_URL')
