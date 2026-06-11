# backend/app/core/config.py
# FIX: Added JWT_SECRET_KEY and TOKEN_EXPIRE_MINUTES for the new token system.
# Generate a key with: python -c "import secrets; print(secrets.token_hex(32))"

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str    = "OpsPilot AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool      = False
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # ── Auth ────────────────────────────────────────────────────────
    # Master key — used only to issue JWT tokens via POST /auth/token
    API_KEY: str = ""
    # JWT signing secret — generate once, keep secret, never share
    JWT_SECRET_KEY: str = ""
    # How long issued tokens live (in minutes)
    TOKEN_EXPIRE_MINUTES: int = 60

    # ── Google Cloud / Gemini ───────────────────────────────────────
    GEMINI_API_KEY:        str = ""
    GOOGLE_CLOUD_PROJECT:  str = ""
    GOOGLE_CLOUD_LOCATION: str = "us-central1"
    GITLAB_PROJECT_ID: str = "82734152"
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
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    # ── Uploads ─────────────────────────────────────────────────────
    MAX_UPLOAD_SIZE_MB: int = 10

    # ── AI Log Analysis ─────────────────────────────────────────────
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
