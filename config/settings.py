"""Typed settings read from environment variables.

The code reads ONLY environment variables. Where they come from depends on
where the bot runs:
- Local: the .env file (loaded here, never committed).
- Azure DevOps: Variable Groups linked to Azure Key Vault, mapped to env vars.
- Airflow: Connections/Variables passed to the process as env vars.

Real environment variables always win over values in .env.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ENV_FILE = PROJECT_ROOT / ".env"
SUPPORTED_ENGINES = ("selenium", "playwright")
TRUE_VALUES = ("true", "1", "yes")
FALSE_VALUES = ("false", "0", "no")


@dataclass(frozen=True)
class Settings:
    process_name: str
    engine: str
    headless: bool
    base_url: str
    timeout_seconds: float
    max_retries: int
    username: str
    password: str = field(repr=False)
    logs_dir: Path = PROJECT_ROOT / "logs"
    evidence_dir: Path = PROJECT_ROOT / "evidence"
    input_dir: Path = PROJECT_ROOT / "data" / "input"
    output_dir: Path = PROJECT_ROOT / "data" / "output"


def load_settings(env_file: Path | None = DEFAULT_ENV_FILE) -> Settings:
    """Load .env (if present) and build the settings. Fails fast on bad values."""
    if env_file is not None and env_file.exists():
        load_dotenv(env_file, override=False)

    engine = os.environ.get("RPA_ENGINE", "selenium").strip().lower()
    if engine not in SUPPORTED_ENGINES:
        raise ValueError(f"RPA_ENGINE must be one of {SUPPORTED_ENGINES}, got '{engine}'")

    max_retries = _read_int("RPA_MAX_RETRIES", default=3)
    if max_retries < 1:
        raise ValueError("RPA_MAX_RETRIES must be at least 1")

    return Settings(
        process_name=_read_required("RPA_PROCESS_NAME"),
        engine=engine,
        headless=_read_bool("RPA_HEADLESS", default=True),
        base_url=_read_required("RPA_BASE_URL"),
        timeout_seconds=float(_read_int("RPA_TIMEOUT_SECONDS", default=30)),
        max_retries=max_retries,
        username=_read_required("RPA_USERNAME"),
        password=_read_required("RPA_PASSWORD"),
    )


def _read_required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable {name}. See .env.example")
    return value


def _read_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None or not value.strip():
        return default
    normalized = value.strip().lower()
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    raise ValueError(f"{name} must be true or false, got '{value}'")


def _read_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None or not value.strip():
        return default
    try:
        return int(value)
    except ValueError as error:
        raise ValueError(f"{name} must be an integer, got '{value}'") from error
