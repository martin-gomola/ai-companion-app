from pathlib import Path

import pytest

from yourturn.config import CONFIG_PATH, DEFAULT_HISTORY_DAYS, load_history_days


def test_default_and_configured_history(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    assert load_history_days(path) == DEFAULT_HISTORY_DAYS
    path.write_text("history_days = 7\n")
    assert load_history_days(path) == 7


@pytest.mark.parametrize("value", ["0", "-1", "true", '"seven"', "1.5", "["])
def test_rejects_invalid_history(tmp_path: Path, value: str) -> None:
    path = tmp_path / "config.toml"
    path.write_text(f"history_days = {value}\n")
    with pytest.raises(ValueError):
        load_history_days(path)


def test_checkout_config_does_not_depend_on_working_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert CONFIG_PATH == Path(__file__).resolve().parents[1] / "config.toml"
    assert load_history_days() > 0
