from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "chatbot_db"
    GEMINI_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    HOST: Optional[str] = "http://localhost"
    PORT: Optional[int] = 8000

    class Config:
        env_file = ".env"

settings = Settings() 