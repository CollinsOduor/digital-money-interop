from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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
    "MPESA_1001": {"name": "M-Pesa Agent 1", "balance": 500000.00, "network": "MPESA"},
    "MPESA_1002": {"name": "M-Pesa Agent 2", "balance": 120000.00, "network": "MPESA"},
    
    # AIRTEL MONEY PAYBILLS (Type: AIRTEL)
    "AIRTEL_2001": {"name": "Airtel Agent 1", "balance": 50000.00, "network": "AIRTEL"},
    "AIRTEL_2002": {"name": "Airtel Agent 2", "balance": 80000.00, "network": "AIRTEL"},
    
    # The Intermediary
    "INTERMEDIARY_ACCOUNT": {"name": "Float balance of Intermediary", "balance": 1000000.00, "network": "INTERMEDIARY"},
}

class TransferRequest(BaseModel):
    source_paybill: str
    destination_paybill: str
    amount: float

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
