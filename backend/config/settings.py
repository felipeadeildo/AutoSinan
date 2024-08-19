from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    debug: bool = False
    """If the application is in debug mode."""

    host: str = "0.0.0.0"
    """Server IP address."""

    port: int = 8000
    """Server port."""

    SECRET_KEY: str = "SECRET_KEY"
    """Secret key used to sign cookies."""

    ALGORITHM: str = "HS256"
    """Algorithm used to sign cookies."""

    DEFAULT_ADMIN_USERNAME: str = "admin"
    """Default admin username."""

    DEFAULT_ADMIN_PASSWORD: str = "admin"
    """Default admin password."""

    DEFAULT_ADMIN_NAME: str = "Administrator"
    """Default admin name."""


settings = Settings()
