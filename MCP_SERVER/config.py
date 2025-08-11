
import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field
import logging

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Server Configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    debug: bool = Field(default=False, env="DEBUG")
    reload: bool = Field(default=False, env="RELOAD")

    # API Configuration
    title: str = "MCP FastAPI Server"
    description: str = "Scalable FastAPI server for handling MCP (Model Control Protocol) requests"
    version: str = "1.0.0"

    # Security
    api_key_salt: str = Field(default="default-salt-change-in-production", env="API_KEY_SALT")

    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    redis_db: int = Field(default=0, env="REDIS_DB")

    # Rate Limiting
    default_rate_limit: int = Field(default=60, env="DEFAULT_RATE_LIMIT")
    rate_limit_window: int = Field(default=60, env="RATE_LIMIT_WINDOW")

    # CORS Configuration
    cors_origins: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    cors_credentials: bool = Field(default=True, env="CORS_CREDENTIALS")

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="text", env="LOG_FORMAT")  # text or json

    # Model Configuration
    default_max_tokens: int = Field(default=2048, env="DEFAULT_MAX_TOKENS")
    default_temperature: float = Field(default=0.7, env="DEFAULT_TEMPERATURE")

    # Features
    security_headers_enabled: bool = Field(default=True, env="SECURITY_HEADERS_ENABLED")
    metrics_enabled: bool = Field(default=False, env="METRICS_ENABLED")
    health_check_enabled: bool = Field(default=True, env="HEALTH_CHECK_ENABLED")

    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()

def setup_logging():
    """Configure logging based on settings."""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    if settings.log_format.lower() == "json":
        # JSON logging format for production
        import json
        import datetime

        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_entry = {
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                    "module": record.module,
                    "function": record.funcName,
                    "line": record.lineno
                }

                if record.exc_info:
                    log_entry["exception"] = self.formatException(record.exc_info)

                return json.dumps(log_entry)

        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
    else:
        # Text logging format for development
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Configure specific loggers
    logging.getLogger("uvicorn").setLevel(log_level)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("mcp_server").setLevel(log_level)

def get_redis_config() -> dict:
    """Get Redis configuration dictionary."""
    config = {
        "url": settings.redis_url,
        "db": settings.redis_db,
        "decode_responses": True,
        "encoding": "utf-8"
    }

    if settings.redis_password:
        config["password"] = settings.redis_password

    return config

def validate_settings():
    """Validate critical settings."""
    errors = []

    # Validate port
    if not (1 <= settings.port <= 65535):
        errors.append(f"Invalid port number: {settings.port}")

    # Validate log level
    valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if settings.log_level.upper() not in valid_log_levels:
        errors.append(f"Invalid log level: {settings.log_level}")

    # Validate rate limit settings
    if settings.default_rate_limit <= 0:
        errors.append(f"Rate limit must be positive: {settings.default_rate_limit}")

    if settings.rate_limit_window <= 0:
        errors.append(f"Rate limit window must be positive: {settings.rate_limit_window}")

    # Validate model settings
    if settings.default_max_tokens <= 0:
        errors.append(f"Max tokens must be positive: {settings.default_max_tokens}")

    if not (0.0 <= settings.default_temperature <= 2.0):
        errors.append(f"Temperature must be between 0.0 and 2.0: {settings.default_temperature}")

    if errors:
        error_msg = "\n".join(errors)
        raise ValueError(f"Configuration validation failed:\n{error_msg}")

# Validate settings on import
validate_settings()
