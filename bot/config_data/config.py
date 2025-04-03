import os
import pymongo 
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, Field

class Settings(BaseSettings):
    TOKEN: SecretStr
    MONGODB_URI: str = Field(..., description="MongoDB connection URI")  # ... означает обязательное поле

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

config_settings = Settings()
admins = [248603604, 705098458, 660094929, 294062257, 6432481914]

# Используем URI из переменной окружения или конфига
mongodb_uri = os.getenv('MONGODB_URI', config_settings.MONGODB_URI)
mongo_client = pymongo.MongoClient(mongodb_uri)
db = mongo_client[mongodb_uri.split('/')[-1]]  # Получаем имя базы данных из URI 