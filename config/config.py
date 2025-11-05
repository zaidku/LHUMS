"""Configuration settings for different environments."""
import os
from datetime import timedelta


class Config:
    """Base configuration."""
    
    # Secret key for signing tokens
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # CORS
    CORS_HEADERS = 'Content-Type'
    
    # Mail configuration
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'false').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@ums.com')
    
    # Security settings
    MAX_LOGIN_ATTEMPTS = int(os.getenv('MAX_LOGIN_ATTEMPTS', 5))
    ACCOUNT_LOCKOUT_DURATION = int(os.getenv('ACCOUNT_LOCKOUT_DURATION', 30))  # minutes
    PASSWORD_RESET_TOKEN_EXPIRY = int(os.getenv('PASSWORD_RESET_TOKEN_EXPIRY', 24))  # hours
    EMAIL_VERIFICATION_TOKEN_EXPIRY = int(os.getenv('EMAIL_VERIFICATION_TOKEN_EXPIRY', 48))  # hours
    
    # Password policy (HIPAA compliance)
    PASSWORD_MIN_LENGTH = int(os.getenv('PASSWORD_MIN_LENGTH', 8))
    PASSWORD_EXPIRY_DAYS = int(os.getenv('PASSWORD_EXPIRY_DAYS', 90))  # HIPAA requires 90 days
    PASSWORD_HISTORY_COUNT = int(os.getenv('PASSWORD_HISTORY_COUNT', 5))  # Remember last 5 passwords
    PASSWORD_COMPLEXITY_REQUIRED = os.getenv('PASSWORD_COMPLEXITY_REQUIRED', 'true').lower() == 'true'


class DevelopmentConfig(Config):
    """Development configuration."""
    
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:///ums_dev.db'
    )
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """Production configuration."""
    
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    
    # Ensure secret keys are set in production
    @classmethod
    def init_app(cls, app):
        if not os.getenv('SECRET_KEY'):
            raise ValueError('SECRET_KEY must be set in production')
        if not os.getenv('DATABASE_URL'):
            raise ValueError('DATABASE_URL must be set in production')


class TestingConfig(Config):
    """Testing configuration."""
    
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///ums_test.db'
    WTF_CSRF_ENABLED = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
