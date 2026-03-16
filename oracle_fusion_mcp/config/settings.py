"""Configuration settings for Oracle Fusion MCP Server"""

import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""

    # Server
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    # CORS
    ALLOWED_ORIGINS: List[str] = Field(default=["*"], env="ALLOWED_ORIGINS")

    # Entra ID (optional — only needed for HTTP/OAuth server mode,
    # not required for STDIO transport).
    AZURE_AD_TENANT_ID: Optional[str] = Field(default="", alias="ENTRA_TENANT_ID")
    AZURE_AD_CLIENT_ID: Optional[str] = Field(default="", alias="ENTRA_ID")  # API app
    AZURE_AD_CLIENT_SECRET: Optional[str] = Field(default=None, alias="ENTRA_SECRET")
    MCP_CLIENT_ID: Optional[str] = Field(default=None, env="MCP_CLIENT_ID")  # Public client app
    ENTRA_ISSUER: Optional[str] = Field(None, env="ENTRA_ISSUER")

    # Oracle Fusion ERP (API calls)
    ORACLE_FUSION_BASE_URL: str = Field(
        default="", env="ORACLE_FUSION_BASE_URL"
    )
    ORACLE_FUSION_API_VERSION: str = Field(
        default="11.13.18.05", env="ORACLE_FUSION_API_VERSION"
    )

    # MCP config
    MCP_MODE: str = Field(default="readonly", env="MCP_MODE")
    MCP_VERSION: str = Field(default="2025-06-18", env="MCP_VERSION")
    MCP_SERVER_NAME: str = Field(
        default="oracle-fusion-erp-server", env="MCP_SERVER_NAME"
    )
    MCP_SERVER_VERSION: str = Field(default="0.1.0", env="MCP_SERVER_VERSION")

    # URLs
    BASE_URL: str = Field(default="http://localhost:8000", env="BASE_URL")

    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")

    # JWT (Entra token validation)
    JWT_ALGORITHM: str = Field(default="RS256", env="JWT_ALGORITHM")

    # Oracle JWT API Authentication (certificate-based)
    ORACLE_JWT_PRIVATE_KEY: Optional[str] = Field(
        default=None, env="ORACLE_JWT_PRIVATE_KEY"
    )
    ORACLE_JWT_PRIVATE_KEY_PATH: Optional[str] = Field(
        default=None, env="ORACLE_JWT_PRIVATE_KEY_PATH"
    )
    ORACLE_JWT_CERT_PATH: Optional[str] = Field(
        default=None, env="ORACLE_JWT_CERT_PATH"
    )
    ORACLE_JWT_ISSUER: Optional[str] = Field(
        default=None, env="ORACLE_JWT_ISSUER"
    )

    @property
    def oracle_api_base(self) -> str:
        """Full Oracle REST API base URL with version"""
        base = self.ORACLE_FUSION_BASE_URL.rstrip("/")
        return f"{base}/fscmRestApi/resources/{self.ORACLE_FUSION_API_VERSION}"

    @property
    def oracle_hcm_base(self) -> str:
        """Full Oracle HCM REST API base URL"""
        base = self.ORACLE_FUSION_BASE_URL.rstrip("/")
        return f"{base}/hcmRestApi/resources/{self.ORACLE_FUSION_API_VERSION}"

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "allow",
        "populate_by_name": True,
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    from dotenv import load_dotenv

    for env_path in [".env", "../.env"]:
        if os.path.exists(env_path):
            load_dotenv(env_path)
            break
    return Settings()
