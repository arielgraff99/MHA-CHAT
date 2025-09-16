import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration class"""
    
    # Basic Flask/FastAPI settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///timeline_narrator.db')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # File storage
    BASE_DIR = Path(__file__).parent.parent
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', str(BASE_DIR / 'data' / 'uploads'))
    EXPORT_FOLDER = os.getenv('EXPORT_FOLDER', str(BASE_DIR / 'data' / 'exports'))
    TEMP_FOLDER = os.getenv('TEMP_FOLDER', str(BASE_DIR / 'data' / 'temp'))
    OUTPUT_DIRECTORY = ""  # Set dynamically based on source directory
    MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', '250'))
    MAX_TOTAL_SIZE_GB = int(os.getenv('MAX_TOTAL_SIZE_GB', '5'))
    
    # NLP & AI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    SPACY_MODEL = os.getenv('SPACY_MODEL', 'en_core_web_sm')
    LLM_MODEL = os.getenv('LLM_MODEL', 'gpt-4')
    LLM_TEMPERATURE = float(os.getenv('LLM_TEMPERATURE', '0.2'))
    LLM_MAX_TOKENS = int(os.getenv('LLM_MAX_TOKENS', '2000'))
    
    # OCR
    TESSERACT_PATH = os.getenv('TESSERACT_PATH', '/usr/bin/tesseract')
    
    # Security
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
    
    # Timezone
    DEFAULT_TIMEZONE = os.getenv('DEFAULT_TIMEZONE', 'America/Toronto')
    
    # API
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', '8000'))
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    AUDIT_LOG_PATH = os.getenv('AUDIT_LOG_PATH', str(BASE_DIR / 'logs' / 'audit.log'))
    
    # Supported file types
    SUPPORTED_EXTENSIONS = {
        'email': ['.eml', '.msg'],
        'text': ['.txt', '.md', '.csv', '.json'],
        'pdf': ['.pdf'],
        'image': ['.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.gif']
    }
    
    # Timeline settings
    INTERNAL_GRANULARITY = 'second'
    DEDUPLICATION_WINDOW_SECONDS = 120
    SIMILARITY_THRESHOLD = 0.9
    
    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist"""
        directories = [
            cls.UPLOAD_FOLDER,
            cls.EXPORT_FOLDER,
            cls.TEMP_FOLDER,
            Path(cls.AUDIT_LOG_PATH).parent
        ]
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

# Create config instance
config = Config()
config.ensure_directories()