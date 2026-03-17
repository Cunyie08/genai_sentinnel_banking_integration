import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import {
  ChevronLeft, Mic, Send, Bot, ChevronRight,
  AlertTriangle, CheckCircle, Paperclip,
  HelpCircle, MessageSquareWarning, X, Loader2
} from 'lucide-react';
import { addChatMessage, sendMessage, createTicket, initChatGreeting, submitComplaint } from '../features/aiSlice';
import { api } from '../api/axiosConfig';

// ─── Chat modes ───────────────────────────────────────────────────────────────
const MODES = {
  SELECT:    'select',    // initial — pick a mode
  FAQ:       'faq',       // FAQ / question mode
  COMPLAINT: 'complaint', // Complaint form + AI routing
};

// ─── Complaint multi-step form state ─────────────────────────────────────────
const COMPLAINT_STEPS = { ACCOUNT: 0, TEXT: 1, SENDING: 2, DONE: 3, ERROR: 4 };

const ChatScreen = () => {
  const navigate   = useNavigate();
  const dispatch   = useDispatch();
  const { chatHistory, isLoading } = useSelector(s => s.ai);
  const user       = useSelector(s => s.auth.user);
  const accounts   = user?.accounts || [];

  // ── UI state ──────────────────────────────────────────────────────────────
  const [mode,        setMode]        = useState(MODES.SELECT);
  const [input,       setInput]       = useState('');

  // FAQ state
  const [faqLoading,  setFaqLoading]  = useState(false);
  const [faqQuery,    setFaqQuery]    = useState('');

  // Complaint state
  const [cStep,       setCStep]       = useState(COMPLAINT_STEPS.ACCOUNT);
  const [cAccount,    setCAccount]    = useState('');
  const [cAccountObj, setCAccountObj] = useState(null); // full account object
  const [cText,       setCText]       = useState('');
  const [cResult,     setCResult]     = useState(null);
  const [cError,      setCError]      = useState('');

  const scrollRef = useRef(null);

  // Greet with real name on mount
  useEffect(() => {
    const firstName = user?.name?.split(' ')[0] || 'there';
    dispatch(initChatGreeting(firstName));
  }, [dispatch, user?.name]);

  // Auto-scroll
  useEffect(() => {
    if (scrollRef.current)
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [chatHistory, isLoading, mode]);

  // ── FAQ helpers ───────────────────────────────────────────────────────────
  const handleFaqSend = async () => {
    if (!faqQuery.trim()) return;
    const q = faqQuery.trim();
    setFaqQuery('');
    // Add user bubble
    dispatch(addChatMessage({
      id: Date.now(), sender: 'user', type: 'text', text: q,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }));
    setFaqLoading(true);
    try {
      // GET /faqs?prompt=... returns { answer, question_matched, match_found }
      const res = await api.getFaqs(q);
      const answer = res?.data?.answer ||
        "I couldn't find a specific answer. Please contact our 24/7 customer care team at 0700-SENTINEL.";

      dispatch(addChatMessage({
        id: Date.now(), sender: 'ai', type: 'text', text: answer,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }));
    } catch {
      dispatch(addChatMessage({
        id: Date.now(), sender: 'ai', type: 'text',
        text: 'Could not retrieve FAQ at this time. Please try again.',
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }));
    } finally {
      setFaqLoading(false);
    }
  };

  // ── Complaint submit ──────────────────────────────────────────────────────
  const handleComplaintSubmit = async () => {
    if (!cText.trim() || !cAccount) return;
    setCStep(COMPLAINT_STEPS.SENDING);
    try {
      const res = await api.makeComplaint({
        account_number:    cAccount,
        complaint_channel: 'App',
        complaint_text:    cText,
      });
      setCResult(res.data);
      setCStep(COMPLAINT_STEPS.DONE);
    } catch (err) {
      setCError(err?.detail || 'Failed to submit complaint. Please try again.');
      setCStep(COMPLAINT_STEPS.ERROR);
    }
  };

  const resetComplaint = () => {
    setCStep(COMPLAINT_STEPS.ACCOUNT);
    setCAccount(''); setCAccountObj(null); setCText(''); setCResult(null); setCError('');
  };

  // ── AI Chat helpers ───────────────────────────────────────────────────────
  const handleSend = () => {
    if (!input.trim()) return;
    dispatch(addChatMessage({
      id: Date.now(), sender: 'user', type: 'text', text: input,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }));
    dispatch(sendMessage(input));
    setInput('');
  };

  const handleEscalate = () => {
    const newTicket = { id: `TKT-${Math.floor(Math.random()*10000)}`, user: 'User', issue: 'Billing', time: new Date().toLocaleTimeString() };
    dispatch(createTicket(newTicket));
    dispatch(addChatMessage({
      id: Date.now(), sender: 'ai', type: 'success',
      text: `Ticket #${newTicket.id} created. Refund initiated.`,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }));
  };

  // ── Shared header ─────────────────────────────────────────────────────────
  const Header = () => (
    <div className="bg-white px-4 py-4 flex items-center justify-between border-b border-gray-100 shadow-sm shrink-0 z-20">
      <div className="flex items-center gap-3">
        <button
          onClick={() => mode === MODES.SELECT ? navigate('/home') : setMode(MODES.SELECT)}
          className="text-gray-600 hover:bg-gray-50 p-1 rounded-full"
        >
          <ChevronLeft size={26} />
        </button>
        <div>
          <h2 className="font-extrabold text-gray-900 text-lg leading-tight">AI Support</h2>
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <p className="text-[10px] text-gray-500 uppercase font-bold tracking-wide">
              {mode === MODES.FAQ ? 'FAQ Mode' : mode === MODES.COMPLAINT ? 'Complaint Mode' : 'Always Active'}
            </p>
          </div>
        </div>
      </div>
      <div className="w-10 h-10 rounded-full bg-red-50 border border-gray-100 flex items-center justify-center">
        <Bot size={20} className="text-[#A01030]" />
      </div>
    </div>
  );

  // ── Mode SELECT screen ────────────────────────────────────────────────────
  if (mode === MODES.SELECT) {
    return (
      <div className="flex flex-col h-full bg-[#F9FAFB]">
        <Header />
        <div className="flex-1 flex flex-col items-center justify-center p-6 gap-6">
          <div className="text-center mb-2">
            <div className="w-16 h-16 bg-red-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Bot size={32} className="text-[#A01030]" />
            </div>
            <h3 className="text-xl font-black text-gray-900 mb-1">How can we help?</h3>
            <p className="text-sm text-gray-500">Choose the type of support you need</p>
          </div>

          {/* Question / FAQ button */}
          <button
            onClick={() => setMode(MODES.FAQ)}
            className="w-full max-w-sm bg-white border-2 border-gray-100 rounded-2xl p-5 flex items-center gap-4 shadow-sm hover:border-[#A01030] hover:shadow-md active:scale-95 transition-all group"
          >
            <div className="w-12 h-12 bg-blue-50 rounded-xl flex items-center justify-center group-hover:bg-blue-100 transition-colors shrink-0">
              <HelpCircle size={24} className="text-blue-600" />
            </div>
            <div className="text-left">
              <p className="font-bold text-gray-900 text-base">Ask a Question</p>
              <p className="text-xs text-gray-500 mt-0.5">Browse FAQs &amp; get instant answers from our knowledge base</p>
            </div>
            <ChevronRight size={18} className="text-gray-400 ml-auto group-hover:text-[#A01030] transition-colors" />
          </button>

          {/* Complaint button */}
          <button
            onClick={() => setMode(MODES.COMPLAINT)}
            className="w-full max-w-sm bg-white border-2 border-gray-100 rounded-2xl p-5 flex items-center gap-4 shadow-sm hover:border-[#A01030] hover:shadow-md active:scale-95 transition-all group"
          >
            <div className="w-12 h-12 bg-red-50 rounded-xl flex items-center justify-center group-hover:bg-red-100 transition-colors shrink-0">
              <MessageSquareWarning size={24} className="text-[#A01030]" />
            </div>
            <div className="text-left">
              <p className="font-bold text-gray-900 text-base">File a Complaint</p>
              <p className="text-xs text-gray-500 mt-0.5">Report issues — our AI routes it to the right department instantly</p>
            </div>
            <ChevronRight size={18} className="text-gray-400 ml-auto group-hover:text-[#A01030] transition-colors" />
          </button>
        </div>
      </div>
    );
  }

  // ── FAQ MODE ──────────────────────────────────────────────────────────────
  if (mode === MODES.FAQ) {
    return (
      <div className="flex flex-col h-full bg-[#F9FAFB]">
        <Header />

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4" ref={scrollRef}>
          {chatHistory.map(msg => (
            <div key={msg.id} className="flex flex-col">
              {msg.sender === 'ai' && (
                <div className="flex items-center gap-2 mb-1">
                  <div className="w-5 h-5 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center">
                    <span className="text-[9px] font-bold">AI</span>
                  </div>
                  <span className="text-xs font-bold text-gray-400">FAQ Assistant</span>
                </div>
              )}
              {msg.sender === 'user' && (
                <div className="self-end max-w-[85%] bg-blue-600 text-white p-4 rounded-[20px] rounded-tr-none shadow-md text-[14px] leading-relaxed font-medium">
                  {msg.text}
                </div>
              )}
              {msg.sender === 'ai' && (
                <div className="bg-white p-4 rounded-[20px] rounded-tl-none shadow-sm border border-gray-100 max-w-[90%] text-[14px] font-medium text-gray-800 leading-relaxed">
                  {msg.text}
                </div>
              )}
            </div>
          ))}
          {faqLoading && (
            <div className="flex items-center gap-2 text-gray-400 text-xs">
              <Loader2 size={14} className="animate-spin" /> Searching FAQs...
            </div>
          )}
        </div>

        {/* Quick FAQ chips */}
        <div className="bg-white border-t border-gray-50 px-4 pt-3 pb-1">
          <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-2">Common Questions</p>
          <div className="flex gap-2 overflow-x-auto hide-scrollbar pb-2">
            {[
              'How do I reset my PIN?',
              'What are transfer limits?',
              'How to block my card?',
              'Dispute a transaction',
            ].map((q, i) => (
              <button key={i}
                onClick={() => { setFaqQuery(q); }}
                className="whitespace-nowrap px-3 py-2 bg-blue-50 border border-blue-100 rounded-full text-xs font-bold text-blue-700 hover:bg-blue-100 transition-colors shrink-0">
                {q}
              </button>
            ))}
          </div>
        </div>

        {/* Input */}
        <div className="bg-white pb-6 px-4 border-t border-gray-50 shrink-0 pt-2">
          <div className="flex items-center gap-2">
            <div className="flex-1 bg-gray-50 h-12 rounded-full px-5 flex items-center border border-transparent focus-within:border-blue-400/40 focus-within:ring-2 focus-within:ring-blue-400/10 transition-all">
              <input
                type="text" value={faqQuery}
                onChange={e => setFaqQuery(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleFaqSend()}
                placeholder="Ask anything about your account..."
                className="flex-1 bg-transparent outline-none text-sm font-medium text-gray-900 placeholder:text-gray-400"
              />
            </div>
            <button
              onClick={handleFaqSend}
              disabled={faqLoading || !faqQuery.trim()}
              className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center text-white shadow-lg active:scale-95 transition-transform disabled:opacity-70"
            >
              <Send size={18} className="ml-0.5" />
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── COMPLAINT MODE ────────────────────────────────────────────────────────
  if (mode === MODES.COMPLAINT) {
    return (
      <div className="flex flex-col h-full bg-[#F9FAFB]">
        <Header />
        <div className="flex-1 overflow-y-auto p-5 space-y-5">

          {/* Step 0: Select account */}
          {cStep === COMPLAINT_STEPS.ACCOUNT && (
            <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
              <p className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-1">Step 1 of 2</p>
              <p className="text-base font-black text-gray-900 mb-1">Select Account</p>
              <p className="text-xs text-gray-500 mb-5">Which account is this complaint related to?</p>

              {accounts.length > 0 ? (
                <div className="space-y-3">
                  {accounts.map(acc => {
                    const typeLabel = acc.account_type || 'Account';
                    const typeColor =
                      typeLabel.toLowerCase() === 'savings'  ? { bg: 'bg-blue-50',   text: 'text-blue-700',   border: 'border-blue-200'   } :
                      typeLabel.toLowerCase() === 'current'  ? { bg: 'bg-green-50',  text: 'text-green-700',  border: 'border-green-200'  } :
                      typeLabel.toLowerCase() === 'solo'     ? { bg: 'bg-purple-50', text: 'text-purple-700', border: 'border-purple-200' } :
                                                               { bg: 'bg-gray-50',   text: 'text-gray-700',   border: 'border-gray-200'   };
                    const isSelected = cAccount === acc.account_number;
                    // Format account number: mask middle digits e.g. 1234••••5678
                    const num = acc.account_number?.toString() || '';
                    const maskedNum = num.length >= 6
                      ? num.slice(0, 4) + '••••' + num.slice(-4)
                      : num;

                    return (
                      <button
                        key={acc.account_number}
                        onClick={() => { setCAccount(acc.account_number); setCAccountObj(acc); setCStep(COMPLAINT_STEPS.TEXT); }}
                        className={`w-full flex items-center gap-4 p-4 rounded-2xl border-2 text-left transition-all active:scale-[0.98] ${
                          isSelected ? 'border-[#A01030] bg-red-50 shadow-sm' : 'border-gray-100 bg-white hover:border-gray-300 hover:shadow-sm'
                        }`}
                      >
                        {/* Account type icon/initial */}
                        <div className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 font-black text-lg ${typeColor.bg} ${typeColor.text}`}>
                          {typeLabel.charAt(0).toUpperCase()}
                        </div>

                        {/* Account details */}
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

                        {/* Select indicator */}
                        <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center shrink-0 transition-all ${
                          isSelected ? 'border-[#A01030] bg-[#A01030]' : 'border-gray-300'
                        }`}>
                          {isSelected && <div className="w-2 h-2 bg-white rounded-full" />}
                        </div>
                      </button>
                    );
                  })}
                  {cAccount && (
                    <button
                      onClick={() => setCStep(COMPLAINT_STEPS.TEXT)}
                      className="w-full mt-2 bg-[#A01030] text-white py-3.5 rounded-xl font-bold text-sm shadow-md shadow-red-900/20 active:scale-95 transition-all"
                    >
                      Continue →
                    </button>
                  )}
                </div>
              ) : (
                <div className="space-y-3">
                  <label className="block text-xs font-bold text-gray-700 mb-1">Account Number</label>
                  <input
                    type="text" maxLength={20}
                    value={cAccount} onChange={e => setCAccount(e.target.value)}
                    placeholder="Enter your account number"
                    className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm font-medium outline-none focus:border-[#A01030] transition-all"
                  />
                  <button
                    onClick={() => cAccount.trim() && setCStep(COMPLAINT_STEPS.TEXT)}
                    disabled={!cAccount.trim()}
                    className="w-full bg-[#A01030] text-white py-3.5 rounded-xl font-bold text-sm disabled:opacity-50"
                  >
                    Continue
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Step 1: Write complaint */}
          {cStep === COMPLAINT_STEPS.TEXT && (
            <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
              <div className="flex items-center justify-between mb-4">
                <p className="text-xs font-bold text-gray-400 uppercase tracking-widest">Step 2 of 2 — Describe Issue</p>
                <button onClick={() => setCStep(COMPLAINT_STEPS.ACCOUNT)} className="text-xs text-gray-400 hover:text-gray-600 font-bold">← Change Account</button>
              </div>
              <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl mb-4 border border-gray-100">
                <div className="w-8 h-8 rounded-lg bg-[#A01030]/10 flex items-center justify-center shrink-0">
                  <span className="text-xs font-black text-[#A01030]">{(cAccountObj?.account_type || 'A').charAt(0).toUpperCase()}</span>
                </div>
                <div>
                  <p className="text-xs font-black text-gray-900">{cAccountObj?.account_type || 'Account'} Account</p>
                  <p className="text-[11px] text-gray-500 font-mono">
                    {(() => { const n = cAccount?.toString() || ''; return n.length >= 6 ? n.slice(0,4)+'••••'+n.slice(-4) : n; })()}
                  </p>
                </div>
              </div>
              <label className="block text-xs font-bold text-gray-700 mb-2">Describe your complaint</label>
              <textarea
                rows={5} value={cText} onChange={e => setCText(e.target.value)}
                placeholder="e.g. I was double-charged ₦15,000 for a utility bill payment this morning..."
                className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm font-medium outline-none focus:border-[#A01030] transition-all resize-none"
              />
              <button
                onClick={handleComplaintSubmit}
                disabled={!cText.trim() || cText.length < 10}
                className="w-full mt-4 bg-[#A01030] text-white py-4 rounded-xl font-bold text-sm shadow-lg shadow-red-900/20 disabled:opacity-50 active:scale-95 transition-all flex items-center justify-center gap-2"
              >
                Submit Complaint
              </button>
            </div>
          )}

          {/* Step 2: Sending */}
          {cStep === COMPLAINT_STEPS.SENDING && (
            <div className="flex flex-col items-center justify-center py-16 gap-4">
              <Loader2 size={36} className="text-[#A01030] animate-spin" />
              <p className="font-bold text-gray-700">Routing your complaint with AI...</p>
              <p className="text-xs text-gray-400 text-center max-w-xs">Our AI is analysing your complaint and routing it to the right department. This may take up to 60 seconds.</p>
            </div>
          )}

          {/* Step 3: Done */}
          {cStep === COMPLAINT_STEPS.DONE && cResult && (
            <div className="space-y-4">
              <div className="flex flex-col items-center py-6 gap-3">
                <div className="w-16 h-16 bg-green-50 rounded-full flex items-center justify-center">
                  <CheckCircle size={32} className="text-green-500" />
                </div>
                <h3 className="font-black text-gray-900 text-lg">Complaint Submitted!</h3>
                <p className="text-xs text-gray-500 text-center">Your complaint has been received and routed by our AI system.</p>
              </div>

              <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 space-y-3">
                <div className="flex justify-between text-xs border-b border-gray-50 pb-3">
                  <span className="text-gray-400 font-bold uppercase tracking-wide">Complaint ID</span>
                  <span className="font-bold text-gray-900 font-mono">{cResult.complaint_id}</span>
                </div>
                <div className="flex justify-between text-xs border-b border-gray-50 pb-3">
                  <span className="text-gray-400 font-bold uppercase tracking-wide">Department</span>
                  <span className="font-bold text-gray-900">{cResult.department_name}</span>
                </div>
                <div className="flex justify-between text-xs border-b border-gray-50 pb-3">
                  <span className="text-gray-400 font-bold uppercase tracking-wide">Priority</span>
                  <span className={`font-bold ${cResult.priority_level === 'High' ? 'text-red-600' : cResult.priority_level === 'Medium' ? 'text-orange-500' : 'text-green-600'}`}>
                    {cResult.priority_level}
                  </span>
                </div>
                <div className="flex justify-between text-xs border-b border-gray-50 pb-3">
                  <span className="text-gray-400 font-bold uppercase tracking-wide">SLA</span>
                  <span className="font-bold text-gray-900">{cResult.sla_hours}hrs</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-gray-400 font-bold uppercase tracking-wide">Confidence</span>
                  <span className="font-bold text-gray-900">{cResult.confidence ? `${Math.round(cResult.confidence * 100)}%` : '—'}</span>
                </div>
              </div>

              <div className="bg-blue-50 border border-blue-100 rounded-xl p-4 text-xs text-blue-700 leading-relaxed">
                <span className="font-bold">AI Reasoning: </span>{cResult.reasoning || 'Complaint routed based on content analysis.'}
              </div>

              <button
                onClick={resetComplaint}
                className="w-full bg-[#A01030] text-white py-4 rounded-xl font-bold text-sm shadow-lg shadow-red-900/20 active:scale-95 transition-all"
              >
                File Another Complaint
              </button>
              <button onClick={() => setMode(MODES.SELECT)} className="w-full text-gray-400 text-sm font-bold py-2">Back to Support</button>
            </div>
          )}

          {/* Error state */}
          {cStep === COMPLAINT_STEPS.ERROR && (
            <div className="flex flex-col items-center py-12 gap-4">
              <div className="w-16 h-16 bg-red-50 rounded-full flex items-center justify-center">
                <AlertTriangle size={28} className="text-[#A01030]" />
              </div>
              <p className="font-bold text-gray-800">Submission Failed</p>
              <p className="text-xs text-gray-500 text-center max-w-xs">{cError}</p>
              <button onClick={resetComplaint}
                className="px-6 py-3 bg-[#A01030] text-white rounded-xl font-bold text-sm active:scale-95 transition-all"
              >
                Try Again
              </button>
            </div>
          )}
        </div>
      </div>
    );
  }

  return null;
};

export default ChatScreen;