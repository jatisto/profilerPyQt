"""
Application Configuration Module

Centralized configuration management using Pydantic for type safety.
Supports environment variables and .env files.
"""

from pathlib import Path
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    """Main application configuration."""

    model_config = SettingsConfigDict(
        env_prefix="DB_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application metadata
    app_name: str = "PostgreSQL Statistics Statements Reader"
    app_short_name: str = "PgSSR"
    app_version: str = "2.0.0"
    app_author: str = "Your Name"
    app_license: str = "MIT"

    # Directories
    base_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent)
    logs_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "Logs")
    themes_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "themes")
    icons_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "icons")
    locales_dir: Path = Field(default_factory=lambda: Path(__file__).parent / "locales")

    # Security
    encryption_key_name: str = "pgssr_master_key"
    use_system_keyring: bool = True

    # Database
    db_pool_min_size: int = Field(default=1, ge=1)
    db_pool_max_size: int = Field(default=10, ge=1)
    db_connection_timeout: int = Field(default=30, ge=5)
    db_query_timeout: int = Field(default=60, ge=10)

    # UI Settings
    default_theme: str = "dark"
    default_language: str = "ru"
    window_width: int = Field(default=1400, ge=800)
    window_height: int = Field(default=900, ge=600)
    use_custom_titlebar: bool = False

    # Logging
    log_level: str = Field(default="INFO")
    log_rotation: str = "10 MB"
    log_retention: str = "30 days"
    log_format: str = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}"

    # Update settings
    check_updates_on_startup: bool = False
    github_repo_owner: str = "your-username"
    github_repo_name: str = "profilerPyQt"

    # Performance
    enable_query_cache: bool = True
    cache_ttl_seconds: int = 300
    max_table_rows: int = 10000

    @field_validator("logs_dir", "themes_dir", "icons_dir", "locales_dir")
    @classmethod
    def create_directory_if_not_exists(cls, v: Path) -> Path:
        """Ensure directory exists."""
        v.mkdir(parents=True, exist_ok=True)
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level. Must be one of: {valid_levels}")
        return v_upper


class DatabaseDefaultConfig(BaseSettings):
    """Default database connection configuration."""

    model_config = SettingsConfigDict(
        env_prefix="DB_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    host: str = "localhost"
    port: int = Field(default=5432, ge=1, le=65535)
    database: str = "postgres"
    user: str = "postgres"
    password: Optional[str] = None
    ssl_mode: str = "prefer"

    @field_validator("ssl_mode")
    @classmethod
    def validate_ssl_mode(cls, v: str) -> str:
        """Validate SSL mode."""
        valid_modes = ["disable", "allow", "prefer", "require", "verify-ca", "verify-full"]
        if v not in valid_modes:
            raise ValueError(f"Invalid SSL mode. Must be one of: {valid_modes}")
        return v


# Global configuration instances
app_config = AppConfig()
db_default_config = DatabaseDefaultConfig()


def get_app_config() -> AppConfig:
    """Get application configuration instance."""
    return app_config


def get_db_default_config() -> DatabaseDefaultConfig:
    """Get default database configuration instance."""
    return db_default_config
