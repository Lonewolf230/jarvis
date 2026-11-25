from pydantic import SecretStr
from pydantic_settings import BaseSettings,SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    OPENAI_API_KEY: SecretStr 
    LOCALSTACK_API_KEY: SecretStr 
    TAVILY_API_KEY: SecretStr 
    POSTGRES_DB_URI: SecretStr
    VAULT_DIR: str = '/Users/manish/Manish Docs/Obsidian'
    VAULT_NAME: str = 'JarvisNotes'
    EMBEDDING_MODEL: str = 'text-embedding-3-small'
    ALLOWED_FILE_TYPES : list[str] = ["pdf","docx","text","md"]
    CHUNK_OVERLAP : int = 80
    CHUNK_SIZE : int = 500
    COLLECTION : str = "Notes"

        
settings = Settings()