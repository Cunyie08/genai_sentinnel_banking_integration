import React, { useState, useRef, useEffect, useCallback, memo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import {
  ChevronLeft, Send, Bot, ChevronRight,
  AlertTriangle, CheckCircle,
  HelpCircle, MessageSquareWarning, Loader2
} from 'lucide-react';
import { api } from '../api/axiosConfig';

const ESC_STEPS = { IDLE: 0, ACCOUNT: 1, SENDING: 2, DONE: 3, ERROR: 4 };

const UserMessage = memo(({ msg }) => (
  <div className="flex flex-col items-end">
    <div className="max-w-[85%] bg-[#A01030] text-white p-4 rounded-[20px] rounded-tr-none shadow-md text-[14px] leading-relaxed font-medium">
      {msg.text}
    </div>
    <span className="text-[10px] text-gray-400 mt-1 mr-1">{msg.time} • Read</span>
  </div>
));

const AiTextMessage = memo(({ msg }) => (
  <div className="flex flex-col">
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
));

const RoutingResultMessage = memo(({ msg }) => (
  <div className="flex flex-col">
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
));

const ChatScreen = () => {
  const navigate   = useNavigate();
  const user       = useSelector(s => s.auth.user);
  const accounts   = user?.accounts || [];

  const [messages,      setMessages]     = useState([]);
  const [faqQuery,      setFaqQuery]     = useState('');
  const [faqLoading,    setFaqLoading]   = useState(false);
  const [escStep,       setEscStep]      = useState(ESC_STEPS.IDLE);
  const [escQuery,      setEscQuery]     = useState('');
  const [escAccount,    setEscAccount]   = useState('');
  const [escAccountObj, setEscAccountObj]= useState(null);
  const [escResult,     setEscResult]    = useState(null);
  const [escError,      setEscError]     = useState('');

  const scrollRef = useRef(null);

  useEffect(() => {
    const firstName = user?.name?.split(' ')[0] || 'there';
    setMessages([{
      id: 1, sender: 'ai', type: 'text',
      text: `Hello ${firstName}! How can I help you with your account today? You can ask about:`,
      options: ['Transaction Discrepancy', 'Card Issues & Limits', 'Report Fraudulent Activity'],
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }]);
  }, [user?.name]);

  useEffect(() => {
    if (scrollRef.current)
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, faqLoading, escStep]);

  const addMsg = (msg) => setMessages(prev => [...prev, msg]);
  const now = () => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  // ── FAQ send ───────────────────────────────────────────────────────────
  const handleFaqSend = useCallback(async (overrideQuery) => {
    const q = (overrideQuery || faqQuery).trim();
    if (!q) return;
    setFaqQuery('');
    setEscStep(ESC_STEPS.IDLE);
    setEscQuery('');
    setEscResult(null);

    addMsg({ id: Date.now(), sender: 'user', type: 'text', text: q, time: now() });
    setFaqLoading(true);
    try {
      const res = await api.getFaqs(q);
      const d = res?.data || {};
      const matchFound = d.success === true;
      const answer = matchFound
        ? (d.match?.answer || 'See our FAQ for more details.')
        : (d.message || "I couldn't find a specific answer to your question in our FAQs.");

      if (!matchFound) {
        addMsg({ id: Date.now(), sender: 'ai', type: 'escalation', text: answer, time: now() });
        setEscQuery(q);
      } else {
        addMsg({ id: Date.now(), sender: 'ai', type: 'text', text: answer, time: now() });
      }
    } catch (err) {
      addMsg({
        id: Date.now(), sender: 'ai', type: 'text',
        text: 'Could not retrieve FAQ at this time. Please try again.',
        time: now(),
      });
    } finally {
      setFaqLoading(false);
    }
  }, [faqQuery]); // ✅ fixed: was missing useCallback wrapper, wrong dep (escQuery → faqQuery)

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
      addMsg({ id: Date.now(), sender: 'ai', type: 'routing-result', result: res.data, time: now() });
    } catch (err) {
      setEscError(err?.detail || 'Failed to submit complaint. Please try again.');
      setEscStep(ESC_STEPS.ERROR);
    }
  };

  const resetEscalation = () => {
    setEscStep(ESC_STEPS.IDLE);
    setEscAccount(''); setEscAccountObj(null); setEscResult(null); setEscError('');
  };

  // ... (Header, renderAccountSelector, renderEscSending, renderEscError unchanged)

  const renderMessage = (msg) => {
    // User bubble — memoized, skips re-render if msg unchanged
    if (msg.sender === 'user') {
      return <UserMessage key={msg.id} msg={msg} />;
    }

    if (msg.options) {
      return (
        <div key={msg.id} className="flex flex-col">
          <div className="flex items-center gap-2 mb-1">
            <div className="w-5 h-5 vault-gradient text-white rounded-full flex items-center justify-center">
              <Bot size={12} />
            </div>
            <span className="text-xs font-bold text-gray-400 dark:text-slate-500">AI Assistant</span>
          </div>
          <div className="bg-white dark:bg-vault-dark-card p-4 rounded-[20px] rounded-tl-none shadow-sm border border-gray-100 dark:border-white/5 max-w-[90%]">
            <p className="text-[14px] font-medium text-gray-800 dark:text-white leading-relaxed mb-3">{msg.text}</p>
            <div className="space-y-2">
              {msg.options.map((opt, i) => (
                <button key={i} onClick={() => handleFaqSend(opt)}
                  className="w-full flex items-center justify-between p-3 bg-gray-50 dark:bg-white/5 rounded-xl hover:bg-cyan-50 dark:hover:bg-vault-cyan/10 hover:text-vault-cyan text-sm font-semibold text-gray-700 dark:text-slate-300 transition-all group border border-gray-100 dark:border-white/5"
                >
                  {opt}
                  <ChevronRight size={16} className="text-gray-400 dark:text-slate-500 group-hover:text-vault-cyan" />
                </button>
              ))}
            </div>
          </div>
          <span className="text-[10px] text-gray-400 dark:text-slate-500 mt-1">{msg.time}</span>
        </div>
      );
    }

    if (msg.type === 'escalation') {
      return (
        <div key={msg.id} className="flex flex-col">
          <div className="flex items-center gap-2 mb-1">
            <div className="w-5 h-5 vault-gradient text-white rounded-full flex items-center justify-center">
              <Bot size={12} />
            </div>
            <span className="text-xs font-bold text-gray-400 dark:text-slate-500">AI Assistant</span>
          </div>
          <div className="bg-white dark:bg-vault-dark-card p-4 rounded-[20px] rounded-tl-none shadow-sm border border-gray-100 dark:border-white/5 max-w-[90%]">
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle size={16} className="text-amber-500" />
              <span className="text-[11px] font-black text-amber-500 uppercase tracking-wide">Action Required</span>
            </div>
            <p className="text-[14px] font-medium text-gray-800 dark:text-white leading-relaxed mb-4">{msg.text}</p>
            {escStep === ESC_STEPS.IDLE && (
              <div>
                <p className="text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-2">Route to:</p>
                <div className="flex gap-3">
                  <button onClick={() => setEscStep(ESC_STEPS.ACCOUNT)}
                    className="flex-1 vault-gradient text-white py-3 rounded-xl font-bold text-sm shadow-lg vault-glow active:scale-95 transition-all"
                  >
                    Escalate Now
                  </button>
                  <button onClick={resetEscalation}
                    className="flex-1 bg-white dark:bg-white/5 text-gray-600 dark:text-slate-300 py-3 rounded-xl font-bold text-sm border border-gray-200 dark:border-white/5 active:scale-95 transition-all"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
          <span className="text-[10px] text-gray-400 dark:text-slate-500 mt-1">{msg.time}</span>
        </div>
      );
    }

    // Routing result — memoized
    if (msg.type === 'routing-result' && msg.result) {
      return <RoutingResultMessage key={msg.id} msg={msg} />;
    }

    // Normal AI text bubble — memoized
    return <AiTextMessage key={msg.id} msg={msg} />;
  };

  // ... rest of the component unchanged
};

export default ChatScreen;