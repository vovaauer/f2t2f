import json
from pathlib import Path
from platformdirs import user_config_dir

APP_NAME = "f2t2f"
APP_AUTHOR = "vovaauer"
CONFIG_FILENAME = "config.json"

DEFAULT_IGNORE_PATTERNS = [
    "__pycache__",
    "*.egg-info",
    ".git",
    ".gitignore",
    ".vscode",
    "build",
    "dist",
    ".DS_Store"
]

def get_config_path() -> Path:
    """Gets the path to the config file, ensuring the directory exists."""
    config_dir = Path(user_config_dir(APP_NAME, APP_AUTHOR))
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / CONFIG_FILENAME

def load_config() -> dict:
    """
    Loads the user's config file. If it doesn't exist or is invalid,
    returns the default configuration.
    """
    config_path = get_config_path()
    if not config_path.exists():
        return {"ignore_patterns": DEFAULT_IGNORE_PATTERNS}

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            user_config = json.load(f)
        if "ignore_patterns" not in user_config:
             user_config["ignore_patterns"] = DEFAULT_IGNORE_PATTERNS
        return user_config
    except (json.JSONDecodeError, IOError):
        return {"ignore_patterns": DEFAULT_IGNORE_PATTERNS}

def save_default_config() -> Path:
    """Saves a default config file for the user to edit."""
    config_path = get_config_path()
    default_config = {"ignore_patterns": DEFAULT_IGNORE_PATTERNS}
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(default_config, f, indent=2)
    return config_path