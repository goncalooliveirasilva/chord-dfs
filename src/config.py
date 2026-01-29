"""Application configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_prefix="CHORD_", case_sensitive=False)

    # Node identity
    host: str = "localhost"
    port: int = 5000

    # Bootstrap node (for joining the ring)
    bootstrap_host: str | None = None
    bootstrap_port: int | None = None

    # Chord parameters
    m_bits: int = 10
    stabilize_interval: float = 2.0

    # Storage
    storage_path: str = "/app/storage"

    # Logging
    log_level: str = "INFO"

    @property
    def address(self) -> tuple[str, int]:
        """Get node address as tuple."""
        return (self.host, self.port)

    @property
    def bootstrap_address(self) -> tuple[str, int] | None:
        """Get bootstrap node address if configured."""
        if self.bootstrap_host and self.bootstrap_port:
            return (self.bootstrap_host, self.bootstrap_port)
        return None


def get_settings() -> Settings:
    """Get application settings instance."""
    return Settings()
