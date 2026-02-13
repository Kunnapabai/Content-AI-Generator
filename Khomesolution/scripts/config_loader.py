"""
Shared configuration loader for Khomesolution scripts.

Reads config.yaml from the project root and provides per-task
OpenRouter parameters via get_model_config() and get_openrouter_config().
Reads prompt markdown files from PROMPTS/ via load_prompt().

Usage:
    from config_loader import get_openrouter_config, get_model_config, load_prompt

    openrouter = get_openrouter_config()       # api_key, api_url, http_referer
    cfg        = get_model_config("title_analysis")  # model, temperature, ...
    prompt     = load_prompt("title_analysis_system.md")  # raw string
"""

import yaml
from pathlib import Path
from typing import Any, Dict

# Resolve project root (one level up from scripts/)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_CONFIG_PATH = _PROJECT_ROOT / "config.yaml"
_PROMPTS_DIR = _PROJECT_ROOT / "PROMPTS"

_config_cache: Dict[str, Any] | None = None


def _load_config() -> Dict[str, Any]:
    """Load and cache config.yaml."""
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    if not _CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"config.yaml not found at {_CONFIG_PATH}. "
            "Please create it in the project root."
        )

    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        _config_cache = yaml.safe_load(f)

    return _config_cache


def get_openrouter_config() -> Dict[str, str]:
    """Return the shared OpenRouter connection settings.

    Returns dict with keys: api_key, api_url, http_referer
    """
    cfg = _load_config()
    return cfg["openrouter"]


def get_model_config(task_name: str) -> Dict[str, Any]:
    """Return model parameters for a specific task.

    Args:
        task_name: Key under 'models' in config.yaml, e.g.
                   "title_analysis", "outline_generation", etc.

    Returns dict with keys like: model, temperature, max_tokens, ...
    """
    cfg = _load_config()
    models = cfg.get("models", {})
    if task_name not in models:
        raise KeyError(
            f"No model config found for '{task_name}'. "
            f"Available tasks: {list(models.keys())}"
        )
    return models[task_name]


_prompt_cache: Dict[str, str] = {}


def load_prompt(filename: str) -> str:
    """Load a prompt template from the PROMPTS directory.

    Args:
        filename: Name of the .md file inside PROMPTS/,
                  e.g. "title_analysis_system.md"

    Returns the file contents as a UTF-8 string.
    """
    if filename in _prompt_cache:
        return _prompt_cache[filename]

    prompt_path = _PROMPTS_DIR / filename
    if not prompt_path.exists():
        raise FileNotFoundError(
            f"Prompt file not found: {prompt_path}. "
            f"Available files: {[f.name for f in _PROMPTS_DIR.glob('*.md')]}"
        )

    with open(prompt_path, "r", encoding="utf-8") as f:
        content = f.read()

    _prompt_cache[filename] = content
    return content
