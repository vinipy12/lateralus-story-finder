from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, validated at startup.

    A missing or malformed value raises here rather than surfacing as a mystery
    failure on the first command. Unknown variables are ignored, so credentials
    captured ahead of time for later slices do not break startup now.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    telegram_bot_token: str
    telegram_owner_id: int
