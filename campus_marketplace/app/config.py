import os
from dataclasses import dataclass, field


def _cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "*")
    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Campus Marketplace API")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./campus_marketplace.db")
    redis_url: str = os.getenv("REDIS_URL", "")
    jwt_secret: str = os.getenv("JWT_SECRET", "dev-secret-change-me-please-use-32-bytes")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
    cors_origins: list[str] = field(default_factory=_cors_origins)


settings = Settings()
