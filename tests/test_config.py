import pytest
from pydantic import ValidationError

from story_finder.config import Settings

_REQUIRED = {"TELEGRAM_BOT_TOKEN": "token", "TELEGRAM_OWNER_ID": "12345"}


def _env(monkeypatch, **overrides):
    values = {**_REQUIRED, **overrides}
    for key in values:
        monkeypatch.delenv(key, raising=False)
    for key, value in values.items():
        if value is not None:
            monkeypatch.setenv(key, value)


def test_settings_load_from_environment(monkeypatch):
    _env(monkeypatch)
    settings = Settings(_env_file=None)
    assert settings.telegram_owner_id == 12345
    assert settings.telegram_bot_token == "token"


def test_missing_required_setting_is_a_validation_error(monkeypatch):
    _env(monkeypatch, TELEGRAM_BOT_TOKEN=None)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_owner_id_must_be_an_integer(monkeypatch):
    _env(monkeypatch, TELEGRAM_OWNER_ID="not-a-number")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_unrelated_environment_variables_are_ignored(monkeypatch):
    _env(monkeypatch)
    monkeypatch.setenv("REDDIT_CLIENT_ID", "set-by-the-wizard-ahead-of-time")
    Settings(_env_file=None)
