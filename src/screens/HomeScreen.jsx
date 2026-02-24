import React, { useState, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { setRoute, dismissWelcome } from "../features/uiSlice";
import {
  Bell,
  Eye,
  EyeOff,
  Copy,
  QrCode,
  Send,
  Plus,
  Clock,
  FileText,
  Smartphone,
  Wifi,
  Gamepad2,
  Zap,
  Sparkles,
  X,
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
  const dispatch = useDispatch();
  const user = useSelector((state) => state.auth.user);
  const showPopup = useSelector((state) => state.ui.showWelcome);
  const [showBal, setShowBal] = useState(true);

  useEffect(() => {
    if (showPopup) {
      const timer = setTimeout(() => dispatch(dismissWelcome()), 5000);
      return () => clearTimeout(timer);
    }
  }, [showPopup, dispatch]);

  const actions = [
    {
      label: "Send",
      icon: Send,
      route: "send",
      bg: "bg-[#A01030]",
      color: "text-white",
    },
    {
      label: "Fund",
      icon: Plus,
      route: "fund",
      bg: "bg-white",
      color: "text-gray-900",
    },
    {
      label: "History",
      icon: Clock,
      route: "history",
      bg: "bg-white",
      color: "text-gray-900",
    },
    {
      label: "Bills",
      icon: FileText,
      route: "bills",
      bg: "bg-white",
      color: "text-gray-900",
    },
  ];

  const quickItems = [
    { icon: Smartphone, label: "Airtime", route: "airtime" },
    { icon: Wifi, label: "Data", route: "data" },
    { icon: Gamepad2, label: "Betting", route: "betting" },
    { icon: Zap, label: "Electricity", route: "bills" },
  ];

  return (
    <div className="min-h-full w-full bg-[#F8F9FB] font-sans relative">
      <InjectStyles />

      {/* ── NOTIFICATION POPUP ─────────────────────────────────────────────── */}
      {showPopup && (
        <div
          className="fixed top-0 left-0 right-0 bottom-0 z-[9999] flex items-center justify-center bg-black/60 backdrop-blur-sm"
          style={{ position: "fixed", inset: 0 }}
          onClick={(e) => {
            if (e.target === e.currentTarget) dispatch(dismissWelcome());
          }}
        >
          <div
            className="relative bg-gradient-to-br from-[#2F4F4F] to-[#1A2E2E] text-white shadow-2xl border border-white/10"
            style={{
              width: "min(92vw, 360px)",
              borderRadius: "28px",
              padding: "clamp(20px, 4vw, 28px)",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* X Close button */}
            <button
              onClick={() => dispatch(dismissWelcome())}
              className="absolute top-4 right-4 w-8 h-8 bg-white/10 rounded-full flex items-center justify-center hover:bg-white/20 active:scale-90 transition-all z-20"
              aria-label="Close"
            >
              <X size={16} />
            </button>

            {/* Decorative blob */}
            <div className="absolute top-0 right-0 w-32 h-32 bg-white/5 rounded-full blur-2xl -mr-10 -mt-10 pointer-events-none" />

            <div className="relative z-10">
              <span className="text-[10px] font-bold text-[#FFD700] uppercase tracking-wider mb-2 block">
                Education First
              </span>
              <h3 className="text-xl sm:text-2xl font-black leading-tight mb-2">
                Student Loan
                <br />
                Up to ₦500k
              </h3>
              <p className="text-white/70 text-xs mb-6 leading-relaxed">
                Zero interest for the first 3 months. Apply instantly to secure
                your tuition fees.
              </p>
              <div className="space-y-3">
                <button
                  onClick={() => dispatch(dismissWelcome())}
                  className="w-full bg-white text-[#2F4F4F] text-xs font-extrabold py-3.5 rounded-full shadow-lg active:scale-95 hover:shadow-xl transition-all"
                >
                  APPLY NOW
                </button>
                {/* ← This is the cancel/dismiss button — always works */}
                <button
                  type="button"
                  onClick={() => dispatch(dismissWelcome())}
                  className="w-full text-white/50 text-[10px] font-bold uppercase tracking-widest hover:text-white active:text-white transition-colors py-1 cursor-pointer"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── HEADER ─────────────────────────────────────────────────────────── */}
      <header className="w-full px-4 sm:px-6 xl:px-8 pt-8 pb-4 flex justify-between items-center bg-[#F8F9FB]/95 backdrop-blur-sm sticky top-0 z-20 border-b border-gray-100">
        <div className="flex items-center gap-3 fu fu1">
          <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-full bg-[#E5E7EB] overflow-hidden border-2 border-white shadow-sm shrink-0 md:hidden">
            <img
              src="https://api.dicebear.com/7.x/avataaars/svg?seed=Tunde"
              alt="User"
              className="w-full h-full"
            />
          </div>
          <div>
            <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest leading-none mb-0.5">
              Good Afternoon
            </p>
            <h2 className="text-base sm:text-lg xl:text-xl font-extrabold text-gray-900 leading-tight">
              {user?.name || "Tunde"}
            </h2>
          </div>
        </div>
        <div className="flex gap-2 sm:gap-3 fu fu1">
          <button className="w-9 h-9 sm:w-10 sm:h-10 xl:w-12 xl:h-12 rounded-full bg-white flex items-center justify-center shadow-sm text-[#A01030] hover:bg-rose-50 transition-colors">
            <Sparkles
              className="w-4 h-4 sm:w-5 sm:h-5 xl:w-6 xl:h-6"
              fill="currentColor"
            />
          </button>
          <button className="w-9 h-9 sm:w-10 sm:h-10 xl:w-12 xl:h-12 rounded-full bg-white flex items-center justify-center shadow-sm text-gray-600 relative hover:bg-gray-50 transition-colors">
            <Bell className="w-4 h-4 sm:w-5 sm:h-5 xl:w-6 xl:h-6" />
            <span className="absolute top-2 right-2.5 xl:top-2.5 xl:right-3 w-2 h-2 bg-red-500 rounded-full border border-white" />
          </button>
        </div>
      </header>

      {/* ── MAIN CONTENT ───────────────────────────────────────────────────── */}
      <div className="w-full px-4 sm:px-6 xl:px-8 py-5 sm:py-6 xl:py-8 pb-24 md:pb-10 space-y-5 sm:space-y-6">
        {/* ── BALANCE CARD ─────────────────────────────────────────────────── */}
        <div className="fu fu2 w-full bg-gradient-to-br from-[#9F1239] to-[#881337] rounded-[24px] xl:rounded-[32px] p-5 sm:p-6 xl:p-8 text-white shadow-xl shadow-red-900/20 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-72 h-72 bg-white/5 rounded-full blur-3xl -mr-24 -mt-24 pointer-events-none" />

          {/* Top row: label + eye toggle + premium badge */}
          <div className="flex justify-between items-start mb-4 relative z-10">
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium uppercase tracking-widest opacity-80">
                Total Balance
              </span>
              <button
                onClick={() => setShowBal(!showBal)}
                className="opacity-70 hover:opacity-100 transition-opacity focus:outline-none"
                aria-label={showBal ? "Hide balance" : "Show balance"}
              >
                {showBal ? <Eye size={16} /> : <EyeOff size={16} />}
              </button>
            </div>
            <div className="bg-[#B45309]/80 backdrop-blur-md px-3 py-1 rounded-full border border-white/10">
              <span className="text-[10px] font-bold text-[#FFD700] uppercase tracking-wider">
                PREMIUM
              </span>
            </div>
          </div>

          {/* Balance amount */}
          <h1 className="text-3xl sm:text-4xl xl:text-5xl font-black tracking-tighter mb-8 xl:mb-10 relative z-10">
            {showBal ? "₦ 4,850,200.50" : "••••••••••"}
          </h1>

          {/* Account number + QR */}
          <div className="flex justify-between items-end relative z-10">
            <div>
              <p className="text-[10px] text-white/60 uppercase font-bold mb-1 tracking-widest">
                Savings Account
              </p>
              <div className="flex items-center gap-2">
                <span className="text-sm font-mono font-bold tracking-wider">
                  0123456789
                </span>
                <Copy
                  size={13}
                  className="opacity-60 cursor-pointer hover:opacity-100 transition-opacity"
                />
              </div>
            </div>
            <div className="w-10 h-10 xl:w-12 xl:h-12 bg-white/10 rounded-2xl flex items-center justify-center backdrop-blur-md border border-white/10 cursor-pointer hover:bg-white/20 transition-colors">
              <QrCode size={22} />
            </div>
          </div>
        </div>

        {/* ── ACTION BUTTONS ───────────────────────────────────────────────── */}
        <div className="fu fu3 flex gap-3 sm:gap-4 xl:gap-6">
          {actions.map((action, i) => (
            <div key={i} className="flex flex-col items-center gap-2 flex-1">
              <button
                onClick={() => dispatch(setRoute(action.route))}
                className={`w-14 h-14 sm:w-16 sm:h-16 md:w-18 md:h-18 xl:w-20 xl:h-20 
          ${action.bg} rounded-[18px] md:rounded-[22px] xl:rounded-[26px] 
          flex items-center justify-center ${action.color} 
          shadow-sm border border-gray-100 active:scale-95 
          hover:scale-[1.06] transition-transform`}
              >
                <action.icon className="w-6 h-6 md:w-7 md:h-7 xl:w-8 xl:h-8" />
              </button>
              <span className="text-[11px] sm:text-xs md:text-sm font-bold text-gray-700">
                {action.label}
              </span>
            </div>
          ))}
        </div>
        {/* ── QUICK ACCESS ─────────────────────────────────────────────────── */}
        <div className="fu fu4">
          <div className="flex justify-between items-center mb-3 sm:mb-4 xl:mb-5">
            <h3 className="font-bold text-gray-900 text-sm md:text-base xl:text-lg">
              Quick Access
            </h3>
            <span className="text-xs md:text-sm font-bold text-[#A01030] cursor-pointer hover:underline">
              View All
            </span>
          </div>
          <div className="grid grid-cols-4 gap-3 md:gap-5 xl:gap-8">
            {quickItems.map((item, idx) => (
              <div
                key={idx}
                onClick={() => dispatch(setRoute(item.route))}
                className="flex flex-col items-center gap-2 xl:gap-3 cursor-pointer group"
              >
                <div className="w-14 h-14 sm:w-16 sm:h-16 md:w-20 md:h-20 xl:w-24 xl:h-24 bg-[#FFF5F7] rounded-[20px] md:rounded-[24px] xl:rounded-[28px] flex items-center justify-center text-[#A01030] group-hover:bg-rose-100 group-active:scale-90 transition-all">
                  <item.icon className="w-6 h-6 md:w-8 md:h-8 xl:w-10 xl:h-10" />
                </div>
                <span className="text-[10px] sm:text-xs md:text-sm font-bold text-gray-500 text-center">
                  {item.label}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* ── SMART FEED ───────────────────────────────────────────────────── */}
        <div className="fu fu5 overflow-hidden pb-2">
          <div className="flex items-center gap-2 mb-3 sm:mb-4 xl:mb-5">
            <h3 className="font-bold text-gray-900 text-sm md:text-base xl:text-lg">
              Smart Feed
            </h3>
            <span className="bg-[#FCE7F3] text-[#BE185D] text-[9px] md:text-[10px] font-black px-2 py-0.5 rounded-md uppercase tracking-wide">
              AI Powered
            </span>
          </div>
          <div className="relative w-full overflow-hidden">
            <div className="marquee-track">
              {[1, 2, 3, 4].map((i) => (
                <React.Fragment key={i}>
                  {/* Card 1 */}
                  <div className="w-[240px] sm:w-[280px] xl:w-[300px] h-[145px] xl:h-[160px] rounded-[24px] sm:rounded-[28px] bg-gradient-to-r from-[#2F4F4F] to-[#1F2F2F] p-5 sm:p-6 text-white flex flex-col justify-between shrink-0 shadow-lg relative overflow-hidden">
                    <div className="absolute right-0 top-0 w-32 h-32 bg-white/5 rounded-full blur-3xl -mr-10 -mt-10 pointer-events-none" />
                    <div>
                      <span className="text-[10px] font-bold text-[#FFD700] uppercase tracking-wider mb-1.5 block">
                        Education First
                      </span>
                      <h3 className="text-lg sm:text-xl font-bold leading-tight">
                        Student Loan
                        <br />
                        Up to ₦500k
                      </h3>
                    </div>
                    <button className="bg-white text-[#2F4F4F] text-[10px] font-bold px-5 py-2.5 rounded-full w-fit hover:shadow-md active:scale-95 transition-all">
                      APPLY NOW
                    </button>
                  </div>

                  {/* Card 2 */}
                  <div className="w-[240px] sm:w-[280px] xl:w-[300px] h-[145px] xl:h-[160px] rounded-[24px] sm:rounded-[28px] bg-gradient-to-r from-[#0F766E] to-[#0D5E56] p-5 sm:p-6 text-white flex flex-col justify-between shrink-0 shadow-lg relative overflow-hidden">
                    <div>
                      <span className="text-[10px] font-bold text-[#6EE7B7] uppercase tracking-wider mb-1.5 block">
                        High Yield
                      </span>
                      <h3 className="text-lg sm:text-xl font-bold leading-tight">
                        Fixed Deposit
                        <br />
                        15% Interest
                      </h3>
                    </div>
                    <button className="bg-white text-[#0F766E] text-[10px] font-bold px-5 py-2.5 rounded-full w-fit hover:shadow-md active:scale-95 transition-all">
                      START SAVING
                    </button>
                  </div>
                </React.Fragment>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomeScreen;
