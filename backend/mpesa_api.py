"""
M-Pesa API Simulation Module
"""

import base64
import time
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

import requests

from config import settings
from utils import normalize_msisdn

import pytz


class MpesaAPI:
    def __init__(self):
        self.short_code = settings.MPESA_SHORT_CODE or "174379"
        self.pass_key = settings.MPESA_PASS_KEY or "test_pass_key"
        self.base_url = settings.MPESA_BASE_URL or "https://sandbox.safaricom.co.ke"
        base_callback = settings.BASE_URL or "https://intermediary.com"
        self.callback_url = f"{base_callback.rstrip('/')}/mpesa/stkpush/callback"

    @staticmethod
    def _generate_checkout_request_id() -> str:
        return f"ws_CO_{uuid.uuid4().hex[:32]}"

    @staticmethod
    def _generate_merchant_request_id() -> str:
        return f"MR{int(time.time())}{uuid.uuid4().hex[:6].upper()}"

    def generate_security_credential(self) -> str:
        return base64.b64encode(self.pass_key.encode("utf-8")).decode("utf-8")

    def generate_transaction_reference(self) -> str:
        return f"MPESA{int(time.time())}{uuid.uuid4().hex[:8].upper()}"

    def generate_auth_creds(self) -> str:
        creds = f"{settings.MPESA_CONSUMER_KEY}:{settings.MPESA_CONSUMER_SECRET}"
        return base64.b64encode(creds.encode("utf-8")).decode("utf-8")

    def authenticate(self) -> Dict[str, Any]:
        response = requests.request(
            "GET",
            f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials",
            headers={"Authorization": f"Basic {self.generate_auth_creds()}"},
        )
        response.raise_for_status()
        return response.json()

    def _generate_password(self, timestamp: Optional[str] = None) -> str:
        if not timestamp:
            timestamp = datetime.now(pytz.timezone('Africa/Nairobi')).strftime("%Y%m%d%H%M%S")
        raw = f"{self.short_code}{self.pass_key}{timestamp}"
        return base64.b64encode(raw.encode("utf-8")).decode("utf-8")

    def initiate_stk_push(
        self,
        *,
        phone_number: str,
        amount: float,
        account_reference: str,
        description: str = "Interoperability STK Push",
        transaction_reference: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Initiate (or simulate) an M-Pesa STK push request.
        """
        if amount <= 0:
            raise ValueError("Amount must be greater than zero.")

        msisdn = normalize_msisdn(phone_number)
        timestamp = datetime.now(pytz.timezone('Africa/Nairobi')).strftime("%Y%m%d%H%M%S")
        password = self._generate_password(timestamp)
        merchant_request_id = self._generate_merchant_request_id()
        checkout_request_id = self._generate_checkout_request_id()
        reference = transaction_reference or merchant_request_id

        payload = {
            "BusinessShortCode": self.short_code,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(round(amount)),
            "PartyA": msisdn,
            "PartyB": self.short_code,
            "PhoneNumber": msisdn,
            "CallBackURL": self.callback_url,
            "AccountReference": account_reference,
            "TransactionDesc": description[:255],
            "ClientReference": reference,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.authenticate()['access_token']}",
        }

        try:
            response = requests.request(
                method="POST",
                url=f"{self.base_url}/mpesa/stkpush/v1/processrequest",
                headers=headers,
                json=payload,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException:
            data = {
                "MerchantRequestID": merchant_request_id,
                "CheckoutRequestID": checkout_request_id,
                "ResponseCode": "0",
                "ResponseDescription": "Simulated STK push accepted",
                "CustomerMessage": "Simulated STK Push request sent to handset",
                "Request": payload,
                "simulation": True,
                "timestamp": datetime.now().isoformat(),
            }
        else:
            data.setdefault("MerchantRequestID", merchant_request_id)
            data.setdefault("CheckoutRequestID", checkout_request_id)
            data["Request"] = payload
            data["timestamp"] = datetime.now().isoformat()

        if data.get("ResponseCode") != "0":
            raise Exception("Nework payment request request was rejected")
        return data

    def confirm_stk_push(
        self,
        checkout_request_id: str,
        *,
        result_code: str = "0",
        result_desc: str = "The service request is processed successfully.",
        amount: Optional[float] = None,
        mpesa_receipt_number: Optional[str] = None,
        transaction_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Simulate asynchronous STK callback payload from M-Pesa.
        """
        success = result_code == "0"
        receipt = mpesa_receipt_number or uuid.uuid4().hex[:10].upper()
        transaction_time = transaction_date or datetime.now(pytz.timezone('Africa/Nairobi')).strftime("%Y%m%d%H%M%S")

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
            "timestamp": datetime.now(pytz.timezone('Africa/Nairobi')).isoformat(),
        }
