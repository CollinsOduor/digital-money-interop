"""
M-Pesa API Simulation Module
"""

import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from backend.utils import normalize_msisdn
from config import settings
import requests

import base64


class MpesaAPI:
    def generate_security_credential(self):
        return base64.b64encode(settings.MPESA_PASS_KEY.encode('utf-8')).decode('utf-8')

    def generate_transaction_reference(self) -> str:
        return f"MPESA{int(time.time())}{uuid.uuid4().hex[:8].upper()}"

    def authenticate(self) -> Dict[str, Any]:
        response = requests.request(
            "GET",
            f'{settings.MPESA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials',
            headers={
                'Authorization': f'Basic {self.generate_auth_creds()}'
            }
        )
        response.raise_for_status()
        return response.json()

    def generate_auth_creds(self):
        creds = f"{settings.MPESA_CONSUMER_KEY}:{settings.MPESA_CONSUMER_SECRET}"
        return base64.b64encode(creds.encode('utf-8')).decode('utf-8')

    def _generate_password(self, timestamp: Optional[str] = None) -> str:
        if not timestamp:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        raw = f"{settings.MPESA_SHORT_CODE}{settings.MPESA_PASS_KEY}{timestamp}"
        return base64.b64encode(raw.encode('utf-8')).decode('utf-8')

    def initiate_stk_push(
        self,
        *,
        phone_number: str,
        amount: float,
        account_reference: str,
        description: str = "Interoperability STK Push",
        transaction_reference: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Simulate M-Pesa STK push initiation request.
        """
        if amount <= 0:
            raise ValueError("Amount must be greater than zero.")

        msisdn = normalize_msisdn(phone_number)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        password = self._generate_password(timestamp)
        bearer_token = self.authenticate()["access_token"]
        
        payload = {
            "BusinessShortCode": settings.MPESA_SHORT_CODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(round(amount)),
            "PartyA": msisdn,
            "PartyB": settings.MPESA_SHORT_CODE,
            "PhoneNumber": msisdn,
            "CallBackURL": f"{settings.BASE_URL}/mpesa/stkpush/callback",
            "AccountReference": account_reference,
            "TransactionDesc": description[:255]
        }

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {bearer_token}'
        }

        response = requests.request(
            method="POST",
            url=f'{settings.MPESA_BASE_URL}/mpesa/stkpush/v1/processrequest',
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        data = response.json()

        if data.get("ResponseCode") != "0":
            raise Exception("STK Push request was rejected")
        return data

    def confirm_stk_push(
        self,
        checkout_request_id: str,
        *,
        result_code: str = "0",
        result_desc: str = "The service request is processed successfully.",
        amount: Optional[float] = None,
        mpesa_receipt_number: Optional[str] = None,
        transaction_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Simulate asynchronous STK callback payload from M-Pesa.
        """
        success = result_code == "0"
        receipt = mpesa_receipt_number or uuid.uuid4().hex[:10].upper()
        transaction_time = transaction_date or datetime.now().strftime("%Y%m%d%H%M%S")

        return {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": self._generate_merchant_request_id(),
                    "CheckoutRequestID": checkout_request_id,
                    "ResultCode": result_code,
                    "ResultDesc": result_desc,
                    "CallbackMetadata": {
                        "Item": [
                            {"Name": "Amount", "Value": round(amount or 0, 2)},
                            {"Name": "MpesaReceiptNumber", "Value": receipt},
                            {"Name": "TransactionDate", "Value": transaction_time},
                        ]
                    }
                    if success
                    else None,
                }
            },
            "success": success,
            "timestamp": datetime.now().isoformat(),
        }
