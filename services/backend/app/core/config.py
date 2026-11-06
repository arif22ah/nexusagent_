from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "NexusAgent Enterprise Engine"
    DATABASE_URL: str = "postgresql://nexusadmin:nexusstrongpassword123@postgres:5432/nexusagent_db"
    MCP_SERVER_URL: str = "http://mcp_server:8080"
    OPENAI_API_KEY: str = "mock-key"
    MODEL_NAME: str = "gpt-4o-mini"
    CONFIDENCE_THRESHOLD: float = 0.65
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"


settings = Settings()
