import React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { toggleVoice } from '../features/uiSlice';

const VoiceOverlay = () => {
    const dispatch = useDispatch();
    const isVoiceActive = useSelector(state => state.ui.isVoiceActive);
    
    if (!isVoiceActive) return null;

    return (
        <div 
            onClick={() => dispatch(toggleVoice(false))}
            className="absolute inset-0 bg-black/80 backdrop-blur-md z-[60] flex flex-col items-center justify-center text-white animate-in fade-in"
        >
            <div className="w-32 h-32 bg-gradient-to-r from-[#A01030] via-purple-500 to-pink-500 rounded-full blur-2xl animate-pulse"></div>
            <div className="w-24 h-24 bg-white/10 rounded-full border border-white/20 absolute"></div>
            <h2 className="mt-8 text-2xl font-bold tracking-tight">N-ATLaS</h2>
            <p className="text-white/60 font-mono text-sm mt-2">Listening in English, Yoruba, Hausa...</p>
        </div>
    )
};
export default VoiceOverlay;