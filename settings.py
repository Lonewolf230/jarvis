from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")
    LOCALSTACK_API_KEY: str = Field(..., env="LOCALSTACK_API_KEY")
    TAVILY_API_KEY: str = Field(..., env="TAVILY_API_KEY")
    VAULT_DIR: str = '/Users/manish/Manish Docs/Obsidian'
    VAULT_NAME: str = 'JarvisNotes'

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        
settings = Settings()