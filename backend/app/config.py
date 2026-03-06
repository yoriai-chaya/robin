from functools import lru_cache
from pathlib import Path

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    openai_max_turns: int = 6

    log_dir: Path = BASE_DIR / "log"
    output_dir: Path = BASE_DIR / "output"
    test_results_dir: str = "results"
    archive_dir: Path = BASE_DIR / "archive"
    prompts_dir: Path = BASE_DIR / "prompts"

    playwright_customconfig_file: str = "playwright.customconfig.json"
    build_customconfig_file: str = "build.customconfig.json"
    agents_prompt_file: str = "agents.yml"

    code_gen_retry: int = 5
    rebuild_retry: int = 3

    debug: bool = False
    log_filename: str = "yoriai.log"
    log_level: str = "AGENT"

    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env")


@lru_cache
def get_settings():
    return Settings()
