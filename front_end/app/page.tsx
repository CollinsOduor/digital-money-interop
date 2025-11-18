"use client"

import React, { useState, useEffect } from 'react';

const API_URL = "http://localhost:8000/transfer";
const STATUS_URL = "http://localhost:8000/";

const formatKsh = (amount: any) => {
    if (typeof amount !== 'number') return 'N/A';
    return `Ksh ${amount.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ",")}`;
};

const App = () => {
    const [sourcePaybill, setSourcePaybill] = useState<any>('MPESA_AGENT_1');
    const [destPaybill, setDestPaybill] = useState<any>('AIRTEL_AGENT_1');
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
        if (amount <= 0 || !sourcePaybill || !destPaybill) {
            setStatus({ success: false, message: "Please enter valid Paybill IDs and a positive amount." });
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
                    source_paybill: sourcePaybill,
                    destination_paybill: destPaybill,
                    amount: parseFloat(amount),
                }),
            });

            const data = await response.json();

            if (response.ok) {
                setStatus(data);
                setLedgerSnapshot(data.current_ledger_snapshot);
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
                {Object.keys(ledgerSnapshot).map(key => {
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
                    Simulated M-Pesa and Airtel Money API transfers using proper API structures.
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
                            <label htmlFor="source" className="block text-sm font-medium text-gray-700">Source Paybill</label>
                            <input
                                id="source"
                                type="text"
                                value={sourcePaybill}
                                onChange={(e) => setSourcePaybill(e.target.value)}
                                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 p-3 border"
                                placeholder="MPESA_AGENT_1"
                                disabled={isLoading}
                            />
                            <p className="mt-1 text-xs text-gray-500">e.g., MPESA_AGENT_1, MPESA_AGENT_2, AIRTEL_AGENT_1, AIRTEL_AGENT_2</p>
                        </div>
                        <div>
                            <label htmlFor="destination" className="block text-sm font-medium text-gray-700">Destination Paybill</label>
                            <input
                                id="destination"
                                type="text"
                                value={destPaybill}
                                onChange={(e) => setDestPaybill(e.target.value)}
                                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 p-3 border"
                                placeholder="AIRTEL_AGENT_1"
                                disabled={isLoading}
                            />
                            <p className="mt-1 text-xs text-gray-500">e.g., MPESA_AGENT_1, MPESA_AGENT_2, AIRTEL_AGENT_1, AIRTEL_AGENT_2</p>
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

                            {status.transaction_steps && (
                                <div className="space-y-4 pt-4 border-t border-gray-200">
                                    <h5 className="font-semibold text-gray-700">Transaction Flow Steps:</h5>
                                    {status.transaction_steps.map((step: any, index: any) => (
                                        <div key={index} className="flex space-x-3 items-start">
                                            <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-white shrink-0 ${step.status === 'COMPLETED' ? 'bg-indigo-600' : 'bg-yellow-600'}`}>
                                                {index + 1}
                                            </div>
                                            <div>
                                                <p className="font-medium text-gray-900">{step.description}</p>
                                                <p className="text-sm text-gray-500">{step.details}</p>
                                            </div>
                                        </div>
                                    ))}
                                    {status.settlement_fee !== undefined && status.settlement_fee > 0 && (
                                        <p className="text-sm text-gray-600 pt-2 border-t border-gray-200">
                                            Settlement Fee: {formatKsh(status.settlement_fee)} (1% for cross-network transfers)
                                        </p>
                                    )}
                                    <p className="text-lg font-bold text-indigo-700 pt-3 border-t border-gray-200">
                                        Final Credit Amount: {formatKsh(status.final_amount_credited)}
                                    </p>
                                    {status.transfer_type && (
                                        <p className="text-sm text-gray-600 pt-2">
                                            Transfer Type: <span className="font-semibold">{status.transfer_type}</span>
                                        </p>
                                    )}
                                </div>
                            )}
                            {status.api_responses && status.api_responses.length > 0 && (
                                <div className="mt-6 pt-6 border-t border-gray-200">
                                    <h5 className="font-semibold text-gray-700 mb-3">API Responses:</h5>
                                    <div className="space-y-3">
                                        {status.api_responses.map((apiResp: any, index: number) => (
                                            <div key={index} className="bg-gray-50 p-3 rounded border border-gray-200">
                                                <div className="flex justify-between items-start mb-2">
                                                    <span className="text-xs font-semibold text-gray-700">{apiResp.step}</span>
                                                    <span className="text-xs text-gray-500">{apiResp.network}</span>
                                                </div>
                                                <pre className="text-xs text-gray-600 overflow-x-auto">
                                                    {JSON.stringify(apiResp.response, null, 2)}
                                                </pre>
                                            </div>
                                        ))}
                                    </div>
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
