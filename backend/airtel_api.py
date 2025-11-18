import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

import requests

from backend.utils import normalize_msisdn
from config import settings


class AirtelAPI:
    def authenticate(self) -> Dict[str, Any]:
        headers = {
            'Content-Type': 'application/json', 
            'Accept': '*/*', 
        }
        resp = requests.request(
            method="POST",
            url=f'{settings.AIRTEL_MONEY_BASE_URL}/auth/oauth2/token',
            data={
                "client_id": settings.AIRTEL_MONEY_CLIENT_ID,
                "client_secret": settings.AIRTEL_MONEY_CLIENT_SECRET,
                "grant_type": "client_credientials"
            },
            headers=headers
        )

        return resp["data"]["access_token"]
    
    def generate_transaction_reference(self) -> str:
        """Generate a unique transaction reference"""
        return f"AIRTEL{int(time.time())}{uuid.uuid4().hex[:8].upper()}"

    def paybill_to_customer(
        self,
        paybill_id: str,
        customer_msisdn: str,
        amount: float,
        *,
        currency: str = "KES",
        country: str = "KEN",
        transaction_reference: Optional[str] = None,
    ) -> Dict[str, Any]:
        if amount <= 0:
            raise ValueError("Amount for Paybill to customer transfer must be positive.")

        if transaction_reference is None:
            transaction_reference = self.generate_transaction_reference()

        payload = {
            "payee": {
                "msisdn": normalize_msisdn(customer_msisdn),
                "wallet_type": "NORMAL"
            },
            "reference": transaction_reference,
            "pin": settings.AIRTEL_MONEY_PIN,
            "transaction": {
                "amount": amount,
                "id": transaction_reference,
                "type": "B2C"
            }
        }

        headers = headers = {
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'X-Country': country,
            'X-Currency': currency,
            'Authorization': f'Bearer {self.authenticate()}',
            'x-signature': 'MGsp*********Ag==',
            'x-key': 'DVZC*******************NM='
        }

        response = requests.request(
            method="POST",
            url=f'{settings.AIRTEL_MONEY_BASE_URL}/paybill/v1/paybill-to-customer',
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        data = response.json()

        if not data.get("status", {}).get("code") == "200":
            raise Exception("Paybill to customer transfer failed")

        return data
