"""إعدادات التطبيق — كل القيم من متغيرات البيئة (تعمل دون إنترنت)."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://intel:intel_strong_change_me@db:5432/inteldb"
    MEILI_HOST: str = "http://meilisearch:7700"
    MEILI_MASTER_KEY: str = "meili_master_change_me_32chars"
    API_TOKEN: str = "dev_token_change_me"
    UPLOAD_DIR: str = "/uploads"
    MAX_UPLOAD_MB: int = 100


settings = Settings()
