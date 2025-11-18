import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    BASE_URL = os.getenv("base_url")
    
    MPESA_BASE_URL = os.getenv("mpesa_base_url", "https://sandbox.safaricom.co.ke")
    MPESA_CONSUMER_KEY = os.getenv("mpesa_consumer_key")
    MPESA_CONSUMER_SECRET = os.getenv("mpesa_consumer_secret")
    MPESA_SHORT_CODE = os.getenv("mpesa_short_code", "174379")
    MPESA_PASS_KEY = os.getenv("mpesa_pass_key")
    
    AIRTEL_MONEY_BASE_URL = os.getenv("airtel_money_base_url", "https://openapiuat.airtel.africa")
    AIRTEL_MONEY_CLIENT_ID = os.getenv("airtel_money_client_id")
    AIRTEL_MONEY_CLIENT_SECRET = os.getenv("airtel_money_client_secret")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
