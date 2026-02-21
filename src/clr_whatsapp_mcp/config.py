"""Configuration for WhatsApp MCP Server.

Standard credential loading pattern for Clearminds MCP servers:
1. Load from environment variables (WHATSAPP_*) as base/fallback
2. Override with ~/.config/whatsapp/credentials.json (takes priority)

Config file is the primary source for local development.
Env vars can override for CI/CD, Docker, or quick testing.
"""

import json
import logging
import logging.config
from pathlib import Path
from typing import Any, Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

CREDS_PATH = Path.home() / ".config" / "whatsapp" / "credentials.json"


class Settings(BaseSettings):
    """Settings loaded from credentials.json or environment variables.

    Priority order:
    1. Environment variables (WHATSAPP_BRIDGE_URL, WHATSAPP_SUPABASE_URL, etc.) - base
    2. ~/.config/whatsapp/credentials.json - override (takes priority)
    """

    whatsapp_bridge_url: str = "http://localhost:8080"
    whatsapp_supabase_url: str = ""
    whatsapp_supabase_key: str = ""

    whatsapp_read_only: bool = False

    whatsapp_transport: str = "stdio"
    whatsapp_log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    def load_credentials(self) -> dict[str, Any]:
        """Load credentials with env-first, config-file-override pattern.

        Returns:
            Dict with bridge_url, supabase_url, and supabase_key.
        """
        creds: dict[str, Any] = {}

        # 1. FIRST: Load from environment variables (base/fallback)
        if self.whatsapp_bridge_url:
            creds["bridge_url"] = self.whatsapp_bridge_url
        if self.whatsapp_supabase_url:
            creds["supabase_url"] = self.whatsapp_supabase_url
        if self.whatsapp_supabase_key:
            creds["supabase_key"] = self.whatsapp_supabase_key

        # 2. THEN: Override with credentials.json file (takes priority)
        if CREDS_PATH.exists():
            try:
                file_creds: dict[str, Any] = json.loads(CREDS_PATH.read_text())

                if "bridge_url" in file_creds:
                    creds["bridge_url"] = file_creds["bridge_url"]
                if "supabase_url" in file_creds:
                    creds["supabase_url"] = file_creds["supabase_url"]
                if "supabase_key" in file_creds:
                    creds["supabase_key"] = file_creds["supabase_key"]

                logger.info("Loaded WhatsApp credentials from %s", CREDS_PATH)
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning("Failed to load %s: %s", CREDS_PATH, e)

        # Ensure bridge_url has a default
        if not creds.get("bridge_url"):
            creds["bridge_url"] = "http://localhost:8080"

        if not self._has_required_creds(creds):
            logger.warning(
                "Missing Supabase credentials. Set WHATSAPP_SUPABASE_URL/WHATSAPP_SUPABASE_KEY "
                "env vars or create %s",
                CREDS_PATH,
            )

        return creds

    def _has_required_creds(self, creds: dict[str, Any]) -> bool:
        """Check if minimum required credentials are present."""
        return bool(creds.get("supabase_url") and creds.get("supabase_key"))


def configure_logging(
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
) -> None:
    """Configure structured logging to stderr."""
    config: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "console": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "console",
                "stream": "ext://sys.stderr",
            },
        },
        "loggers": {
            "httpx": {
                "level": "WARNING" if log_level != "DEBUG" else "DEBUG",
            },
            "httpcore": {
                "level": "WARNING",
            },
        },
        "root": {
            "level": log_level,
            "handlers": ["console"],
        },
    }
    logging.config.dictConfig(config)


# Example credentials.json format:
"""
{
  "bridge_url": "http://localhost:8080",
  "supabase_url": "https://your-project.supabase.co",
  "supabase_key": "your-supabase-anon-key"
}
"""
