import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "postgresql://user:password@localhost:5432/trends_db")

settings = Settings()