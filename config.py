"""
Configuração de chaves de API e seleção de provedor.
"""

import json
import os
from pathlib import Path

CONFIG_FILE = Path(__file__).resolve().parent / "user_config.json"

# Defaults — overridden by user_config.json or env vars
GEMINI_API_KEY = ""
GROQ_API_KEY = ""
PROVIDER = "gemini"  # "gemini" or "groq"


def load_config() -> dict:
    cfg = {"gemini_api_key": "", "groq_api_key": "", "provider": "gemini"}
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except Exception:
            pass
    cfg["gemini_api_key"] = os.environ.get("GEMINI_API_KEY", cfg["gemini_api_key"])
    cfg["groq_api_key"] = os.environ.get("GROQ_API_KEY", cfg["groq_api_key"])
    cfg["provider"] = os.environ.get("LLM_PROVIDER", cfg["provider"])
    return cfg


def save_config(gemini_key: str, groq_key: str, provider: str):
    data = {
        "gemini_api_key": gemini_key,
        "groq_api_key": groq_key,
        "provider": provider,
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_active_key(cfg: dict | None = None) -> tuple[str, str]:
    """Returns (provider, api_key) for the active provider."""
    if cfg is None:
        cfg = load_config()
    provider = cfg["provider"]
    if provider == "groq":
        return "groq", cfg["groq_api_key"]
    return "gemini", cfg["gemini_api_key"]
