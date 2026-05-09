from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "mysql+aiomysql://root:password@localhost:3307/reddit_comments"
    redis_url: str = "redis://localhost:16379/0"
    debug: bool = True

    jwt_secret: str = "change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 1440

    deepseek_api_key: str = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_redirect_uri: str = "http://localhost:8000/api/auth/reddit/callback"

    cors_origins: list[str] = ["http://localhost:8000", "chrome-extension://*"]

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()