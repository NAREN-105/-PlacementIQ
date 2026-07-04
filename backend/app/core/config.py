import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GEMINI_MODEL: str = "gemini-2.0-flash"
    CHROMA_DIR: str = os.getenv("CHROMA_DIR", "./chroma_store")
    ALLOWED_ORIGINS: list[str] = ["*"]

    class Config:
        env_file = ".env"


settings = Settings()
