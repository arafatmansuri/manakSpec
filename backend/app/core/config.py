import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

settings = Settings()