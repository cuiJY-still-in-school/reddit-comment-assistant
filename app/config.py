from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "reddit_user"
    mysql_password: str = "reddit_password"
    mysql_database: str = "reddit_comments"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    # JWT
    jwt_secret_key: str = "your-jwt-secret-key-change-in-production"
    jwt_access_token_expire_minutes: int = 1440

    # DeepSeek
    deepseek_api_key: str = ""
    deepseek_api_base: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-flash"
    deepseek_timeout: int = 10

    # Rate Limiting
    rate_limit_per_minute: int = 10
    llm_concurrent_limit: int = 5
    circuit_breaker_threshold: int = 5
    circuit_breaker_recovery_seconds: int = 60

    # App
    app_name: str = "Reddit Comment Assistant"
    debug: bool = True

    @property
    def database_url(self) -> str:
        return (
            f"mysql+aiomysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            "?charset=utf8mb4"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
