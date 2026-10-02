from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = "local"
    database_url: str = "postgresql+psycopg://agentic:agentic@localhost:5432/agentic"
    openai_api_key: str = ""
    openai_model: str = "gpt-5.6-luna"
    embedding_model: str = "text-embedding-3-small"
    require_human_approval_pct: float = 15.0
    langchain_tracing_v2: bool = False
    langchain_project: str = "agentic-assortment"
    langchain_api_key: str = ""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
