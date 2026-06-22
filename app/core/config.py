from pydantic import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str
    greptile_api_key: str | None = None
    environment: str = "development"

    class Config:
        env_file = ".env"


settings = Settings()
