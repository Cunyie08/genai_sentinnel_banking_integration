import React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { setRoute, toggleVoice } from '../features/uiSlice';
import { Home, MessageSquare, Grid, Mic } from 'lucide-react';

const BottomNav = () => {
    const dispatch = useDispatch();
    const activeRoute = useSelector(state => state.ui.activeRoute);

    return (
        // FIXED BOTTOM BAR (Not floating, Full Width, Single Piece)
        <div className="fixed bottom-0 left-0 w-full bg-white border-t border-gray-100 px-6 py-3 pb-6 z-50 flex items-center justify-between shadow-[0_-4px_20px_rgba(0,0,0,0.03)]">
            
            {/* 1. LEFT: Voice Assistant Orb */}
            <button 
                onClick={() => dispatch(toggleVoice(true))}
                className="w-14 h-14 rounded-full bg-gradient-to-tr from-[#FF00CC] to-[#333399] p-[2px] shadow-lg shadow-purple-900/20 active:scale-95 transition-transform"
            >
                <div className="w-full h-full rounded-full bg-gradient-to-br from-pink-500 via-purple-500 to-indigo-600 flex items-center justify-center overflow-hidden relative">
                    <div className="absolute inset-0 bg-white/20 blur-md"></div>
                    <Mic size={24} className="text-white relative z-10" />
                </div>
            </button>

            {/* 2. RIGHT: Navigation Links (Home - Chat - Menu) */}
            <div className="flex-1 flex items-center justify-end gap-8 ml-4">
                
                {/* Home */}
                <NavBtn 
                    icon={Home} 
                    label="Home" 
                    isActive={activeRoute === 'home'} 
                    onClick={() => dispatch(setRoute('home'))} 
                />

                {/* Chat (Replaces Explore) */}
                <NavBtn 
                    icon={MessageSquare} 
                    label="Chat" 
                    isActive={activeRoute === 'chat'} 
                    onClick={() => dispatch(setRoute('chat'))} 
                />

                {/* Menu */}
                <NavBtn 
                    icon={Grid} 
                    label="Menu" 
                    isActive={activeRoute === 'menu'} 
                    onClick={() => dispatch(setRoute('menu'))} 
                />

            </div>

        </div>
    );
};

// Reusable Button Component
const NavBtn = ({ icon: Icon, label, isActive, onClick }) => (
    <button 
        onClick={onClick} 
        className="flex flex-col items-center justify-center gap-1 w-12 h-full transition-colors group"
    >
        <Icon 
            size={24} 
            strokeWidth={isActive ? 2.5 : 2} 
            className={isActive ? 'text-[#A01030]' : 'text-gray-400 group-hover:text-gray-600'} 
        />
        <span className={`text-[11px] font-bold ${isActive ? 'text-[#A01030]' : 'text-gray-400 group-hover:text-gray-600'}`}>
            {label}
        </span>
    </button>
);

export default BottomNav;