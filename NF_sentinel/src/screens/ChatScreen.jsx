import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import {
  ChevronLeft, Send, Bot, ChevronRight,
  AlertTriangle, CheckCircle,
  HelpCircle, MessageSquareWarning, Loader2
} from 'lucide-react';
import { api } from '../api/axiosConfig';

const ESC_STEPS = { IDLE: 0, ACCOUNT: 1, SENDING: 2, DONE: 3, ERROR: 4 };

const ChatScreen = () => {
  const navigate = useNavigate();
  const user = useSelector(s => s.auth.user);
  const accounts = user?.accounts || [];

  const [messages, setMessages] = useState([]);
  const [faqQuery, setFaqQuery] = useState('');
  const [faqLoading, setFaqLoading] = useState(false);

  const [escStep, setEscStep] = useState(ESC_STEPS.IDLE);
  const [escQuery, setEscQuery] = useState('');   // the original query that had no FAQ match
  const [escAccount, setEscAccount] = useState('');
  const [escAccountObj, setEscAccountObj] = useState(null);
  const [escResult, setEscResult] = useState(null);
  const [escError, setEscError] = useState('');

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

  const handleFaqSend = async (overrideQuery) => {
    const q = (overrideQuery || faqQuery).trim();
    if (!q) return;
    setFaqQuery('');
    setEscStep(ESC_STEPS.IDLE);
    setEscQuery('');
    setEscResult(null);

    addMsg({ id: Date.now(), sender: 'user', type: 'text', text: q, time: now() });
    setFaqLoading(true);
    try {
      console.log('[FAQ] Sending query to backend:', q);
      const res = await api.getFaqs(q);
      console.log('[FAQ] Raw response from backend:', res?.data);

      const d = res?.data || {};
      const matchFound = d.success === true;
      const answer = matchFound
        ? (d.match?.answer || 'See our FAQ for more details.')
        : (d.message || "I couldn't find a specific answer to your question in our FAQs.");

      console.log('[FAQ] Match found:', matchFound, '| Answer preview:', answer?.substring(0, 80));

      if (!matchFound) {
        addMsg({
          id: Date.now(), sender: 'ai', type: 'escalation',
          text: answer,
          time: now(),
        });
        setEscQuery(q);
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

  const handleEscalateSubmit = async (accountNumber, accountObj) => {
    setEscAccount(accountNumber);
    setEscAccountObj(accountObj);
    setEscStep(ESC_STEPS.SENDING);
    try {
      const res = await api.makeComplaint({
        account_number: accountNumber,
        complaint_channel: 'App',
        complaint_text: escQuery,
      });
      setEscResult(res.data);
      setEscStep(ESC_STEPS.DONE);
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

  const Header = () => (
    <div className="bg-white dark:bg-vault-dark-card px-4 py-4 flex items-center justify-between border-b border-gray-100 dark:border-white/5 shadow-sm shrink-0 z-20 vault-transition">
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate('/home')}
          className="text-gray-600 dark:text-slate-400 hover:bg-gray-50 dark:hover:bg-white/5 p-1 rounded-full"
        >
          <ChevronLeft size={26} />
        </button>
        <div>
          <h2 className="font-extrabold text-gray-900 dark:text-white text-lg leading-tight">AI Support Assistant</h2>
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <p className="text-[10px] text-gray-500 dark:text-slate-500 uppercase font-bold tracking-wide">Always Active</p>
          </div>
        </div>
      </div>
      <div className="w-10 h-10 rounded-full vault-gradient flex items-center justify-center">
        <Bot size={20} className="text-white" />
      </div>
    </div>
  );

  const renderMessage = (msg) => {
    if (msg.sender === 'user') {
      return (
        <div key={msg.id} className="flex flex-col items-end">
          <div className="max-w-[85%] vault-gradient text-white p-4 rounded-[20px] rounded-tr-none shadow-md text-[14px] leading-relaxed font-medium">
            {msg.text}
          </div>
          <span className="text-[10px] text-gray-400 dark:text-slate-500 mt-1 mr-1">{msg.time} • Read</span>
        </div>
      );
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
                <button
                  key={i}
                  onClick={() => handleFaqSend(opt)}
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
                  <button
                    onClick={() => setEscStep(ESC_STEPS.ACCOUNT)}
                    className="flex-1 vault-gradient text-white py-3 rounded-xl font-bold text-sm shadow-lg vault-glow active:scale-95 transition-all"
                  >
                    Escalate Now
                  </button>
                  <button
                    onClick={resetEscalation}
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

    if (msg.type === 'routing-result' && msg.result) {
      const r = msg.result;
      return (
        <div key={msg.id} className="flex flex-col">
          <div className="flex items-center gap-2 mb-1">
            <div className="w-5 h-5 bg-green-50 dark:bg-green-500/20 text-green-600 dark:text-green-400 rounded-full flex items-center justify-center">
              <CheckCircle size={12} />
            </div>
            <span className="text-xs font-bold text-gray-400 dark:text-slate-500">AI Assistant</span>
          </div>
          <div className="bg-white dark:bg-vault-dark-card rounded-[20px] rounded-tl-none shadow-sm border border-gray-100 dark:border-white/5 max-w-[90%] overflow-hidden">
            <div className="bg-green-50 dark:bg-green-500/20 px-4 py-3 flex items-center gap-2">
              <CheckCircle size={16} className="text-green-500 dark:text-green-400" />
              <span className="text-sm font-black text-green-700 dark:text-green-400">Complaint Routed Successfully</span>
            </div>
          </div>
          <span className="text-[10px] text-gray-400 dark:text-slate-500 mt-1">{msg.time}</span>
        </div>
      );
    }

    return (
      <div key={msg.id} className="flex flex-col">
        <div className="flex items-center gap-2 mb-1">
          <div className="w-5 h-5 vault-gradient text-white rounded-full flex items-center justify-center">
            <Bot size={12} />
          </div>
          <span className="text-xs font-bold text-gray-400 dark:text-slate-500">AI Assistant</span>
        </div>
        <div className="bg-white dark:bg-vault-dark-card p-4 rounded-[20px] rounded-tl-none shadow-sm border border-gray-100 dark:border-white/5 max-w-[90%] text-[14px] font-medium text-gray-800 dark:text-white leading-relaxed">
          {msg.text}
        </div>
        <span className="text-[10px] text-gray-400 dark:text-slate-500 mt-1">{msg.time}</span>
      </div>
    );
  };

  const renderAccountSelector = () => {
    if (escStep !== ESC_STEPS.ACCOUNT) return null;

    return (
      <div className="bg-white dark:bg-vault-dark-card rounded-2xl p-5 shadow-sm border border-gray-100 dark:border-white/5 mx-1 mt-2">
        <p className="text-xs font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-1">Select Account</p>
        <p className="text-base font-black text-gray-900 dark:text-white mb-1">Which account is this related to?</p>
        <p className="text-xs text-gray-500 dark:text-slate-400 mb-4">Your complaint will be routed by our AI to the right department.</p>

        {accounts.length > 0 ? (
          <div className="space-y-3">
            {accounts.map(acc => {
              const typeLabel = acc.account_type || 'Account';
              const typeColor =
                typeLabel.toLowerCase() === 'savings' ? { bg: 'bg-blue-50 dark:bg-blue-500/10', text: 'text-blue-700 dark:text-blue-400', border: 'border-blue-200 dark:border-blue-500/20' } :
                  typeLabel.toLowerCase() === 'current' ? { bg: 'bg-green-50 dark:bg-green-500/10', text: 'text-green-700 dark:text-green-400', border: 'border-green-200 dark:border-green-500/20' } :
                    typeLabel.toLowerCase() === 'solo' ? { bg: 'bg-purple-50 dark:bg-purple-500/10', text: 'text-purple-700 dark:text-purple-400', border: 'border-purple-200 dark:border-purple-500/20' } :
                      { bg: 'bg-gray-50 dark:bg-white/5', text: 'text-gray-700 dark:text-slate-300', border: 'border-gray-200 dark:border-white/10' };
              const num = acc.account_number?.toString() || '';
              const maskedNum = num.length >= 6
                ? num.slice(0, 4) + '••••' + num.slice(-4)
                : num;

              return (
                <button
                  key={acc.account_number}
                  onClick={() => handleEscalateSubmit(acc.account_number, acc)}
                  className="w-full flex items-center gap-4 p-4 rounded-2xl border-2 border-gray-100 dark:border-white/5 bg-white dark:bg-vault-dark-card hover:border-vault-cyan hover:shadow-sm text-left transition-all active:scale-[0.98]"
                >
                  <div className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 font-black text-lg ${typeColor.bg} ${typeColor.text}`}>
                    {typeLabel.charAt(0).toUpperCase()}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <p className="font-black text-gray-900 dark:text-white text-sm">{typeLabel} Account</p>
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide border ${typeColor.bg} ${typeColor.text} ${typeColor.border}`}>
                        {typeLabel}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 dark:text-slate-400 font-mono tracking-widest">{maskedNum}</p>
                    {acc.balance !== undefined && (
                      <p className="text-xs text-gray-400 dark:text-slate-500 mt-0.5">
                        Balance: <span className="font-bold text-gray-700 dark:text-white">₦{Number(acc.balance).toLocaleString('en-NG', { minimumFractionDigits: 2 })}</span>
                      </p>
                    )}
                  </div>
                  <ChevronRight size={18} className="text-gray-400 dark:text-slate-500 shrink-0" />
                </button>
              );
            })}
          </div>
        ) : (
          <div className="space-y-3">
            <label className="block text-xs font-bold text-gray-700 dark:text-slate-300 mb-1">Account Number</label>
            <input
              type="text" maxLength={20}
              value={escAccount} onChange={e => setEscAccount(e.target.value)}
              placeholder="Enter your account number"
              className="w-full px-4 py-3 bg-gray-50 dark:bg-vault-dark-input border border-gray-200 dark:border-white/5 rounded-xl text-sm font-medium outline-none focus:border-vault-cyan focus:ring-2 focus:ring-vault-cyan/20 transition-all text-gray-900 dark:text-white"
            />
            <button
              onClick={() => escAccount.trim() && handleEscalateSubmit(escAccount.trim(), null)}
              disabled={!escAccount.trim()}
              className="w-full vault-gradient text-white py-3.5 rounded-xl font-bold text-sm disabled:opacity-50 vault-glow"
            >
              Submit Complaint
            </button>
          </div>
        )}

        <button
          onClick={resetEscalation}
          className="w-full mt-3 text-gray-400 dark:text-slate-500 text-sm font-bold py-2 hover:text-gray-600 dark:hover:text-slate-300"
        >
          Cancel
        </button>
      </div>
    );
  };

  const renderEscSending = () => {
    if (escStep !== ESC_STEPS.SENDING) return null;
    return (
      <div className="flex flex-col items-center justify-center py-12 gap-4 mx-1 mt-2">
        <Loader2 size={36} className="text-vault-cyan animate-spin" />
        <p className="font-bold text-gray-700 dark:text-white">Routing your complaint with Sentinnel...</p>
        <p className="text-xs text-gray-400 dark:text-slate-500 text-center max-w-xs">Our AI is analysing your complaint and routing it to the right department.</p>
      </div>
    );
  };

  const renderEscError = () => {
    if (escStep !== ESC_STEPS.ERROR) return null;
    return (
      <div className="flex flex-col items-center py-8 gap-4 mx-1 mt-2">
        <div className="w-16 h-16 bg-red-50 dark:bg-red-500/20 rounded-full flex items-center justify-center">
          <AlertTriangle size={28} className="text-red-500 dark:text-red-400" />
        </div>
        <p className="font-bold text-gray-800 dark:text-white">Escalation Failed</p>
        <p className="text-xs text-gray-500 dark:text-slate-400 text-center max-w-xs">{escError}</p>
        <button onClick={() => setEscStep(ESC_STEPS.ACCOUNT)}
          className="px-6 py-3 vault-gradient text-white rounded-xl font-bold text-sm active:scale-95 transition-all vault-glow"
        >
          Try Again
        </button>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full bg-vault-light-bg dark:bg-vault-dark-bg vault-transition">
      <Header />

      <div className="flex-1 overflow-y-auto p-4 space-y-4" ref={scrollRef}>
        {messages.map(msg => renderMessage(msg))}

        {renderAccountSelector()}
        {renderEscSending()}
        {renderEscError()}

        {faqLoading && (
          <div className="flex items-center gap-2 text-gray-400 dark:text-slate-500 text-xs">
            <Loader2 size={14} className="animate-spin" /> Searching FAQs...
          </div>
        )}
      </div>

      <div className="bg-white dark:bg-vault-dark-card border-t border-gray-50 dark:border-white/5 px-4 pt-3 pb-1 vault-transition">
        <p className="text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-2">Quick Actions</p>
        <div className="flex gap-2 overflow-x-auto hide-scrollbar pb-2">
          {[
            'ATM debit no cash',
            'Wrong transfer reversal',
            'Daily transfer limit',
          ].map((q, i) => (
            <button key={i}
              onClick={() => handleFaqSend(q)}
              className="whitespace-nowrap px-3 py-2 bg-gray-50 dark:bg-white/5 border border-gray-100 dark:border-white/5 rounded-full text-xs font-bold text-gray-600 dark:text-slate-300 hover:bg-cyan-50 dark:hover:bg-vault-cyan/10 hover:text-vault-cyan hover:border-cyan-200 dark:hover:border-vault-cyan/30 transition-colors shrink-0"
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      <div className="bg-white dark:bg-vault-dark-card pb-6 px-4 border-t border-gray-50 dark:border-white/5 shrink-0 pt-2 vault-transition">
        <div className="flex items-center gap-2">
          <div className="flex-1 bg-gray-50 dark:bg-vault-dark-input h-12 rounded-full px-5 flex items-center border border-transparent focus-within:border-vault-cyan/40 focus-within:ring-2 focus-within:ring-vault-cyan/10 transition-all">
            <input
              type="text" value={faqQuery}
              onChange={e => setFaqQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleFaqSend()}
              placeholder="Type your complaint..."
              className="flex-1 bg-transparent outline-none text-sm font-medium text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-slate-500"
            />
          </div>
          <button
            onClick={() => handleFaqSend()}
            disabled={faqLoading || !faqQuery.trim()}
            className="w-12 h-12 vault-gradient rounded-full flex items-center justify-center text-white shadow-lg vault-glow active:scale-95 transition-transform disabled:opacity-70"
          >
            <Send size={18} className="ml-0.5" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatScreen;