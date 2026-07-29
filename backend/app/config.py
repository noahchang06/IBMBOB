import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./creative_reasoning.db")
    GRANITE_API_URL: str = os.getenv("GRANITE_API_URL", "https://us-south.ml.cloud.ibm.com")
    GRANITE_API_KEY: str = os.getenv("GRANITE_API_KEY", "")
    GRANITE_MODEL_ID: str = os.getenv("GRANITE_MODEL_ID", "ibm/granite-13b-chat-v2")
    SEED_DATA_PATH: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app", "data", "seed")
    USE_MOCK_GRANITE: bool = True
    
    class Config:
        env_file = ".env"

settings = Settings()
