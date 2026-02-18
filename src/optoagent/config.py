"""
Centralized configuration management for OptoAgent.

Loads config.yaml for business settings and .env for secrets (API keys).
"""

import os
import yaml
from dotenv import load_dotenv

# Load .env once at import time
load_dotenv()

# ---------------------------------------------------------------------------
# Locate config.yaml — walk up from this file until we find the project root
# ---------------------------------------------------------------------------

def _find_project_root() -> str:
    """Find the project root directory containing config.yaml."""
    current = os.path.dirname(os.path.abspath(__file__))
    for _ in range(5):  # at most 5 levels up
        candidate = os.path.join(current, "config.yaml")
        if os.path.exists(candidate):
            return current
        current = os.path.dirname(current)
    # Fallback: current working directory
    return os.getcwd()


PROJECT_ROOT = _find_project_root()

# ---------------------------------------------------------------------------
# Load YAML config
# ---------------------------------------------------------------------------

def _load_yaml_config() -> dict:
    config_path = os.path.join(PROJECT_ROOT, "config.yaml")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


_cfg = _load_yaml_config()

# ---------------------------------------------------------------------------
# App settings
# ---------------------------------------------------------------------------

APP_NAME: str = _cfg.get("app", {}).get("name", "OptoAgent")
APP_VERSION: str = _cfg.get("app", {}).get("version", "1.0.0")
LOG_LEVEL: str = _cfg.get("app", {}).get("log_level", "INFO")
DATA_DIR: str = os.path.join(PROJECT_ROOT, _cfg.get("app", {}).get("data_dir", "data"))
LOGS_DIR: str = os.path.join(PROJECT_ROOT, _cfg.get("app", {}).get("logs_dir", "logs"))

# ---------------------------------------------------------------------------
# API keys (from .env)
# ---------------------------------------------------------------------------

EXA_API_KEY: str | None = os.getenv("EXA_API_KEY")
OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL: str | None = os.getenv("OPENAI_BASE_URL")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
FEISHU_WEBHOOK: str | None = os.getenv("FEISHU_WEBHOOK")
APP_ID: str | None = os.getenv("APP_ID")
APP_SECRET: str | None = os.getenv("APP_SECRET")

# ---------------------------------------------------------------------------
# Search settings
# ---------------------------------------------------------------------------

_search_cfg = _cfg.get("search", {})
DEFAULT_QUERY: str = _search_cfg.get(
    "default_query",
    "miniaturized spectrometer OR spectral imaging OR 2D material optoelectronics",
)
DEFAULT_LIMIT: int = _search_cfg.get("default_limit", 5)
SEARCH_DAYS_BACK: int = _search_cfg.get("days_back", 30)
ACADEMIC_DOMAINS: list[str] = _search_cfg.get("academic_domains", [])

# ---------------------------------------------------------------------------
# Scheduler settings
# ---------------------------------------------------------------------------

_sched_cfg = _cfg.get("scheduler", {})
SCHEDULER_INTERVAL: int = _sched_cfg.get("interval", 6)
SCHEDULER_UNIT: str = _sched_cfg.get("unit", "hours")

# ---------------------------------------------------------------------------
# Tracking sources
# ---------------------------------------------------------------------------

_tracking_cfg = _cfg.get("tracking", {})
RSS_FEEDS: list[str] = _tracking_cfg.get("rss_feeds", [])
RESEARCH_GROUPS: list[dict] = _tracking_cfg.get("research_groups", [])

# ---------------------------------------------------------------------------
# Target journals
# ---------------------------------------------------------------------------

TARGET_JOURNALS: list[str] = _cfg.get("journals", {}).get("target_journals", [])
