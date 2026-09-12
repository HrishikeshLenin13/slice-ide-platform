"""Configuration management for Slice backend."""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # Server
    backend_host: str = "localhost"
    backend_port: int = 8080
    debug: bool = True
    log_level: str = "INFO"

    # Session
    session_dir: str = ".slice_sessions"
    session_cache_size: int = 1000

    # LSP
    lsp_python_enabled: bool = False
    lsp_python_port: int = 7071
    lsp_ts_enabled: bool = False
    lsp_ts_port: int = 7072

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def session_path(self) -> Path:
        """Get session directory path."""
        p = Path(self.session_dir)
        p.mkdir(exist_ok=True, parents=True)
        return p


settings = Settings()
