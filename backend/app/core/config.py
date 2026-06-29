"""Application configuration, loaded from environment / .env file."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application settings.

    Values are read from the process environment, falling back to a local
    ``.env`` file. Secrets must never be committed; see ``.env.example``.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Database ---
    database_url: str = "postgresql+psycopg://cutpoint:cutpoint@localhost:5432/cutpoint"

    # --- Auth (JWT) ---
    jwt_secret: str = "dev-insecure-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 10080  # 7 days

    # --- LLM (Groq) ---
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # --- Realistic AI try-on (fal.ai, Flux Kontext) ---
    fal_key: str = ""
    fal_model: str = "fal-ai/flux-pro/kontext"

    # --- Email notifications (Gmail SMTP) ---
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""  # full Gmail address
    smtp_password: str = ""  # Gmail app password (not your normal password)
    email_from: str = ""  # defaults to smtp_user if blank
    email_from_name: str = "CutPoint"

    # --- Server / CORS ---
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        """CORS origins as a clean list."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def llm_enabled(self) -> bool:
        """Whether a real LLM provider is configured."""
        return bool(self.groq_api_key.strip())

    @property
    def ai_tryon_enabled(self) -> bool:
        """Whether realistic AI try-on (fal.ai) is configured."""
        return bool(self.fal_key.strip())

    @property
    def email_enabled(self) -> bool:
        """Whether email notifications (SMTP) are configured."""
        return bool(self.smtp_user.strip() and self.smtp_password.strip())

    @property
    def email_sender(self) -> str:
        """The From address, defaulting to the SMTP user."""
        return self.email_from.strip() or self.smtp_user.strip()


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor (single instance per process)."""
    return Settings()
