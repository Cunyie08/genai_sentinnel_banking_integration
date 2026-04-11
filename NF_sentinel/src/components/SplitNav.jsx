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
    <div className="fixed bottom-0 w-full max-w-md px-6 pb-6 pt-2 z-50 flex items-end justify-between bg-gradient-to-t from-white via-white to-transparent pointer-events-none">
      
      {}
      <button 
        onClick={() => dispatch(toggleVoice(true))}
        className="pointer-events-auto w-14 h-14 rounded-full bg-gradient-to-tr from-[#A01030] to-[#FF4D6D] shadow-lg shadow-red-900/30 flex items-center justify-center border-2 border-white animate-pulse"
      >
        <Mic className="text-white w-6 h-6" />
      </button>

      {}
      <div className="pointer-events-auto bg-white border border-gray-100 shadow-xl rounded-full px-6 py-3 flex gap-8 items-center h-16">
        <button 
          onClick={() => navigate('/home')}
          className={`flex flex-col items-center gap-1 ${activeRoute === 'home' ? 'text-[#A01030]' : 'text-gray-400'}`}
        >
          <Home size={22} strokeWidth={activeRoute === 'home' ? 2.5 : 2} />
          <span className="text-[10px] font-bold">Home</span>
        </button>
        
        <button 
          onClick={() => navigate('/chat')}
          className={`flex flex-col items-center gap-1 ${activeRoute === 'chat' ? 'text-[#A01030]' : 'text-gray-400'}`}
        >
          <MessageSquare size={22} strokeWidth={activeRoute === 'chat' ? 2.5 : 2} />
          <span className="text-[10px] font-bold">Chat</span>
        </button>
        
        <button 
          onClick={() => navigate('/profile')}
          className={`flex flex-col items-center gap-1 ${activeRoute === 'menu' ? 'text-[#A01030]' : 'text-gray-400'}`}
        >
          <Grid size={22} strokeWidth={activeRoute === 'menu' ? 2.5 : 2} />
          <span className="text-[10px] font-bold">Menu</span>
        </button>
      </div>
    </div>
  );
};
export default SplitNav;