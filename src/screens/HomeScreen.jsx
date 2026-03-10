import { useNavigate } from 'react-router-dom';
import React, { useState, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { dismissWelcome, triggerPayment } from "../features/uiSlice"; 
import { fetchDashboard } from "../features/accountSlice";
import { api } from "../api/axiosConfig";
import {
  Bell, Eye, EyeOff, Copy, QrCode, Send, Plus, Clock, FileText,
  Smartphone, Wifi, Gamepad2, Zap, Sparkles, X, Settings
} from "lucide-react";

const InjectStyles = () => (
  <style>{`
    @keyframes slideLeft {
      0%   { transform: translateX(0); }
      100% { transform: translateX(-50%); }
    }
    .marquee-track {
      display: flex;
      width: max-content;
      gap: 1rem;
      animation: slideLeft 22s linear infinite;
    }
    .marquee-track:hover { animation-play-state: paused; }

    @keyframes fadeUp {
      from { opacity: 0; transform: translateY(12px); }
      to   { opacity: 1; transform: translateY(0); }
    }
    .fu  { animation: fadeUp 0.38s ease both; }
    .fu1 { animation-delay: 0.04s; }
    .fu2 { animation-delay: 0.10s; }
    .fu3 { animation-delay: 0.18s; }
    .fu4 { animation-delay: 0.26s; }
    .fu5 { animation-delay: 0.34s; }
  `}</style>
);

const HomeScreen = () => {
  const navigate = useNavigate();

  const dispatch = useDispatch();
  const user = useSelector((state) => state.auth.user);
  const account = useSelector((state) => state.account?.details); 
  const showPopup = useSelector((state) => state.ui.showWelcome);
  
  const [showBal, setShowBal] = useState(true);
  const [feedCards, setFeedCards] = useState([]);
  const [loadingFeed, setLoadingFeed] = useState(true);

  
  useEffect(() => {
    dispatch(fetchDashboard());

    const loadFeed = async () => {
      try {
        const res = await api.getSmartFeed({ userId: user?.id });
        if (res?.data?.cards) {
          setFeedCards(res.data.cards);
        }
      } catch (err) {
        console.error("Feed error:", err);
      } finally {
        setLoadingFeed(false);
      }
    };

    const checkPayments = async () => {
      try {
        setTimeout(async () => {
          const res = await api.checkPaymentRequest();
          if (res.data && res.data.id) {
            dispatch(triggerPayment()); 
          }
        }, 2000);
      } catch (err) {}
    };

    loadFeed();
    checkPayments();
  }, [dispatch, user?.id]);

  useEffect(() => {
    if (showPopup) {
      const timer = setTimeout(() => dispatch(dismissWelcome()), 5000);
      return () => clearTimeout(timer);
    }
  }, [showPopup, dispatch]);

  const quickItems = [
    { icon: Smartphone, label: "Airtime",     route: "airtime" },
    { icon: Wifi,       label: "Data",        route: "data" },
    { icon: Gamepad2,   label: "Betting",     route: "betting" },
    { icon: Zap,        label: "Electricity", route: "bills" },
  ];

  return (
    <div className="min-h-full w-full bg-[#F8F9FB] font-sans relative">
      <InjectStyles />

      {/* Popup / Modal area */}
      {showPopup && (
        <div
          className="fixed top-0 left-0 right-0 bottom-0 z-[9999] flex items-center justify-center bg-black/60 backdrop-blur-sm"
          onClick={(e) => { if (e.target === e.currentTarget) dispatch(dismissWelcome()); }}
        >
          <div
            className="relative bg-gradient-to-br from-[#2F4F4F] to-[#1A2E2E] text-white shadow-2xl border border-white/10"
            style={{ width: "min(92vw, 360px)", borderRadius: "28px", padding: "clamp(20px, 4vw, 28px)" }}
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => dispatch(dismissWelcome())}
              className="absolute top-4 right-4 w-8 h-8 bg-white/10 rounded-full flex items-center justify-center hover:bg-white/20 active:scale-90 transition-all z-20"
            >
              <X size={16} />
            </button>
            <div className="absolute top-0 right-0 w-32 h-32 bg-white/5 rounded-full blur-2xl -mr-10 -mt-10 pointer-events-none" />
            <div className="relative z-10">
              <span className="text-[10px] font-bold text-[#FFD700] uppercase tracking-wider mb-2 block">Education First</span>
              <h3 className="text-xl sm:text-2xl font-black leading-tight mb-2">Student Loan<br />Up to ₦500k</h3>
              <p className="text-white/70 text-xs mb-6 leading-relaxed">Zero interest for the first 3 months. Apply instantly to secure your tuition fees.</p>
              <div className="space-y-3">
                <button onClick={() => dispatch(dismissWelcome())} className="w-full bg-white text-[#2F4F4F] text-xs font-extrabold py-3.5 rounded-full shadow-lg active:scale-95 hover:shadow-xl transition-all">APPLY NOW</button>
                <button type="button" onClick={() => dispatch(dismissWelcome())} className="w-full text-white/50 text-[10px] font-bold uppercase tracking-widest hover:text-white active:text-white transition-colors py-1 cursor-pointer">Cancel</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* New Header + Balance Area */}
      <div className="w-full bg-gradient-to-br from-[#800020] via-[#A01030] to-[#5a0a1e] text-white px-4 sm:px-6 xl:px-8 pt-8 pb-6 rounded-b-[32px] shadow-lg shadow-red-900/10 mb-6 relative z-20">
        <div className="flex justify-between items-center mb-6 fu fu1">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-full overflow-hidden shrink-0 bg-white/10 border-2 border-white/20">
              <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${user?.name || 'Lukman'}`} alt="User" className="w-full h-full object-cover" />
            </div>
            <div>
              <p className="text-white/90 text-[13px] font-medium leading-none mb-1">Good Afternoon</p>
              <h2 className="text-lg font-bold leading-tight">{user?.name || "Lukman"}</h2>
            </div>
          </div>
          <div className="flex gap-2">
            <button className="relative w-10 h-10 flex items-center justify-center text-white hover:bg-white/10 rounded-full transition-colors">
              <Bell size={22} />
              <span className="absolute top-2 right-2.5 w-2 h-2 bg-red-500 rounded-full border border-red-900" />
            </button>
            <button className="w-10 h-10 flex items-center justify-center text-white hover:bg-white/10 rounded-full transition-colors">
              <Settings size={22} />
            </button>
          </div>
        </div>

        <div className="flex items-center gap-2 mb-4 fu fu2">
          <span className="text-white/80 text-[12px] sm:text-[13px] font-medium">Tier {account?.tier || '3'} Savings Account | <span className="text-white font-bold">{account?.number || '0244037192'}</span></span>
          <button className="text-white hover:text-white/80 transition-colors">
            <Copy size={16} />
          </button>
        </div>

        <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl p-5 relative fu fu3">
          <div className="absolute top-0 right-0 bg-white text-green-700 text-[11px] font-bold px-3 py-1 rounded-bl-[14px] rounded-tr-[14px]">
            Active
          </div>
          <p className="text-white text-sm font-medium mb-1.5">Account Balance</p>
          <div className="flex items-center gap-2 mb-6">
            <h1 className="text-4xl font-extrabold tracking-tight">
              {showBal ? `₦${Number(account?.balance || 336.97).toLocaleString(undefined, { minimumFractionDigits: 2 })}` : "••••••••"}
            </h1>
            <button onClick={() => setShowBal(!showBal)} className="text-white/80 hover:text-white transition-colors focus:outline-none">
              {showBal ? <EyeOff size={22} /> : <Eye size={22} />}
            </button>
          </div>

          <div className="grid grid-cols-2 gap-3 pt-2">
            <button onClick={() => navigate('/fund')} className="w-full flex items-center justify-center gap-2 py-3 bg-transparent border border-white/50 shadow-sm rounded-xl hover:bg-white/10 transition-colors font-semibold text-sm">
              <Plus size={18} /> Fund Account
            </button>
            <button onClick={() => navigate('/history')} className="w-full flex items-center justify-center gap-2 py-3 bg-transparent border border-white/50 shadow-sm rounded-xl hover:bg-white/10 transition-colors font-semibold text-sm">
              <FileText size={18} /> History
            </button>
          </div>
        </div>
      </div>

      <div className="w-full px-4 sm:px-6 xl:px-8 py-2 pb-24 md:pb-10 space-y-6">

        {/* Send Action */}
        <div className="fu fu3 grid grid-cols-3 gap-3 sm:gap-4 xl:gap-6 w-full">
            <button
              onClick={() => navigate('/send')}
              className="w-full h-full min-h-[85px] md:min-h-[100px] bg-[#A01030] rounded-2xl md:rounded-3xl flex flex-col items-center justify-center gap-2 text-white shadow-xl shadow-red-900/20 active:scale-95 hover:scale-[1.03] transition-transform p-3"
            >
              <Send className="w-6 h-6 md:w-8 md:h-8" />
              <span className="text-[11px] sm:text-xs md:text-sm font-bold truncate">Send</span>
            </button>
            <button
              onClick={() => navigate('/bills')}
              className="w-full h-full min-h-[85px] md:min-h-[100px] bg-white rounded-2xl md:rounded-3xl flex flex-col items-center justify-center gap-2 text-[#A01030] shadow-sm border border-gray-100 active:scale-95 hover:scale-[1.03] transition-transform p-3"
            >
              <FileText className="w-6 h-6 md:w-8 md:h-8" />
              <span className="text-[11px] sm:text-xs md:text-sm font-bold truncate text-gray-700">Pay Bills</span>
            </button>
            <button
              onClick={() => navigate('#')}
              className="w-full h-full min-h-[85px] md:min-h-[100px] bg-white rounded-2xl md:rounded-3xl flex flex-col items-center justify-center gap-2 text-[#A01030] shadow-sm border border-gray-100 active:scale-95 hover:scale-[1.03] transition-transform p-3"
            >
              <QrCode className="w-6 h-6 md:w-8 md:h-8" />
              <span className="text-[11px] sm:text-xs md:text-sm font-bold truncate text-gray-700">Cards</span>
            </button>
        </div>

        {/* Quick Access */}
        <div className="fu fu4">
          <div className="flex justify-between items-center mb-3 sm:mb-4 xl:mb-5">
            <h3 className="font-bold text-gray-900 text-sm md:text-base xl:text-lg">Quick Access</h3>
            <span className="text-xs md:text-sm font-bold text-[#A01030] cursor-pointer hover:underline">View All</span>
          </div>
          <div className="grid grid-cols-4 gap-3 md:gap-5 xl:gap-8">
            {quickItems.map((item, idx) => (
              <div key={idx} onClick={() => navigate(item.route)} className="flex flex-col items-center gap-2 xl:gap-3 cursor-pointer group">
                <div className="w-14 h-14 sm:w-16 sm:h-16 xl:w-20 xl:h-20 bg-[#FFF5F7] rounded-[20px] xl:rounded-[24px] flex items-center justify-center text-[#A01030] group-hover:bg-rose-100 group-active:scale-90 transition-all">
                  <item.icon className="w-6 h-6 xl:w-8 xl:h-8" />
                </div>
                <span className="text-[10px] sm:text-xs md:text-sm font-bold text-gray-500 text-center">{item.label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Smart Feed */}
        <div className="fu fu5 overflow-hidden pb-2">
          <div className="flex items-center gap-2 mb-3 sm:mb-4 xl:mb-5">
            <h3 className="font-bold text-gray-900 text-sm md:text-base xl:text-lg">Smart Feed</h3>
            <span className="bg-[#FCE7F3] text-[#BE185D] text-[9px] md:text-[10px] font-black px-2 py-0.5 rounded-md uppercase tracking-wide">AI Powered</span>
          </div>
          <div className="relative w-full overflow-hidden">
            {loadingFeed ? (
              <div className="flex gap-4">
                 {[1,2].map(i => <div key={i} className="w-[240px] h-[145px] bg-gray-100 rounded-[24px] animate-pulse"></div>)}
              </div>
            ) : (
              <div className="marquee-track">
                {feedCards?.length > 0 && [...feedCards, ...feedCards].map((card, i) => (
                  <div 
                    key={`${card.id}-${i}`}
                    className="w-[240px] sm:w-[280px] xl:w-[300px] h-[145px] xl:h-[160px] rounded-[24px] sm:rounded-[28px] p-5 sm:p-6 text-white flex flex-col justify-between shrink-0 shadow-lg relative overflow-hidden"
                    style={{ background: card.gradient ? `linear-gradient(to right, ${card.gradient[0]}, ${card.gradient[1]})` : '#333' }}
                  >
                    <div className="absolute right-0 top-0 w-32 h-32 bg-white/5 rounded-full blur-3xl -mr-10 -mt-10 pointer-events-none" />
                    <div>
                      <span className="text-[10px] font-bold uppercase tracking-wider mb-1.5 block" style={{ color: card.labelColor || '#fff' }}>
                        {card.label}
                      </span>
                      <h3 className="text-lg sm:text-xl font-bold leading-tight">{card.title}<br />{card.subtitle}</h3>
                    </div>
                    <button 
                      onClick={() => card.ctaRoute && navigate(card.ctaRoute)}
                      className="bg-white text-[10px] font-bold px-5 py-2.5 rounded-full w-fit hover:shadow-md active:scale-95 transition-all"
                      style={{ color: card.gradient?.[0] || '#000' }}
                    >
                      {card.cta}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomeScreen;