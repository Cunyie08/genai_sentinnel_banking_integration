import React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { toggleVoice } from '../features/uiSlice';
import { X, Mic, ShieldAlert, Fingerprint } from 'lucide-react';

// --- 1. VOICE ASSISTANT OVERLAY ---
export const VoiceModal = () => {
    const dispatch = useDispatch();
    const isVoiceActive = useSelector(state => state.ui.isVoiceActive);
    
    if (!isVoiceActive) return null;

    return (
        <div className="absolute inset-0 z-[60] bg-black/90 backdrop-blur-xl flex flex-col items-center justify-center text-white animate-in fade-in duration-300">
            
            {/* Close Button */}
            <button 
                onClick={() => dispatch(toggleVoice(false))} 
                className="absolute top-8 right-8 p-3 bg-white/10 rounded-full hover:bg-white/20 transition-colors"
            >
                <X size={24} />
            </button>

            {/* Glowing Orb Animation */}
            <div className="relative mb-12">
                <div className="absolute inset-0 bg-[#A01030] rounded-full blur-[60px] opacity-60 animate-pulse"></div>
                <div className="w-32 h-32 rounded-full bg-gradient-to-tr from-[#A01030] to-[#FF4D6D] relative z-10 flex items-center justify-center shadow-[0_0_50px_rgba(160,16,48,0.5)] border-4 border-white/10">
                    <Mic size={48} className="text-white animate-bounce" />
                </div>
                {/* Ripples */}
                <div className="absolute inset-0 border border-white/20 rounded-full animate-ping delay-75"></div>
                <div className="absolute inset-0 border border-white/10 rounded-full animate-ping delay-150"></div>
            </div>

            <h2 className="text-3xl font-bold tracking-tight mb-3">I'm Listening...</h2>
            <p className="text-white/60 font-medium text-center max-w-xs leading-relaxed">
                Try saying <span className="text-white font-bold">"Send 5k to Mum"</span> or <span className="text-white font-bold">"Pay my electric bill"</span>
            </p>

            {/* Language Pill */}
            <div className="mt-8 px-4 py-2 bg-white/10 rounded-full border border-white/5 text-xs font-mono text-white/50">
                Listening in: English • Yoruba • Hausa
            </div>
        </div>
    );
};

// --- 2. SENTINEL (FRAUD ALERT) MODAL ---
// You can trigger this by dispatching an action if you want to test it later
export const SentinelModal = () => {
    // For now, this is hidden by default. 
    // To test: Change "false" to "true" manually or connect to Redux state.
    const showFraudAlert = false; 

    if (!showFraudAlert) return null;

    return (
        <div className="absolute inset-0 z-[70] flex items-end sm:items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in">
            <div className="w-full max-w-sm bg-white rounded-[32px] p-6 shadow-2xl animate-in slide-in-from-bottom duration-300">
                
                <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mb-4">
                    <ShieldAlert size={24} className="text-red-600" />
                </div>

                <h3 className="text-xl font-bold text-gray-900 mb-2">Suspicious Attempt</h3>
                <p className="text-gray-500 text-sm mb-6 leading-relaxed">
                    We blocked a charge of <span className="font-bold text-gray-900">₦50,000</span> at <span className="font-bold text-gray-900">Jumia NG</span>. Was this you?
                </p>

                <div className="space-y-3">
                    <button className="w-full bg-[#A01030] text-white py-4 rounded-xl font-bold flex items-center justify-center gap-2 shadow-lg shadow-red-900/20 active:scale-95 transition-transform">
                        <Fingerprint size={20} /> Verify Identity
                    </button>
                    <button className="w-full bg-gray-50 text-gray-900 py-4 rounded-xl font-bold active:scale-95 transition-transform">
                        No, Block Card
                    </button>
                </div>
            </div>
        </div>
    );
};