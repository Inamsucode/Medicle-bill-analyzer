from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    openrouter_api_key: str = Field(..., env="OPENROUTER_API_KEY")
    openrouter_model: str = Field("mistralai/mistral-7b-instruct:free", env="OPENROUTER_MODEL")
    openrouter_base_url: str = Field("https://openrouter.ai/api/v1", env="OPENROUTER_BASE_URL")
    environment: str = "development"

    class Config:
        env_file = ".env"


settings = Settings()
