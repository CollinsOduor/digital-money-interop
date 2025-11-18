import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    BASE_URL:Optional[str] = os.getenv("base_url")
    
    MPESA_BASE_URL:Optional[str] = os.getenv("mpesa_base_url", "https://sandbox.safaricom.co.ke")
    MPESA_CONSUMER_KEY:Optional[str] = os.getenv("mpesa_consumer_key")
    MPESA_CONSUMER_SECRET:Optional[str] = os.getenv("mpesa_consumer_secret")
    MPESA_SHORT_CODE:Optional[str] = os.getenv("mpesa_short_code", "174379")
    MPESA_PASS_KEY:Optional[str] = os.getenv("mpesa_pass_key")
    
    AIRTEL_MONEY_BASE_URL:Optional[str] = os.getenv("airtel_money_base_url", "https://openapiuat.airtel.africa")
    AIRTEL_MONEY_CLIENT_ID:Optional[str] = os.getenv("airtel_money_client_id")
    AIRTEL_MONEY_CLIENT_SECRET:Optional[str]  = os.getenv("airtel_money_client_secret")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
