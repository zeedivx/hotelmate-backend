import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API Configuration
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEBUG: bool = True
    ENVIRONMENT: str = "development"

    # CORS Origins - React Native and web
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",  # Web development
        "http://127.0.0.1:3000",
        "http://localhost:8081",  # Expo web
        "http://127.0.0.1:8081",
        "exp://127.0.0.1:8081",  # Expo mobile
        "exp://localhost:8081",
        "*",  # Allow all for development (!TODO: usun to w produkcji)
    ]

    # JWT Configuration
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # Firebase Configuration
    FIREBASE_PROJECT_ID: str = "hotelmate-app"
    FIREBASE_CREDENTIALS_PATH: str = "firebase-admin-credentials.json"

    # Database Collections
    USERS_COLLECTION: str = "users"
    HOTELS_COLLECTION: str = "hotels"
    ROOMS_COLLECTION: str = "rooms"
    RESERVATIONS_COLLECTION: str = "reservations"

    # Password Hashing
    PASSWORD_HASH_ALGORITHM: str = "bcrypt"
    PASSWORD_HASH_ROUNDS: int = 12

    # API Rate Limiting (future use)
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 3600  # 1 hour

    # Application Settings
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Create settings instance
settings = Settings()

# Development vs Production configurations
if settings.ENVIRONMENT == "production":
    settings.DEBUG = False
    settings.ALLOWED_ORIGINS = [
        "https://example.com",
    ]


# Validate required environment variables
def validate_config():
    """Validate that all required configuration is present"""
    required_vars = [
        "FIREBASE_PROJECT_ID",
        "JWT_SECRET_KEY"
    ]

    missing_vars = []
    for var in required_vars:
        if not getattr(settings, var):
            missing_vars.append(var)

    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    # Check if Firebase credentials file exists
    if not os.path.exists(settings.FIREBASE_CREDENTIALS_PATH):
        print(f"⚠️  Warning: Firebase credentials file not found at {settings.FIREBASE_CREDENTIALS_PATH}")
        print("   You'll need to add this file to connect to Firebase Firestore")

    return True


# Run validation on import
try:
    validate_config()
    print("✅ Configuration loaded successfully")
except ValueError as e:
    print(f"❌ Configuration error: {e}")
except Exception as e:
    print(f"⚠️  Configuration warning: {e}")