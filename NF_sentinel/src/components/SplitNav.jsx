import { useNavigate } from 'react-router-dom';
import React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Home, MessageSquare, Grid, Mic } from 'lucide-react';
import { toggleVoice } from '../features/uiSlice';

const SplitNav = () => {
  const navigate = useNavigate();

  const dispatch = useDispatch();
  const { activeRoute, isAuthenticated } = useSelector(state => ({ ...state.ui, ...state.auth }));

  
  if (!isAuthenticated || ['login', 'welcome', 'adminDashboard', 'adminLogin'].includes(activeRoute)) return null;

  return (
    <div className="fixed bottom-0 w-full max-w-md px-6 pb-6 pt-2 z-50 flex items-end justify-between bg-gradient-to-t from-white dark:from-vault-dark-bg via-white/80 dark:via-vault-dark-bg/80 to-transparent pointer-events-none">
      
      {}
      <button 
        onClick={() => dispatch(toggleVoice(true))}
        className="pointer-events-auto w-14 h-14 rounded-full vault-gradient shadow-lg vault-glow flex items-center justify-center border-2 border-white/20 dark:border-white/10 animate-pulse"
      >
        <Mic className="text-white w-6 h-6" />
      </button>

      {}
      <div className="pointer-events-auto bg-white dark:bg-vault-dark-card border border-gray-100 dark:border-white/5 shadow-xl rounded-full px-6 py-3 flex gap-8 items-center h-16 vault-transition">
        <button 
          onClick={() => navigate('/home')}
          className={`flex flex-col items-center gap-1 ${activeRoute === 'home' ? 'text-vault-cyan' : 'text-gray-400 dark:text-slate-500'}`}
        >
          <Home size={22} strokeWidth={activeRoute === 'home' ? 2.5 : 2} />
          <span className="text-[10px] font-bold">Home</span>
        </button>
        
        <button 
          onClick={() => navigate('/chat')}
          className={`flex flex-col items-center gap-1 ${activeRoute === 'chat' ? 'text-vault-cyan' : 'text-gray-400 dark:text-slate-500'}`}
        >
          <MessageSquare size={22} strokeWidth={activeRoute === 'chat' ? 2.5 : 2} />
          <span className="text-[10px] font-bold">Chat</span>
        </button>
        
        <button 
          onClick={() => navigate('/profile')}
          className={`flex flex-col items-center gap-1 ${activeRoute === 'menu' ? 'text-vault-cyan' : 'text-gray-400 dark:text-slate-500'}`}
        >
          <Grid size={22} strokeWidth={activeRoute === 'menu' ? 2.5 : 2} />
          <span className="text-[10px] font-bold">Menu</span>
        </button>
      </div>
    </div>
  );
};
export default SplitNav;