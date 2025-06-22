import os

class Config:
    # AWS Configuration
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
    
    # MongoDB Configuration
    MONGODB_URI = os.environ.get('MONGODB_URI')
    
    # Application Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'set-a-strong-secret-key')
    DEBUG = os.environ.get('DEBUG', 'False') == 'True'

    # AquaPulse - Configuration for Harmful Algae Bloom Detection
