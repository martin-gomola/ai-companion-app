"""Local dashboard configuration, loaded when the server starts."""

from pathlib import Path
import tomllib

DEFAULT_HISTORY_DAYS = 14
CONFIG_PATH = Path(__file__).resolve().parents[2] / "config.toml"


def load_history_days(path: Path = CONFIG_PATH) -> int:
    if not path.exists():
        return DEFAULT_HISTORY_DAYS
    with path.open("rb") as handle:
        days = tomllib.load(handle).get("history_days", DEFAULT_HISTORY_DAYS)
    if type(days) is not int or days < 1:
        raise ValueError("history_days must be a positive integer")
    return days
