from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./veritas_dev.db"
    jwt_secret: str = "dev-only-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    cors_origins: str = "http://localhost:5173"
    llm_api_key: str = ""
    news_api_key: str = ""
    llm_model: str = "claude-sonnet-5-5"
    max_node_retries: int = 2
    environment: str = "development"  # set to "production" on the server
    log_level: str = "INFO"
    auth_attempts_per_minute: int = 10  # per client IP, login and register
    max_active_tasks_per_user: int = 3
    max_tasks_per_day: int = 30
    stale_task_minutes: int = 30  # queued/running tasks older than this are failed at startup


    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


settings = Settings()


def validate_production(cfg: Settings) -> None:
    """Refuse to start in production with unsafe defaults."""
    if not cfg.is_production:
        return
    problems = []
    if cfg.jwt_secret.startswith("dev-only") or len(cfg.jwt_secret) < 32:
        problems.append("JWT_SECRET must be a random string of at least 32 characters")
    if cfg.database_url.startswith("sqlite"):
        problems.append("DATABASE_URL must point at PostgreSQL in production")
    if "*" in cfg.cors_origins or not cfg.cors_origins.strip():
        problems.append("CORS_ORIGINS must list explicit origins")
    if problems:
        raise RuntimeError("Unsafe production configuration: " + "; ".join(problems))
