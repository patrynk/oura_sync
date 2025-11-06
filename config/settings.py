"""Configuration management for Oura Sync service."""
import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Oura API OAuth2 Settings
    oura_client_id: str
    oura_client_secret: str
    oura_redirect_uri: str = "http://localhost:8000/callback"
    oura_api_base_url: str = "https://api.ouraring.com"
    oura_auth_base_url: str = "https://cloud.ouraring.com/oauth"
    
    # Database Settings
    database_url: Optional[str] = None
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "oura_data"
    db_user: str = "postgres"
    db_password: str = ""
    
    # Application Settings
    log_level: str = "INFO"
    sync_days_back: int = 90
    
    # Webhook Settings (optional)
    webhook_url: Optional[str] = None
    webhook_verification_token: Optional[str] = None
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @property
    def database_url_constructed(self) -> str:
        """Construct database URL from components if not provided directly."""
        if self.database_url:
            return self.database_url
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )
    
    @property
    def oauth_scopes(self) -> list[str]:
        """Return all available OAuth scopes for Oura API."""
        return [
            "email",
            "personal",
            "daily",
            "heartrate",
            "workout",
            "tag",
            "session",
            "spo2"
        ]


# Global settings instance
settings = Settings()


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


def get_data_dir() -> Path:
    """Get the data directory for storing files."""
    data_dir = get_project_root() / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir


def get_logs_dir() -> Path:
    """Get the logs directory."""
    logs_dir = get_project_root() / "logs"
    logs_dir.mkdir(exist_ok=True)
    return logs_dir