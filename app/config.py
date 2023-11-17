from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Andigames Incredible API"
    database_url: str

    class Config:
        env_file = ".env"

settings = Settings()