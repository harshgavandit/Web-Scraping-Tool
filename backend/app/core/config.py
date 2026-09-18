import os
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Brand Chatter & Social Listening"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"

    # Database
    DATABASE_URL: str = "sqlite:///./brand_chatter.db"

    # Gemini is the only semantic analysis provider.
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash"
    AI_ANALYSIS_ENABLED: bool = True
    AI_BATCH_SIZE: int = 20

    # Reddit Collector
    REDDIT_ENABLED: bool = False
    REDDIT_CLIENT_ID: str = ""
    REDDIT_CLIENT_SECRET: str = ""
    REDDIT_USER_AGENT: str = "BrandChatterBot/1.0"

    # Facebook Collector
    FACEBOOK_ENABLED: bool = False
    FACEBOOK_ACCESS_TOKEN: str = ""

    # Web & RSS Collector
    RSS_ENABLED: bool = True
    PUBLISHER_RSS_ENABLED: bool = True
    # Optional newline-separated entries: "Publisher name|https://publisher.example/feed".
    # An empty value uses the curated Nike publisher feed allowlist.
    PUBLISHER_RSS_FEEDS: str = ""
    GOOGLE_SEARCH_ENABLED: bool = False
    GOOGLE_SEARCH_API_KEY: str = ""
    GOOGLE_SEARCH_ENGINE_ID: str = ""
    GOOGLE_SEARCH_ENDPOINT: str = "https://customsearch.googleapis.com/customsearch/v1"
    GOOGLE_SEARCH_COUNTRY: str = "US"
    GOOGLE_SEARCH_LANGUAGE: str = "en"
    PAGE_FETCH_ENABLED: bool = True
    PAGE_FETCH_LIMIT_PER_RUN: int = 30

    # Scheduler & Pipeline
    COLLECTION_INTERVAL_MINUTES: int = 60
    VIRAL_THRESHOLD: int = 85

    # Enterprise email alerts (disabled until explicitly configured)
    EMAIL_ALERTS_ENABLED: bool = False
    EMAIL_ALERT_RECIPIENTS: str = ""
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_USE_TLS: bool = True
    APP_PUBLIC_URL: str = "http://localhost:5173"

    # CORS & Network
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def assemble_database_url(cls, v: str) -> str:
        if v.startswith("sqlite:///") and ":memory:" not in v:
            rel_path = v.replace("sqlite:///", "")
            if not os.path.isabs(rel_path):
                # Resolve relative to root workspace directory (parent of backend)
                base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
                db_file = os.path.normpath(os.path.join(base_dir, rel_path.lstrip("./")))
                return f"sqlite:///{db_file}"
        return v

    @field_validator("CORS_ORIGINS", mode="after")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
