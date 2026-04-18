import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { closePayment } from '../features/uiSlice';
import { ShieldCheck, X, Fingerprint, AlertTriangle, CheckCircle, Lock } from 'lucide-react';

const PaymentModal = () => {
    const dispatch = useDispatch();
    const show = useSelector(state => state.ui.showPaymentModal);
    const [status, setStatus] = useState('pending'); 

    
    useEffect(() => {
        if (show) setStatus('pending');
    }, [show]);

    const handleApprove = () => {
        setStatus('verifying');
        
        setTimeout(() => {
            setStatus('success');
            
            setTimeout(() => {
                dispatch(closePayment());
            }, 2000);
        }, 1500);
    };

    if (!show) return null;

    return (
        <div className="fixed inset-0 z-[60] flex items-end sm:items-center justify-center bg-vault-light-bg/90 dark:bg-black/80 backdrop-blur-md p-4 animate-in fade-in duration-200">
            
            <div className="w-full max-w-sm bg-white dark:bg-vault-dark-card rounded-[32px] shadow-2xl border border-gray-100 dark:border-white/5 overflow-hidden relative animate-in slide-in-from-bottom duration-300">
                
                {}
                <div className="px-6 py-4 flex justify-between items-center border-b border-gray-50 dark:border-white/5">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 vault-gradient rounded-full flex items-center justify-center text-white font-black text-xs">S</div>
                        <div>
                            <h3 className="text-sm font-bold text-gray-900 dark:text-white">SentinelBank</h3>
                            <p className="text-[10px] text-gray-400 dark:text-slate-500 font-medium">Secure Verification</p>
                        </div>
                    </div>
                    <button onClick={() => dispatch(closePayment())} className="p-2 bg-gray-50 dark:bg-white/5 rounded-full hover:bg-gray-100 dark:hover:bg-white/10 transition-colors">
                        <X size={18} className="text-gray-500 dark:text-slate-400"/>
                    </button>
                </div>

                {}
                <div className="p-6 text-center">
                    
                    {}
                    {status === 'pending' && (
                        <>
                            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-1">Verify Online Payment</h2>
                            <p className="text-xs text-gray-500 dark:text-slate-400 mb-8">A payment request requires your approval.</p>

                            {}
                            <div className="bg-gray-50 dark:bg-vault-dark-input rounded-[24px] p-6 mb-8 border border-gray-100 dark:border-white/5 relative overflow-hidden">
                                <div className="absolute top-0 left-0 w-full h-1 vault-gradient"></div>
                                
                                <div className="flex justify-between items-end mb-4">
                                    <div className="text-left">
                                        <p className="text-[10px] font-bold text-vault-cyan uppercase tracking-wider mb-1">Merchant</p>
                                        <h3 className="text-lg font-bold text-gray-900 dark:text-white">Amazon</h3>
                                    </div>
                                    <div className="text-right">
                                        <p className="text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider mb-1">Date</p>
                                        <p className="text-xs font-bold text-gray-700 dark:text-slate-300">Oct 24, 14:20</p>
                                    </div>
                                </div>

                                <div className="text-left">
                                    <p className="text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider mb-0.5">Total Amount</p>
                                    <h1 className="text-3xl font-black vault-gradient-text tracking-tight">₦45,000.00</h1>
                                </div>
                            </div>

                            {}
                            <div className="mb-8">
                                <p className="text-xs font-bold text-gray-500 dark:text-slate-400 mb-4">Use Fingerprint / Face ID to Approve</p>
                                <button 
                                    onClick={handleApprove}
                                    className="w-20 h-20 rounded-full border-2 border-vault-cyan/20 bg-cyan-50 dark:bg-vault-cyan/10 flex items-center justify-center mx-auto text-vault-cyan relative group active:scale-95 transition-transform"
                                >
                                    <div className="absolute inset-0 rounded-full border border-vault-cyan opacity-20 animate-ping"></div>
                                    <Fingerprint size={40} strokeWidth={1.5} />
                                </button>
                            </div>

                            {}
                            <div className="space-y-3">
                                <button onClick={handleApprove} className="w-full py-4 vault-gradient text-white rounded-xl font-bold shadow-lg vault-glow active:scale-95 transition-transform flex items-center justify-center gap-2">
                                    <ShieldCheck size={18} /> Approve Payment
                                </button>
                                <button onClick={() => dispatch(closePayment())} className="w-full py-4 bg-gray-50 dark:bg-white/5 text-gray-600 dark:text-slate-300 rounded-xl font-bold border border-gray-100 dark:border-white/5 flex items-center justify-center gap-2 active:bg-gray-100 dark:active:bg-white/10 transition-colors">
                                    <AlertTriangle size={18} /> Decline & Report Fraud
                                </button>
                            </div>
                        </>
                    )}

                    {}
                    {status === 'verifying' && (
                        <div className="py-12">
                            <div className="w-24 h-24 mx-auto mb-6 relative">
                                <div className="absolute inset-0 border-4 border-gray-100 dark:border-white/10 rounded-full"></div>
                                <div className="absolute inset-0 border-4 border-vault-cyan rounded-full border-t-transparent animate-spin"></div>
                                <Fingerprint size={40} className="text-vault-cyan absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 opacity-50"/>
                            </div>
                            <h3 className="text-lg font-bold text-gray-900 dark:text-white">Verifying Biometrics...</h3>
                            <p className="text-sm text-gray-500 dark:text-slate-400 mt-2">Please wait a moment.</p>
                        </div>
                    )}

                    {}
                    {status === 'success' && (
                        <div className="py-12 animate-in zoom-in-95">
                            <div className="w-24 h-24 bg-green-100 dark:bg-green-500/20 text-green-600 dark:text-green-400 rounded-full flex items-center justify-center mx-auto mb-6">
                                <CheckCircle size={48} />
                            </div>
                            <h3 className="text-xl font-bold text-gray-900 dark:text-white">Payment Approved</h3>
                            <p className="text-sm text-gray-500 dark:text-slate-400 mt-2">Transaction ID: 88291-AZ</p>
                        </div>
                    )}

                </div>
                
                {}
                <div className="bg-gray-50 dark:bg-vault-dark-input py-3 flex items-center justify-center gap-1.5 border-t border-gray-100 dark:border-white/5">
                    <Lock size={12} className="text-gray-400 dark:text-slate-500"/>
                    <span className="text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest">End-to-End Encrypted</span>
                </div>

            </div>
        </div>
    );
};

export default PaymentModal;