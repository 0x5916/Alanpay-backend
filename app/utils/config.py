from datetime import timedelta
from pydantic import Field, computed_field
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="config/dev.env",
        extra="ignore"  # This will ignore extra env vars like PYTHONPATH
    )

    MAX_QR_ALIVE_HOUR: int = Field(24 * 7, description="Maximum lifetime of a QR code in seconds")
    ADMIN_ENABLE: bool = Field(False, description="Enable admin features")

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = Field("HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(60)
    FERNET_KEY: str  # Added for encryption

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    CORS_ORIGINS: list[str]

    @computed_field
    @property
    def asyncpg_url(self) -> MultiHostUrl:
        """
        This is a computed field that generates a PostgresDsn URL for asyncpg.

        Returns:
            PostgresDsn: The constructed PostgresDsn URL for asyncpg.
        """
        return MultiHostUrl.build(
            scheme="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    @computed_field
    @property
    def postgres_url(self) -> MultiHostUrl:
        """
        This is a computed field that generates a PostgresDsn URL

        Returns:
            PostgresDsn: The constructed PostgresDsn URL.
        """
        return MultiHostUrl.build(
            scheme="postgres",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )
    
    @computed_field
    @property
    def qr_alive_delta(self) -> timedelta:
        """
        This is a computed field that returns the maximum lifetime of a QR code as a timedelta.

        Returns:
            timedelta: The maximum lifetime of a QR code.
        """
        return timedelta(seconds=self.MAX_QR_ALIVE_HOUR)

settings = Settings() # type: ignore
