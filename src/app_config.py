from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class AppConfig(BaseSettings):
    MONGODB_URL: Optional[str] = None
    BINANCE_API_KEY: Optional[str] = None
    BINANCE_API_SECRET: Optional[str] = None
    API_KEY_QDRANT: Optional[str] = None
    COLLECTION_NAME: Optional[str] = None
    COLLECTION_NAME_MEM: Optional[str] = None
    DATA_PATH: Optional[str] = None
    MODEL_NAME: Optional[str] = None
    AZURE_ENDPOINT: Optional[str] = None
    API_VERSION: Optional[str] = None
    QDRANT_URL: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_ENGINE: Optional[str] = None
    EMBEDDING_MODEL: Optional[str] = None
    DB_HOST: Optional[str] = None
    TABLE_NAME: Optional[str] = None
    MONGODB_URI: Optional[str] = None
    MONGODB_DB_NAME: Optional[str] = None
    MONGODB_COLLECTION_NAME: Optional[str] = None
    QDRANT_URL: Optional[str] = None
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION_NAME: Optional[str] = None
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")



# Initialize the configuration
app_config = AppConfig()
