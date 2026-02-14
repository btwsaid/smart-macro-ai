"""Configuration management for SmartMacro AI Bot."""

import os
import logging
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration."""

    def __init__(self):
        """Initialize configuration from environment variables."""
        self.telegram_bot_token: str = self._get_required_env("TELEGRAM_BOT_TOKEN")
        self.openai_api_key: str = self._get_required_env("OPENAI_API_KEY")
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        self.openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o")
        self.max_tokens: int = int(os.getenv("MAX_TOKENS", "500"))
        self.database_path: str = os.getenv("DATABASE_PATH", "data/nutrition.db")

        # Setup logging
        self._setup_logging()

    def _get_required_env(self, key: str) -> str:
        """Get required environment variable or raise error.

        Args:
            key: Environment variable name

        Returns:
            Environment variable value

        Raises:
            ValueError: If environment variable is not set
        """
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable {key} is not set")
        return value

    def _setup_logging(self) -> None:
        """Configure logging for the application."""
        logging.basicConfig(
            level=getattr(logging, self.log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )


# Global config instance
config = Config()
