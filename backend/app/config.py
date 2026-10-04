from pathlib import Path
from typing import Optional, List
from pydantic import Field, field_validator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    AGENT_NAME: str = "MiniClaw"
    AGENT_VERSION: str = "0.1.0"

    HOST: str = "127.0.0.1"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    DATABASE_URL: str = "sqlite+aiosqlite:///./data/agent.db"
    DATABASE_ECHO: bool = False

    MODEL_PROVIDER: str = "ollama"
    MODEL_NAME: str = "llama3.2:3b"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None

    EMBEDDING_PROVIDER: str = "sentence-transformers"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DEVICE: str = "cpu"

    JWT_SECRET_KEY: str = Field(default="MiniClawSuperSecretKeyForDevelopmentOnly32CharsMin", min_length=32)
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Store as string in .env, parse via computed fields
    CORS_ORIGINS_STR: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"
    ALLOWED_HOSTS_STR: str = "localhost,127.0.0.1"

    ENABLE_BROWSER: bool = True
    ENABLE_GITHUB: bool = True
    ENABLE_REMOTE_ACCESS: bool = False
    ENABLE_SCHEDULER: bool = True
    ENABLE_NOTIFICATIONS: bool = True

    GITHUB_TOKEN: Optional[str] = None
    GITHUB_WEBHOOK_SECRET: Optional[str] = None

    WEB_PUSH_VAPID_PUBLIC_KEY: Optional[str] = None
    WEB_PUSH_VAPID_PRIVATE_KEY: Optional[str] = None
    WEB_PUSH_VAPID_CLAIMS_SUB: str = "mailto:admin@localhost"

    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None

    DISCORD_BOT_TOKEN: Optional[str] = None
    DISCORD_CHANNEL_ID: Optional[str] = None

    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None

    TAILSCALE_AUTH_KEY: Optional[str] = None
    CLOUDFLARE_TUNNEL_TOKEN: Optional[str] = None

    APPROVAL_TIMEOUT_SECONDS: int = 300
    MAX_FILE_SIZE_MB: int = 100
    MAX_COMMAND_OUTPUT_CHARS: int = 10000

    DATA_DIR: Path = Path("./data")
    LOGS_DIR: Path = Path("./logs")
    PLUGINS_DIR: Path = Path("./plugins")

    VECTOR_DB_PATH: Path = Path("./data/vector_db")

    @field_validator("DATA_DIR", "LOGS_DIR", "PLUGINS_DIR", "VECTOR_DB_PATH", mode="before")
    @classmethod
    def ensure_path(cls, v):
        if isinstance(v, str):
            return Path(v)
        return v

    @computed_field
    @property
    def CORS_ORIGINS(self) -> List[str]:
        return [item.strip() for item in self.CORS_ORIGINS_STR.split(",") if item.strip()]

    @computed_field
    @property
    def ALLOWED_HOSTS(self) -> List[str]:
        return [item.strip() for item in self.ALLOWED_HOSTS_STR.split(",") if item.strip()]


settings = Settings()