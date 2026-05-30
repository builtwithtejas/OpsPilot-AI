from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str    = "OpsPilot AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool      = False
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Auth
    API_KEY: str = "change-this-secret-api-key"

    # ── Google Cloud / Gemini (hackathon required) ──────────────────
    GEMINI_API_KEY:        str = ""   # from Google AI Studio
    GOOGLE_CLOUD_PROJECT:  str = ""   # your GCP project ID
    GOOGLE_CLOUD_LOCATION: str = "us-central1"

    # ── GitHub ──────────────────────────────────────────────────────
    GITHUB_TOKEN:          str = ""
    GITHUB_REPO:           str = "builtwithtejas/OpsPilot-AI"
    GITHUB_WEBHOOK_SECRET: str = ""

    # ── GitLab MCP ─────────────────────────────────────────────────
    GITLAB_TOKEN:    str = ""   # GitLab Personal Access Token
    GITLAB_BASE_URL: str = "https://gitlab.com"

    # ── Notifications ───────────────────────────────────────────────
    SLACK_WEBHOOK_URL: str = ""
    SENDGRID_API_KEY:  str = ""
    ALERT_EMAIL_TO:    str = ""
    ALERT_EMAIL_FROM:  str = "alerts@opspilot.ai"
    FRONTEND_URL:      str = "http://localhost:3000"

    # ── Groq (kept for streaming chat fallback) ─────────────────────
    GROQ_API_KEY: str = ""

    # ── Database ────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite:///./opspilot.db"

    # ── CORS ────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    # ── Uploads ────────────────────────────────────────────────────
    MAX_UPLOAD_SIZE_MB: int = 10

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
