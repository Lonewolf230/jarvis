from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")
    LOCALSTACK_API_KEY: str = Field(..., env="LOCALSTACK_API_KEY")
    TAVILY_API_KEY: str = Field(..., env="TAVILY_API_KEY")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        
settings = Settings()