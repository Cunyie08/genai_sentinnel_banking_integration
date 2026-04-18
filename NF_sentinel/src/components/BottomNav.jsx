import { useNavigate } from 'react-router-dom';
import React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { toggleVoice } from '../features/uiSlice';
import { Home, MessageSquare, Grid, Mic } from 'lucide-react';

const BottomNav = () => {
  const navigate = useNavigate();

    const dispatch = useDispatch();
    const activeRoute = useSelector(state => state.ui.activeRoute);

    return (
        
        <div className="fixed bottom-0 left-0 w-full bg-white dark:bg-vault-dark-card border-t border-gray-100 dark:border-white/5 px-6 py-3 pb-6 z-50 flex items-center justify-between shadow-[0_-4px_20px_rgba(0,0,0,0.03)] dark:shadow-[0_-4px_20px_rgba(0,0,0,0.3)] vault-transition">
            
            {}
            <button 
                onClick={() => dispatch(toggleVoice(true))}
                className="w-14 h-14 rounded-full vault-gradient p-[2px] shadow-lg vault-glow active:scale-95 transition-transform"
            >
                <div className="w-full h-full rounded-full vault-gradient flex items-center justify-center overflow-hidden relative">
                    <div className="absolute inset-0 bg-white/20 blur-md"></div>
                    <Mic size={24} className="text-white relative z-10" />
                </div>
            </button>

            {}
            <div className="flex-1 flex items-center justify-end gap-8 ml-4">
                
                {}
                <NavBtn 
                    icon={Home} 
                    label="Home" 
                    isActive={activeRoute === 'home'} 
                    onClick={() => navigate('/home')} 
                />

                {}
                <NavBtn 
                    icon={MessageSquare} 
                    label="Chat" 
                    isActive={activeRoute === 'chat'} 
                    onClick={() => navigate('/chat')} 
                />

                {}
                <NavBtn 
                    icon={Grid} 
                    label="Menu" 
                    isActive={activeRoute === 'menu'} 
                    onClick={() => navigate('/profile')} 
                />

            </div>

        </div>
    );
};


const NavBtn = ({ icon: Icon, label, isActive, onClick }) => (
    <button 
        onClick={onClick} 
        className="flex flex-col items-center justify-center gap-1 w-12 h-full transition-colors group"
    >
        <Icon 
            size={24} 
            strokeWidth={isActive ? 2.5 : 2} 
            className={isActive ? 'text-vault-cyan' : 'text-gray-400 dark:text-slate-500 group-hover:text-gray-600 dark:group-hover:text-slate-300'} 
        />
        <span className={`text-[11px] font-bold ${isActive ? 'text-vault-cyan' : 'text-gray-400 dark:text-slate-500 group-hover:text-gray-600 dark:group-hover:text-slate-300'}`}>
            {label}
        </span>
    </button>
);

export default BottomNav;