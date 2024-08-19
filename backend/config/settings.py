from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    debug: bool = False
    """If the application is in debug mode."""

    host: str = "0.0.0.0"
    """Server IP address."""

    port: int = 8000
    """Server port."""


settings = Settings()
