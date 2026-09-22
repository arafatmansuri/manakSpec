import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Indian Standards Procurement AI Engine"
    API_V1_STR: str = "/api/v1"
    
    # Database Settings
    # POSTGRES_USER: str = "postgres"
    # POSTGRES_PASSWORD: str = "postgres"
    # POSTGRES_HOST: str = "localhost"
    # POSTGRES_PORT: int = 5432
    # POSTGRES_DB: str = "is_procurement"
    
    
    # @property
    # def DATABASE_URL(self) -> str:
    #     return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Google Gemini API Settings
    GEMINI_API_KEY:str = os.getenv("GEMINI_API_KEY", "")
    EMBEDDING_MODEL: str = "gemini-embedding-001"
    PRIMARY_LLM_MODEL: str = "gemini-2.5-flash"
    
    # Groq Fallback Settings
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    FALLBACK_LLM_MODEL: str = "openai/gpt-oss-120b"

    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

settings = Settings()