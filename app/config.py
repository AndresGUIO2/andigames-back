from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Andigames Incredible API"
    database_url: str
    async_database_url: str
    secret_key: str
    algorithm: str 
    time_to_expire: int
    
    class Config:
        env_file = ".env"

settings = Settings()