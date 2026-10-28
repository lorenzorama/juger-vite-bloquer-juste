import os
from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")

    anthropic_api_key: SecretStr | None = None
    typesafe_api_key: SecretStr | None = None
    agent_model: str = "anthropic:claude-haiku-5-5"
    typesafe_default_model: str = "jev-1.14.0"  # épingler une version, jamais jev-latest

    jev_ing_quarantine: float = 0.70
    jev_ing_suspect: float = 0.35
    jev_egr_allow_req: float = 0.75
    jev_egr_block_leak: float = 0.50
    jev_egr_block_req: float = 0.30
    jev_timeout_s: float = 2.0
    max_drafts_per_run: int = 3


@lru_cache
def get_settings() -> Settings:
    os.environ["LANGSMITH_TRACING"] = "false"
    return Settings()
