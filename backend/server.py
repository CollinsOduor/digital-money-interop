from typing import Any, Dict, Optional

from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from airtel_api import AirtelAPI
from mpesa_api import MpesaAPI

app = FastAPI(title="Paybill Interoperability Simulator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- In-Memory Simulated Ledger ---
ledger = {
    # M-PESA PAYBILLS (Type: MPESA)
    "MPESA_1001": {"name": "Float in Account 1", "balance": 500000.00, "network": "MPESA"},
    "MPESA_1002": {"name": "Float in Account 2", "balance": 120000.00, "network": "MPESA"},
    
    # AIRTEL MONEY PAYBILLS (Type: AIRTEL)
    "AIRTEL_2001": {"name": "Float in Account 1", "balance": 50000.00, "network": "AIRTEL"},
    "AIRTEL_2002": {"name": "Float in Account 2", "balance": 80000.00, "network": "AIRTEL"},
    
    # The Intermediary
    "INTERMEDIARY_ACCOUNT": {"name": "Float balance of Intermediary", "balance": 1000000.00, "network": "INTERMEDIARY"},
}

class TransferRequest(BaseModel):
    source_paybill: str
    destination_paybill: str
    amount: float

class STKPushRequest(BaseModel):
    phone_number: str
    amount: float
    account_reference: str
    airtel_paybill_id: str
    airtel_customer_msisdn: str
    airtel_amount: Optional[float] = None
    airtel_currency: str = "KES"
    airtel_country: str = "KEN"
    airtel_narrative: str = "Cross-network payout"
    airtel_metadata: Optional[Dict[str, Any]] = None

mpesa_api = MpesaAPI()
airtel_api = AirtelAPI()
stk_sessions: Dict[str, Dict[str, Any]] = {}

@app.get("/")
def get_status():
    return {"status": "Simulator Running", "ledger": ledger}

@app.post("/transfer")
def process_transfer(request: TransferRequest):
    """Simulates the bank-backed agent transfer logic."""
    
    source_id = request.source_paybill.upper()
    dest_id = request.destination_paybill.upper()
    amount = round(request.amount, 2)
    
    # 1. Validation and Setup
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Transfer amount must be positive.")
    if source_id not in ledger or dest_id not in ledger:
        raise HTTPException(status_code=404, detail="One or both Paybill IDs not found.")
    if ledger[source_id]['balance'] < amount:
        raise HTTPException(status_code=400, detail=f"Insufficient balance in {source_id}.")

    transaction_steps = []

    try:
        # Step 1: Initiation step (Digital Debit)
        ledger[source_id]['balance'] -= amount
        ledger['INTERMEDIARY_ACCOUNT']['balance'] += amount
        transaction_steps.append({
            "status": "INITIATED",
            "description": f"STEP 1: {source_id} Debited. Funds moved digitally to Intermediary Float.",
            "details": f"Source Balance: {ledger[source_id]['balance']:.2f}, Agent Float: {ledger['INTERMEDIARY_ACCOUNT']['balance']:.2f}"
        })
        
        # Step 2: Bank Settlement
        settlement_fee = amount * 0.01 # A tiny 1% internal settlement fee
        
        ledger['INTERMEDIARY_ACCOUNT']['balance'] += settlement_fee 
        
        transaction_steps.append({
            "status": "SETTLED",
            "description": "STEP 2: Bank Settlement Occurs.",
            "details": f"Amount allocated to Airtel Float. Settlement Fee: {settlement_fee:.2f} (Deducted from Intermediary Float)."
        })
        
        # Step 3: Fullfillment step (Digital Credit)
        transfer_amount = amount - settlement_fee
        ledger[dest_id]['balance'] += transfer_amount
        ledger['INTERMEDIARY_ACCOUNT']['balance'] -= transfer_amount
        
        transaction_steps.append({
            "status": "COMPLETED",
            "description": f"STEP 3: {dest_id} Credited Successfully.",
            "details": f"Destination Balance: {ledger[dest_id]['balance']:.2f}, Final Intermediary Float: {ledger['INTERMEDIARY_ACCOUNT']['balance']:.2f}"
        })

        return {
            "success": True,
            "message": "Cross-Network Paybill Transfer Completed Successfully (Simulated).",
            "final_amount_credited": transfer_amount,
            "transaction_steps": transaction_steps,
            "current_ledger_snapshot": {
                source_id: ledger[source_id],
                dest_id: ledger[dest_id],
                "INTERMEDIARY_ACCOUNT": ledger["INTERMEDIARY_ACCOUNT"]
            }
        }
        
    except Exception as e:
        # Rollback logic
        raise HTTPException(status_code=500, detail=f"Simulation error: {str(e)}")

@app.post("/mpesa/stkpush/initiate")
def initiate_stk_push(request: STKPushRequest):
    try:
        mpesa_response = mpesa_api.initiate_stk_push(
            phone_number=request.phone_number,
            amount=request.amount,
            account_reference=request.account_reference,
            description="Interoperability STK Push",
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to initiate STK push: {exc}") from exc

    checkout_request_id = mpesa_response.get("CheckoutRequestID")
    if checkout_request_id:
        stk_sessions[checkout_request_id] = {
            "airtel_paybill_id": request.airtel_paybill_id,
            "airtel_customer_msisdn": request.airtel_customer_msisdn,
            "airtel_amount": request.airtel_amount or request.amount,
            "airtel_currency": request.airtel_currency,
            "airtel_country": request.airtel_country,
            "airtel_narrative": request.airtel_narrative,
            "airtel_metadata": request.airtel_metadata or {},
        }

    return {
        "success": True,
        "message": "STK push initiated. Awaiting callback confirmation.",
        "mpesa_response": mpesa_response,
        "checkout_request_id": checkout_request_id,
    }

@app.post("/mpesa/stkpush/callback")
def mpesa_stk_callback(payload: Dict[str, Any] = Body(...)):
    callback = payload.get("Body", {}).get("stkCallback", {})
    checkout_request_id = callback.get("CheckoutRequestID")
    result_code = str(callback.get("ResultCode", "1"))
    result_desc = callback.get("ResultDesc", "Unknown status")
    airtel_result = None
    context = stk_sessions.pop(checkout_request_id, None) if checkout_request_id else None

    if result_code == "0" and context:
        airtel_result = airtel_api.paybill_to_customer(
            paybill_id=context["airtel_paybill_id"],
            customer_msisdn=context["airtel_customer_msisdn"],
            amount=context["airtel_amount"],
            currency=context["airtel_currency"],
            country=context["airtel_country"],
            narrative=context["airtel_narrative"],
            metadata={
                "mpesa_checkout_request_id": checkout_request_id,
                "mpesa_result_desc": result_desc,
                **(context.get("airtel_metadata") or {}),
            },
        )

    return {
        "ResultCode": 0,
        "ResultDesc": "Callback received",
        "mpesa_callback": callback,
        "airtel_triggered": airtel_result is not None,
        "airtel_response": airtel_result,
        "stored_context_found": context is not None,
    }
