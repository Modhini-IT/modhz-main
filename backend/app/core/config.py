"""
Configuration settings for the Face Recognition Backend System
"""
import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    DEBUG: bool = Field(default=True, env="DEBUG")
    PORT: int = Field(default=5001, env="PORT")
    HOST: str = Field(default="0.0.0.0", env="HOST")
    
    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./face_recognition.db",
        env="DATABASE_URL"
    )
    
    # Security
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        env="SECRET_KEY"
    )
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # CORS
    ALLOWED_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            "https://your-frontend-domain.vercel.app"
        ],
        env="ALLOWED_ORIGINS"
    )
    
    # Face Recognition
    FACE_RECOGNITION_THRESHOLD: float = Field(default=0.6, env="FACE_RECOGNITION_THRESHOLD")
    MAX_FACE_DISTANCE: float = Field(default=0.4, env="MAX_FACE_DISTANCE")
    FACE_QUALITY_THRESHOLD: float = Field(default=0.5, env="FACE_QUALITY_THRESHOLD")
    
    # Video Processing
    MAX_FRAME_BUFFER_SIZE: int = Field(default=10, env="MAX_FRAME_BUFFER_SIZE")
    VIDEO_PROCESSING_FPS: int = Field(default=10, env="VIDEO_PROCESSING_FPS")
    
    # File Storage
    UPLOAD_DIR: str = Field(default="uploads", env="UPLOAD_DIR")
    MAX_FILE_SIZE: int = Field(default=10 * 1024 * 1024, env="MAX_FILE_SIZE")  # 10MB
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()