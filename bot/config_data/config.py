import pymongo 
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

class Settings(BaseSettings):
    TOKEN: SecretStr
    MONGO_HOST: str
    MONGO_PORT: int
    MONGO_DB_NAME: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

config_settings = Settings()
admins = [248603604, 705098458, 660094929, 294062257]

mongo_client = pymongo.MongoClient(config_settings.MONGO_HOST, config_settings.MONGO_PORT) 
db = mongo_client[config_settings.MONGO_DB_NAME] 