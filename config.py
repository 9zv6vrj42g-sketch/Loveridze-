"""
All configurable values live in .env — nothing here is hardcoded.
Copy .env.example to .env and fill it in (Railway: set these as service Variables).
"""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Bot / access ---
    BOT_TOKEN: str
    ADMIN_IDS: str = ""
    MODERATOR_CHAT_ID: int
    CHANNEL_ID: int
    CHANNEL_LINK: str = ""
    GROUP_ID: int
    GROUP_LINK: str = ""

    # --- Social links ---
    TIKTOK_MAIN_LINK: str = ""
    TIKTOK_FAN_LINK: str = ""
    INSTAGRAM_LINK: str = ""
    YOUTUBE_LINK: str = ""
    THREADS_LINK: str = ""
    X_LINK: str = ""
    ADULT_LINK: str = ""
    STICKERPACK_LINK: str = "https://t.me/addstickers/Lavrelin"

    # --- Database ---
    DATABASE_URL: str = ""

    # --- Behaviour ---
    SUGGESTION_COOLDOWN_MINUTES: int = 120
    TIMEZONE: str = "Europe/Moscow"

    @property
    def admin_ids(self) -> set[int]:
        return {int(x) for x in self.ADMIN_IDS.split(",") if x.strip()}

    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return "sqlite+aiosqlite:///bot.db"


settings = Settings()
