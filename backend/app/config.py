from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "RePackAI"
    DATABASE_URL: str = "sqlite:///./repackai.db"
    SECRET_KEY: str = "supersecretkeyforrepackai"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # ML model configurations
    MODEL_PATH: str = "models/repack_model.joblib"
    DATASET_PATH: str = "data/synthetic/synthetic_containers.csv"
    
    # Recommender Weights
    WEIGHT_FINANCIAL: float = 0.40
    WEIGHT_ENVIRONMENTAL: float = 0.30
    WEIGHT_REUSABILITY: float = 0.20
    WEIGHT_OPERATIONAL: float = 0.10
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings()
