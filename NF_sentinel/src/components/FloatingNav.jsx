import { useNavigate } from 'react-router-dom';
import React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { toggleVoice } from '../features/uiSlice';
import { Home, MessageSquare, Grid, Mic, Waves } from 'lucide-react';

const FloatingNav = () => {
  const navigate = useNavigate();

  const dispatch = useDispatch();
  const { activeRoute, isAuthenticated } = useSelector(state => ({ ...state.ui, ...state.auth }));
  
  if (!isAuthenticated || ['welcome', 'login', 'signup', 'adminLogin', 'adminDashboard'].includes(activeRoute)) return null;

  return (
    <div className="fixed bottom-6 w-full max-w-md px-6 z-40 flex items-center justify-between pointer-events-none">
      
      {}
      <button 
        onClick={() => dispatch(toggleVoice(true))}
        className="pointer-events-auto w-14 h-14 rounded-full bg-gradient-to-b from-[#A01030] to-[#700b21] shadow-xl shadow-red-900/30 flex items-center justify-center border-2 border-white/20 active:scale-90 transition-transform"
      >
        <Waves className="text-white w-6 h-6 animate-pulse" />
      </button>

      {}
      <div className="pointer-events-auto flex-1 ml-4 h-16 bg-white rounded-[32px] shadow-[0_8px_30px_rgba(0,0,0,0.08)] flex items-center justify-between px-8 border border-gray-100">
        <NavBtn 
            icon={Home} 
            label="Home" 
            isActive={activeRoute === 'home'} 
            onClick={() => navigate('/home')} 
        />
        <NavBtn 
            icon={MessageSquare} 
            label="Chat" 
            isActive={activeRoute === 'chat'} 
            onClick={() => navigate('/chat')} 
        />
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
    <button onClick={onClick} className="flex flex-col items-center gap-1 group">
        <Icon size={22} strokeWidth={isActive ? 3 : 2} className={isActive ? 'text-[#A01030]' : 'text-gray-300 group-hover:text-gray-500'} />
        <span className={`text-[9px] font-bold ${isActive ? 'text-[#A01030]' : 'text-gray-300 group-hover:text-gray-500'}`}>
            {label}
        </span>
    </button>
);

export default FloatingNav;