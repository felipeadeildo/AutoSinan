from pathlib import Path

from pydantic import field_validator
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

    UPLOADED_FILES_DEST: Path = Path.cwd() / "uploads"
    """Folder where uploaded files will be stored."""

    @field_validator("UPLOADED_FILES_DEST")
    def validate_uploaded_files_dest(cls, value):
        if isinstance(value, str):
            value = Path(value)
        if not value.exists():
            value.mkdir()
        return value


settings = Settings()
