import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import {
  ChevronLeft, Send, Bot, ChevronRight,
  AlertTriangle, CheckCircle,
  HelpCircle, MessageSquareWarning, Loader2
} from 'lucide-react';
import { api } from '../api/axiosConfig';

// ─── Escalation steps after FAQ miss ──────────────────────────────────────────
const ESC_STEPS = { IDLE: 0, ACCOUNT: 1, SENDING: 2, DONE: 3, ERROR: 4 };

const ChatScreen = () => {
  const navigate   = useNavigate();
  const user       = useSelector(s => s.auth.user);
  const accounts   = user?.accounts || [];

  // ── UI state ──────────────────────────────────────────────────────────────
  const [messages,     setMessages]     = useState([]);
  const [faqQuery,     setFaqQuery]     = useState('');
  const [faqLoading,   setFaqLoading]   = useState(false);

  // Escalation state
  const [escStep,      setEscStep]      = useState(ESC_STEPS.IDLE);
  const [escQuery,     setEscQuery]     = useState('');   // the original query that had no FAQ match
  const [escAccount,   setEscAccount]   = useState('');
  const [escAccountObj,setEscAccountObj]= useState(null);
  const [escResult,    setEscResult]    = useState(null);
  const [escError,     setEscError]     = useState('');

  const scrollRef = useRef(null);

  // Greet on mount
  useEffect(() => {
    const firstName = user?.name?.split(' ')[0] || 'there';
    setMessages([{
      id: 1, sender: 'ai', type: 'text',
      text: `Hello ${firstName}! How can I help you with your account today? You can ask about:`,
      options: ['Transaction Discrepancy', 'Card Issues & Limits', 'Report Fraudulent Activity'],
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }]);
  }, [user?.name]);

  // Auto-scroll
  useEffect(() => {
    if (scrollRef.current)
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, faqLoading, escStep]);

  // ── Helper: add message ────────────────────────────────────────────────
  const addMsg = (msg) => setMessages(prev => [...prev, msg]);
  const now = () => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  // ── FAQ send ───────────────────────────────────────────────────────────
  const handleFaqSend = async (overrideQuery) => {
    const q = (overrideQuery || faqQuery).trim();
    if (!q) return;
    setFaqQuery('');
    // Reset any previous escalation
    setEscStep(ESC_STEPS.IDLE);
    setEscQuery('');
    setEscResult(null);

    // User bubble
    addMsg({ id: Date.now(), sender: 'user', type: 'text', text: q, time: now() });
    setFaqLoading(true);
    try {
      console.log('[FAQ] Sending query to backend:', q);
      const res = await api.getFaqs(q);
      console.log('[FAQ] Raw response from backend:', res?.data);

      // Backend returns { success: true, match: { answer, question, ... } } on hit
      // and { success: false, message: "..." } on miss
      const d = res?.data || {};
      const matchFound = d.success === true;
      const answer = matchFound
        ? (d.match?.answer || 'See our FAQ for more details.')
        : (d.message || "I couldn't find a specific answer to your question in our FAQs.");

      console.log('[FAQ] Match found:', matchFound, '| Answer preview:', answer?.substring(0, 80));

      if (!matchFound) {
        // No FAQ match — show answer + escalation option
        addMsg({
          id: Date.now(), sender: 'ai', type: 'escalation',
          text: answer,
          time: now(),
        });
        setEscQuery(q); // store for later complaint submission
      } else {
        addMsg({ id: Date.now(), sender: 'ai', type: 'text', text: answer, time: now() });
      }
    } catch (err) {
      console.error('[FAQ] Error fetching FAQ:', err?.message || err);
      addMsg({
        id: Date.now(), sender: 'ai', type: 'text',
        text: 'Could not retrieve FAQ at this time. Please try again.',
        time: now(),
      });
    } finally {
      setFaqLoading(false);
    }
  };

  // ── Escalation: submit complaint ─────────────────────────────────────
  const handleEscalateSubmit = async (accountNumber, accountObj) => {
    setEscAccount(accountNumber);
    setEscAccountObj(accountObj);
    setEscStep(ESC_STEPS.SENDING);
    try {
      const res = await api.makeComplaint({
        account_number:    accountNumber,
        complaint_channel: 'App',
        complaint_text:    escQuery,
      });
      setEscResult(res.data);
      setEscStep(ESC_STEPS.DONE);
      // Add success message to chat
      addMsg({
        id: Date.now(), sender: 'ai', type: 'routing-result',
        result: res.data,
        time: now(),
      });
    } catch (err) {
      setEscError(err?.detail || 'Failed to submit complaint. Please try again.');
      setEscStep(ESC_STEPS.ERROR);
    }
  };

  const resetEscalation = () => {
    setEscStep(ESC_STEPS.IDLE);
    setEscAccount(''); setEscAccountObj(null); setEscResult(null); setEscError('');
  };

  // ── Header ────────────────────────────────────────────────────────────
  const Header = () => (
    <div className="bg-white px-4 py-4 flex items-center justify-between border-b border-gray-100 shadow-sm shrink-0 z-20">
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate('/home')}
          className="text-gray-600 hover:bg-gray-50 p-1 rounded-full"
        >
          <ChevronLeft size={26} />
        </button>
        <div>
          <h2 className="font-extrabold text-gray-900 text-lg leading-tight">AI Support Assistant</h2>
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <p className="text-[10px] text-gray-500 uppercase font-bold tracking-wide">Always Active</p>
          </div>
        </div>
      </div>
      <div className="w-10 h-10 rounded-full bg-red-50 border border-gray-100 flex items-center justify-center">
        <Bot size={20} className="text-[#A01030]" />
      </div>
    </div>
  );

  // ── Render a message bubble ───────────────────────────────────────────
  const renderMessage = (msg) => {
    // User bubble
    if (msg.sender === 'user') {
      return (
        <div key={msg.id} className="flex flex-col items-end">
          <div className="max-w-[85%] bg-[#A01030] text-white p-4 rounded-[20px] rounded-tr-none shadow-md text-[14px] leading-relaxed font-medium">
            {msg.text}
          </div>
          <span className="text-[10px] text-gray-400 mt-1 mr-1">{msg.time} • Read</span>
        </div>
      );
    }

    // AI greeting with options
    if (msg.options) {
      return (
        <div key={msg.id} className="flex flex-col">
          <div className="flex items-center gap-2 mb-1">
            <div className="w-5 h-5 bg-red-50 text-[#A01030] rounded-full flex items-center justify-center">
              <Bot size={12} />
            </div>
            <span className="text-xs font-bold text-gray-400">AI Assistant</span>
          </div>
          <div className="bg-white p-4 rounded-[20px] rounded-tl-none shadow-sm border border-gray-100 max-w-[90%]">
            <p className="text-[14px] font-medium text-gray-800 leading-relaxed mb-3">{msg.text}</p>
            <div className="space-y-2">
              {msg.options.map((opt, i) => (
                <button
                  key={i}
                  onClick={() => handleFaqSend(opt)}
                  className="w-full flex items-center justify-between p-3 bg-gray-50 rounded-xl hover:bg-red-50 hover:text-[#A01030] text-sm font-semibold text-gray-700 transition-all group border border-gray-100"
                >
                  {opt}
                  <ChevronRight size={16} className="text-gray-400 group-hover:text-[#A01030]" />
                </button>
              ))}
            </div>
          </div>
          <span className="text-[10px] text-gray-400 mt-1">{msg.time}</span>
        </div>
      );
    }

    // Escalation message — FAQ miss with button
    if (msg.type === 'escalation') {
      return (
        <div key={msg.id} className="flex flex-col">
          <div className="flex items-center gap-2 mb-1">
            <div className="w-5 h-5 bg-red-50 text-[#A01030] rounded-full flex items-center justify-center">
              <Bot size={12} />
            </div>
            <span className="text-xs font-bold text-gray-400">AI Assistant</span>
          </div>
          <div className="bg-white p-4 rounded-[20px] rounded-tl-none shadow-sm border border-gray-100 max-w-[90%]">
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle size={16} className="text-[#A01030]" />
              <span className="text-[11px] font-black text-[#A01030] uppercase tracking-wide">Action Required</span>
            </div>
            <p className="text-[14px] font-medium text-gray-800 leading-relaxed mb-4">{msg.text}</p>

            {escStep === ESC_STEPS.IDLE && (
              <div>
                <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-2">Route to:</p>
                <div className="flex gap-3">
                  <button
                    onClick={() => setEscStep(ESC_STEPS.ACCOUNT)}
                    className="flex-1 bg-[#A01030] text-white py-3 rounded-xl font-bold text-sm shadow-lg shadow-red-900/20 active:scale-95 transition-all"
                  >
                    Escalate Now
                  </button>
                  <button
                    onClick={resetEscalation}
                    className="flex-1 bg-white text-gray-600 py-3 rounded-xl font-bold text-sm border border-gray-200 active:scale-95 transition-all"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
          <span className="text-[10px] text-gray-400 mt-1">{msg.time}</span>
        </div>
      );
    }

    // Routing result after complaint submission
    if (msg.type === 'routing-result' && msg.result) {
      const r = msg.result;
      return (
        <div key={msg.id} className="flex flex-col">
          <div className="flex items-center gap-2 mb-1">
            <div className="w-5 h-5 bg-green-50 text-green-600 rounded-full flex items-center justify-center">
              <CheckCircle size={12} />
            </div>
            <span className="text-xs font-bold text-gray-400">AI Assistant</span>
          </div>
          <div className="bg-white rounded-[20px] rounded-tl-none shadow-sm border border-gray-100 max-w-[90%] overflow-hidden">
            <div className="bg-green-50 px-4 py-3 flex items-center gap-2">
              <CheckCircle size={16} className="text-green-500" />
              <span className="text-sm font-black text-green-700">Complaint Routed Successfully</span>
            </div>
          </div>
          <span className="text-[10px] text-gray-400 mt-1">{msg.time}</span>
        </div>
      );
    }

    // Normal AI text bubble
    return (
      <div key={msg.id} className="flex flex-col">
        <div className="flex items-center gap-2 mb-1">
          <div className="w-5 h-5 bg-red-50 text-[#A01030] rounded-full flex items-center justify-center">
            <Bot size={12} />
          </div>
          <span className="text-xs font-bold text-gray-400">AI Assistant</span>
        </div>
        <div className="bg-white p-4 rounded-[20px] rounded-tl-none shadow-sm border border-gray-100 max-w-[90%] text-[14px] font-medium text-gray-800 leading-relaxed">
          {msg.text}
        </div>
        <span className="text-[10px] text-gray-400 mt-1">{msg.time}</span>
      </div>
    );
  };

  // ── Account selector for escalation ───────────────────────────────────
  const renderAccountSelector = () => {
    if (escStep !== ESC_STEPS.ACCOUNT) return null;

    return (
      <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 mx-1 mt-2">
        <p className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-1">Select Account</p>
        <p className="text-base font-black text-gray-900 mb-1">Which account is this related to?</p>
        <p className="text-xs text-gray-500 mb-4">Your complaint will be routed by our AI to the right department.</p>

        {accounts.length > 0 ? (
          <div className="space-y-3">
            {accounts.map(acc => {
              const typeLabel = acc.account_type || 'Account';
              const typeColor =
                typeLabel.toLowerCase() === 'savings'  ? { bg: 'bg-blue-50',   text: 'text-blue-700',   border: 'border-blue-200'   } :
                typeLabel.toLowerCase() === 'current'  ? { bg: 'bg-green-50',  text: 'text-green-700',  border: 'border-green-200'  } :
                typeLabel.toLowerCase() === 'solo'     ? { bg: 'bg-purple-50', text: 'text-purple-700', border: 'border-purple-200' } :
                                                         { bg: 'bg-gray-50',   text: 'text-gray-700',   border: 'border-gray-200'   };
              const num = acc.account_number?.toString() || '';
              const maskedNum = num.length >= 6
                ? num.slice(0, 4) + '••••' + num.slice(-4)
                : num;

              return (
                <button
                  key={acc.account_number}
                  onClick={() => handleEscalateSubmit(acc.account_number, acc)}
                  className="w-full flex items-center gap-4 p-4 rounded-2xl border-2 border-gray-100 bg-white hover:border-[#A01030] hover:shadow-sm text-left transition-all active:scale-[0.98]"
                >
                  <div className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 font-black text-lg ${typeColor.bg} ${typeColor.text}`}>
                    {typeLabel.charAt(0).toUpperCase()}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <p className="font-black text-gray-900 text-sm">{typeLabel} Account</p>
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide border ${typeColor.bg} ${typeColor.text} ${typeColor.border}`}>
                        {typeLabel}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 font-mono tracking-widest">{maskedNum}</p>
                    {acc.balance !== undefined && (
                      <p className="text-xs text-gray-400 mt-0.5">
                        Balance: <span className="font-bold text-gray-700">₦{Number(acc.balance).toLocaleString('en-NG', { minimumFractionDigits: 2 })}</span>
                      </p>
                    )}
                  </div>
                  <ChevronRight size={18} className="text-gray-400 shrink-0" />
                </button>
              );
            })}
          </div>
        ) : (
          <div className="space-y-3">
            <label className="block text-xs font-bold text-gray-700 mb-1">Account Number</label>
            <input
              type="text" maxLength={20}
              value={escAccount} onChange={e => setEscAccount(e.target.value)}
              placeholder="Enter your account number"
              className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm font-medium outline-none focus:border-[#A01030] transition-all"
            />
            <button
              onClick={() => escAccount.trim() && handleEscalateSubmit(escAccount.trim(), null)}
              disabled={!escAccount.trim()}
              className="w-full bg-[#A01030] text-white py-3.5 rounded-xl font-bold text-sm disabled:opacity-50"
            >
              Submit Complaint
            </button>
          </div>
        )}

        <button
          onClick={resetEscalation}
          className="w-full mt-3 text-gray-400 text-sm font-bold py-2 hover:text-gray-600"
        >
          Cancel
        </button>
      </div>
    );
  };

  // ── Sending spinner for escalation ────────────────────────────────────
  const renderEscSending = () => {
    if (escStep !== ESC_STEPS.SENDING) return null;
    return (
      <div className="flex flex-col items-center justify-center py-12 gap-4 mx-1 mt-2">
        <Loader2 size={36} className="text-[#A01030] animate-spin" />
        <p className="font-bold text-gray-700">Routing your complaint with AI...</p>
        <p className="text-xs text-gray-400 text-center max-w-xs">Our AI is analysing your complaint and routing it to the right department.</p>
      </div>
    );
  };

  // ── Error state for escalation ────────────────────────────────────────
  const renderEscError = () => {
    if (escStep !== ESC_STEPS.ERROR) return null;
    return (
      <div className="flex flex-col items-center py-8 gap-4 mx-1 mt-2">
        <div className="w-16 h-16 bg-red-50 rounded-full flex items-center justify-center">
          <AlertTriangle size={28} className="text-[#A01030]" />
        </div>
        <p className="font-bold text-gray-800">Escalation Failed</p>
        <p className="text-xs text-gray-500 text-center max-w-xs">{escError}</p>
        <button onClick={() => setEscStep(ESC_STEPS.ACCOUNT)}
          className="px-6 py-3 bg-[#A01030] text-white rounded-xl font-bold text-sm active:scale-95 transition-all"
        >
          Try Again
        </button>
      </div>
    );
  };

  // ── Main render ───────────────────────────────────────────────────────
  return (
    <div className="flex flex-col h-full bg-[#F9FAFB]">
      <Header />

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4" ref={scrollRef}>
        {messages.map(msg => renderMessage(msg))}

        {/* Escalation inline UI */}
        {renderAccountSelector()}
        {renderEscSending()}
        {renderEscError()}

        {faqLoading && (
          <div className="flex items-center gap-2 text-gray-400 text-xs">
            <Loader2 size={14} className="animate-spin" /> Searching FAQs...
          </div>
        )}
      </div>

      {/* Quick FAQ chips */}
      <div className="bg-white border-t border-gray-50 px-4 pt-3 pb-1">
        <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-2">Quick Actions</p>
        <div className="flex gap-2 overflow-x-auto hide-scrollbar pb-2">
          {[
            'ATM debit no cash',
            'Wrong transfer reversal',
            'Daily transfer limit',
            
          ].map((q, i) => (
            <button key={i}
              onClick={() => handleFaqSend(q)}
              className="whitespace-nowrap px-3 py-2 bg-gray-50 border border-gray-100 rounded-full text-xs font-bold text-gray-600 hover:bg-red-50 hover:text-[#A01030] hover:border-red-100 transition-colors shrink-0"
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      {/* Input */}
      <div className="bg-white pb-6 px-4 border-t border-gray-50 shrink-0 pt-2">
        <div className="flex items-center gap-2">
          <div className="flex-1 bg-gray-50 h-12 rounded-full px-5 flex items-center border border-transparent focus-within:border-[#A01030]/40 focus-within:ring-2 focus-within:ring-[#A01030]/10 transition-all">
            <input
              type="text" value={faqQuery}
              onChange={e => setFaqQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleFaqSend()}
              placeholder="Type your complaint..."
              className="flex-1 bg-transparent outline-none text-sm font-medium text-gray-900 placeholder:text-gray-400"
            />
          </div>
          <button
            onClick={() => handleFaqSend()}
            disabled={faqLoading || !faqQuery.trim()}
            className="w-12 h-12 bg-[#A01030] rounded-full flex items-center justify-center text-white shadow-lg active:scale-95 transition-transform disabled:opacity-70"
          >
            <Send size={18} className="ml-0.5" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatScreen;