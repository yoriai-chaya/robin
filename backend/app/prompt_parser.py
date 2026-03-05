import re
from pathlib import Path
from typing import Optional

import yaml

from app.base import LocalContext
from app.config import get_settings
from app.logger import logger

DIR_AGENTS = "agents"


def resolve_placeholders(prompt: str, context: LocalContext) -> str:
    logger.debug(f"resolve_placeholders called. prompt:{prompt}")

    def replacer(match):
        logger.debug(f"replacer called. match:{match}")
        file_path = match.group(1).strip()
        logger.debug(f"file_path: {file_path}")
        full_path = context.output_dir / file_path
        logger.debug(f"full_path: {full_path}")
        try:
            content = Path(str(full_path)).read_text(encoding="utf-8")
            return f"[{file_path}]\n```{Path(file_path).suffix.lstrip('.')}\n{content}\n```"
        except FileNotFoundError as e:
            raise e

    filled = re.sub(r"\{\{file:(.+?)\}\}", replacer, prompt)
    return filled


def extract_header_section(prompt: str) -> str:
    """
    Extracts the range from # Header to # Body from the entire prompt.
    """
    header_pattern = re.compile(
        r"#\s*Header(.*?)(?=#\s*Body|$)", re.DOTALL | re.IGNORECASE
    )
    match = header_pattern.search(prompt)
    return match.group(1).strip() if match else ""


def parse_header_fields(header_text: str) -> dict[str, str]:
    """
    Converts the header section into a dictionary in key:value format.
    - "Key:Value" format
    "Key:Value" format
    Both are supported.
    """
    fields: dict[str, str] = {}
    for line in header_text.splitlines():
        line = line.strip("- ").strip()
        if not line:
            continue
        match = re.match(r"(\w+)\s*:\s*(.+)", line)
        if match:
            key, value = match.groups()
            fields[key.strip()] = value.strip()
    return fields


def extract_from_prompt(prompt: str, key: str) -> Optional[str]:
    """
    Extracts the value of the specified key from the header section.
    """
    header_text = extract_header_section(prompt)
    fields = parse_header_fields(header_text)
    return fields.get(key)


def parse_build_check(value: Optional[str]) -> bool:
    """
    Convert BuildCheck header value to bool.
    Returns:
        True  : "on"
        False : "off" or not specified
    """
    if value is None:
        return False

    v = value.strip().lower()
    if v == "on":
        return True
    if v == "off":
        return False
    return False


def load_agents_prompt() -> dict:
    logger.debug("load_agents_prompt called")
    settings = get_settings()
    agents_prompt_file = settings.agents_prompt_file
    base = Path().resolve()
    prompts_dir = settings.prompts_dir
    logger.debug(f"prompts_dir: {prompts_dir}")
    logger.debug(f"base: {base}")
    path = base / prompts_dir / DIR_AGENTS / agents_prompt_file
    logger.debug(f"path: {path}")

    try:
        with path.open() as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML format: {path}")
        raise ValueError(f"Invalid YAML format: {path}") from e

    if data is None:
        raise ValueError(f"YAML file is empty: {path}")

    if not isinstance(data, dict):
        raise ValueError(
            f"YAML root must be mapping(dict): {path}, actual={type(data)}"
        )
    logger.debug("load_agents_prompt return")
    return data


def require_str(data: dict, key: str) -> str:
    logger.debug("require_str called")
    if key not in data:
        raise KeyError(
            f"Invalid agents prompt YAML configuration: "
            f"required key '{key}' is not defined. "
            f"Please add  '{key}' to the YAML file. "
            f"your defined keys={list(data.keys())}"
        )
    value = data[key]
    if not isinstance(value, str):
        raise TypeError(
            f"Invalid type for '{key}' in YAML, "
            f"expected=str, actual={type(value).__name__}"
        )
    logger.debug("require_str return")
    return value
