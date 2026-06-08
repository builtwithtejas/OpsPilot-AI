# backend/app/core/config.py
# FIX: Added MAX_LOG_CHARS setting so log truncation is configurable via .env

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str    = "OpsPilot AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool      = False
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Auth
    API_KEY: str = ""

    # ── Google Cloud / Gemini ───────────────────────────────────────
    GEMINI_API_KEY:        str = ""
    GOOGLE_CLOUD_PROJECT:  str = ""
    GOOGLE_CLOUD_LOCATION: str = "us-central1"

    # ── GitHub ──────────────────────────────────────────────────────
    GITHUB_TOKEN:          str = ""
    GITHUB_REPO:           str = "builtwithtejas/OpsPilot-AI"
    GITHUB_WEBHOOK_SECRET: str = ""

    # ── GitLab MCP ─────────────────────────────────────────────────
    GITLAB_TOKEN:    str = ""
    GITLAB_BASE_URL: str = "https://gitlab.com"
    GITLAB_AGENT_ID:  str = "1009889"
    GITLAB_MCP_URL:   str = "https://gitlab.com/api/v4/ai/agents/1009889/mcp"
    GITLAB_GROUP:     str = "opspilot-ai-hackathon"
    GITLAB_WEBHOOK_SECRET: str = ""

    # ── Notifications ───────────────────────────────────────────────
    SLACK_WEBHOOK_URL: str = ""
    SENDGRID_API_KEY:  str = ""
    ALERT_EMAIL_TO:    str = ""
    ALERT_EMAIL_FROM:  str = "alerts@opspilot.ai"
    FRONTEND_URL:      str = "http://localhost:3000"

    # ── Database ────────────────────────────────────────────────────
    DATABASE_URL: str = ""

    # ── CORS ────────────────────────────────────────────────────────
    # Comma-separated list of allowed origins.
    # Example in .env:
    #   ALLOWED_ORIGINS=https://your-app.vercel.app,http://localhost:3000
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    # ── Uploads ─────────────────────────────────────────────────────
    MAX_UPLOAD_SIZE_MB: int = 10

    # ── AI Log Analysis ─────────────────────────────────────────────
    # FIX: Configurable log truncation limit (characters sent to Gemini).
    # Increase this if you need deeper log analysis; decrease to save tokens.
    MAX_LOG_CHARS: int = 8000

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
