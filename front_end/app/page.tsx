"use client"

import React, { useState, useEffect } from 'react';

const API_URL = "http://localhost:8000/mpesa/stkpush/initiate";
const STATUS_URL = "http://localhost:8000/";

const formatKsh = (amount: any) => {
    if (typeof amount !== 'number') return 'N/A';
    return `Ksh ${amount.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ",")}`;
};

const App = () => {
    const [mpesaPhone, setMpesaPhone] = useState<any>('07XXXXXXXX');
    const [accountReference, setAccountReference] = useState<any>('INTEROP_FLOAT');
    const [airtelPaybill, setAirtelPaybill] = useState<any>('AIRTEL_2001');
    const [airtelCustomerMsisdn, setAirtelCustomerMsisdn] = useState<any>('0700000000');
    const [amount, setAmount] = useState<any>(10000.00);
    const [status, setStatus] = useState<any>(null);
    const [isLoading, setIsLoading] = useState<any>(false);
    const [ledgerSnapshot, setLedgerSnapshot] = useState<any>(null);

    // Fetch initial status and ledger snapshot
    const fetchStatus = async () => {
        try {
            const response = await fetch(STATUS_URL);
            const data = await response.json();
            setLedgerSnapshot(data.ledger);
        } catch (error) {
            console.error("Could not connect to server:", error);
        }
    };

    useEffect(() => {
        fetchStatus();
    }, []);

    const handleTransfer = async () => {
        if (
            amount <= 0 ||
            !mpesaPhone ||
            !accountReference ||
            !airtelPaybill ||
            !airtelCustomerMsisdn
        ) {
            setStatus({ success: false, message: "Please fill in all fields with valid values." });
            return;
        }

        setIsLoading(true);
        setStatus(null);

        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    phone_number: mpesaPhone,
                    amount: parseFloat(amount),
                    account_reference: accountReference,
                    airtel_paybill_id: airtelPaybill,
                    airtel_customer_msisdn: airtelCustomerMsisdn,
                    airtel_amount: parseFloat(amount),
                }),
            });

            const data = await response.json();

            if (response.ok) {
                setStatus({
                    success: true,
                    message: data.message || "STK push initiated.",
                    mpesa_response: data.mpesa_response,
                    checkout_request_id: data.checkout_request_id,
                });
                // Refresh full ledger status
                fetchStatus();
            } else {
                setStatus({ 
                    success: false, 
                    message: data.detail || "Transaction failed due to a server error." 
                });
            }
        } catch (error) {
            setStatus({ success: false, message: `Network error: Could not reach the backend server. Is it running on port 8000?` });
        } finally {
            setIsLoading(false);
        }
    };

    const renderLedger = () => {
        if (!ledgerSnapshot) {
            return <p className="text-gray-500">Loading initial ledger data...</p>;
        }

        return (
            <div className="space-y-4">
                {Object.keys(ledgerSnapshot).map((key) => {
                    const account = ledgerSnapshot[key];
                    const isIntermediary = key.includes('INTERMEDIARY');
                    const isAgent = key.includes('AGENT');
                    const color = account.network === 'MPESA' ? 'text-green-600' : 
                                  account.network === 'AIRTEL' ? 'text-red-600' : 'text-blue-600';
                    const networkTag = account.network === 'MPESA' ? 'M-PESA' : 
                                       account.network === 'AIRTEL' ? 'AIRTEL' : 'UNKNOWN';
                    const borderColor = isIntermediary ? 'border-blue-500 bg-blue-50' : 
                                       isAgent ? 'border-gray-300 bg-gray-50' : 'border-gray-200 bg-white';

                    return (
                        <div key={key} className={`p-4 border-l-4 ${borderColor} rounded-lg shadow-sm`}>
                            <div className="flex justify-between items-center">
                                <h4 className={`font-semibold text-sm ${color}`}>{account.name} ({networkTag})</h4>
                                <span className="text-xs font-mono text-gray-400">{key}</span>
                            </div>
                            <p className="text-2xl font-bold mt-1 text-gray-800">{formatKsh(account.balance)}</p>
                        </div>
                    );
                })}
            </div>
        );
    };

    return (
        <div className="min-h-screen bg-gray-50 p-4 sm:p-8 font-sans">
            <script src="https://cdn.tailwindcss.com"></script>
            <style>{`@import url('https://fonts.googleapis.com/css2?family=Inter:wght@100..900&display=swap'); body { font-family: 'Inter', sans-serif; }`}</style>

            <header className="text-center mb-10">
                <h1 className="text-4xl font-extrabold text-gray-900">
                    Paybill Interoperability <span className="text-indigo-600">POC</span>
                </h1>
                <p className="mt-2 text-lg text-gray-500">
                    M-Pesa and Airtel Money digital money transfers.
                </p>
            </header>

            <main className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Current Ledger Snapshot */}
                <div className="lg:col-span-1 bg-white p-6 rounded-xl shadow-lg h-fit">
                    <h3 className="text-2xl font-bold mb-4 border-b pb-2 text-gray-700">Live Ledger Status</h3>
                    {renderLedger()}
                </div>

                {/* Transfer Form & Simulation Results */}
                <div className="lg:col-span-2 bg-white p-6 rounded-xl shadow-lg">
                    <h3 className="text-2xl font-bold mb-6 text-gray-700">Initiate Transfer</h3>

                    {/* Transfer Form */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                        <div>
                            <label htmlFor="mpesaPhone" className="block text-sm font-medium text-gray-700">M-Pesa Phone Number</label>
                            <input
                                id="mpesaPhone"
                                type="text"
                                value={mpesaPhone}
                                onChange={(e) => setMpesaPhone(e.target.value)}
                                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 p-3 border"
                                placeholder="07XXXXXXXX"
                                disabled={isLoading}
                            />
                            <p className="mt-1 text-xs text-gray-500">Phone that will receive the STK push (e.g., 07XXXXXXXX).</p>
                        </div>
                        <div>
                            <label htmlFor="accountReference" className="block text-sm font-medium text-gray-700">Account Reference</label>
                            <input
                                id="accountReference"
                                type="text"
                                value={accountReference}
                                onChange={(e) => setAccountReference(e.target.value)}
                                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 p-3 border"
                                placeholder="INTEROP_FLOAT"
                                disabled={isLoading}
                            />
                            <p className="mt-1 text-xs text-gray-500">Appears in M-Pesa statements for this STK push.</p>
                        </div>
                        <div>
                            <label htmlFor="amount" className="block text-sm font-medium text-gray-700">Amount (Ksh)</label>
                            <input
                                id="amount"
                                type="number"
                                value={amount}
                                onChange={(e) => setAmount(e.target.value)}
                                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 p-3 border"
                                placeholder="10000.00"
                                min="1"
                                step="0.01"
                                disabled={isLoading}
                            />
                        </div>
                        <div>
                            <label htmlFor="airtelPaybill" className="block text-sm font-medium text-gray-700">Airtel Paybill ID</label>
                            <input
                                id="airtelPaybill"
                                type="text"
                                value={airtelPaybill}
                                onChange={(e) => setAirtelPaybill(e.target.value)}
                                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 p-3 border"
                                placeholder="AIRTEL_2001"
                                disabled={isLoading}
                            />
                            <p className="mt-1 text-xs text-gray-500">Paybill that will send funds to the Airtel customer.</p>
                        </div>
                        <div>
                            <label htmlFor="airtelMsisdn" className="block text-sm font-medium text-gray-700">Airtel Customer MSISDN</label>
                            <input
                                id="airtelMsisdn"
                                type="text"
                                value={airtelCustomerMsisdn}
                                onChange={(e) => setAirtelCustomerMsisdn(e.target.value)}
                                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 p-3 border"
                                placeholder="0700000000"
                                disabled={isLoading}
                            />
                            <p className="mt-1 text-xs text-gray-500">Airtel customer who receives the payout.</p>
                        </div>
                    </div>
                    
                    <button
                        onClick={handleTransfer}
                        disabled={isLoading}
                        className={`w-full py-3 px-6 border border-transparent rounded-lg text-lg font-medium text-white shadow-md transition duration-300 
                            ${isLoading ? 'bg-indigo-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500'}`}
                    >
                        {isLoading ? 'Processing Transfer via APIs...' : 'Execute Transfer'}
                    </button>

                    {/* Transaction Results */}
                    {status && (
                        <div className={`mt-8 p-6 rounded-lg ${status.success ? 'bg-green-50 border border-green-300' : 'bg-red-50 border border-red-300'}`}>
                            <h4 className={`text-xl font-bold ${status.success ? 'text-green-800' : 'text-red-800'} mb-3`}>
                                {status.success ? '✅ Operation Succeeded' : '❌ Operation Failed'}
                            </h4>
                            <p className="text-gray-700 mb-4">{status.message}</p>

                            {status.mpesa_response && (
                                <div className="mt-6 pt-6 border-t border-gray-200">
                                    <h5 className="font-semibold text-gray-700 mb-3">M-Pesa STK Push Response:</h5>
                                    <pre className="text-xs text-gray-600 bg-gray-50 p-3 rounded border border-gray-200 overflow-x-auto">
                                        {JSON.stringify(status.mpesa_response, null, 2)}
                                    </pre>
                                    {status.checkout_request_id && (
                                        <p className="text-sm text-gray-600 mt-3">
                                            Checkout Request ID: <span className="font-mono text-gray-800">{status.checkout_request_id}</span>
                                        </p>
                                    )}
                                </div>
                            )}
                        </div>
                    )}

                </div>
            </main>
        </div>
    );
};

export default App;
