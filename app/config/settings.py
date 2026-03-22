from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    APP_NAME: str = "CardCraft API"
    DEBUG: bool = False

    OPENAI_API_KEY: str
    IDEOGRAM_API_KEY: str        # ← ADD THIS

    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_ANON_KEY: str

    PDF_OUTPUT_DIR: str = "/tmp/cardcraft_pdfs"
    SUPABASE_STORAGE_BUCKET: str = "card-pdfs"

    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()