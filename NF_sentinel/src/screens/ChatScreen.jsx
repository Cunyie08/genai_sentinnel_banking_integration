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

// ─────────────────────────────────────────────────────────────────────────────
// parseAnswer — converts raw AI text into formatted React elements.
// Handles: bullet lines starting with - or •, numbered lists, **bold**, plain.
// ─────────────────────────────────────────────────────────────────────────────
const parseAnswer = (text) => {
  if (!text) return null;

  const parseBold = (str) => {
    const parts = str.split(/\*\*(.*?)\*\*/g);
    return parts.map((part, i) =>
      i % 2 === 1 ? <strong key={i} className="font-bold">{part}</strong> : part
    );
  };

  const lines = text.split('\n').map(l => l.trim()).filter(Boolean);
  const elements = [];
  let bulletBuffer = [];

  const flushBullets = (key) => {
    if (bulletBuffer.length === 0) return;
    elements.push(
      <ul key={`ul-${key}`} className="list-disc list-outside pl-4 space-y-1.5 my-2">
        {bulletBuffer.map((b, i) => (
          <li key={i} className="text-[14px] font-medium text-gray-800 dark:text-white leading-relaxed">
            {parseBold(b)}
          </li>
        ))}
      </ul>
    );
    bulletBuffer = [];
  };

  lines.forEach((line, idx) => {
    const isBullet = /^[-•]\s+/.test(line) || /^\d+\.\s+/.test(line);
    if (isBullet) {
      bulletBuffer.push(line.replace(/^[-•]\s+/, '').replace(/^\d+\.\s+/, ''));
    } else {
      flushBullets(idx);
      elements.push(
        <p key={`p-${idx}`} className="text-[14px] font-medium text-gray-800 dark:text-white leading-relaxed">
          {parseBold(line)}
        </p>
      );
    }
  });
  flushBullets('end');

  return <div className="space-y-1">{elements}</div>;
};

// ─────────────────────────────────────────────────────────────────────────────
// Conversational intent — messages that should never reach the FAQ API
// ─────────────────────────────────────────────────────────────────────────────
const CONVERSATIONAL_CLOSERS = [
  'thanks', 'thank you', 'thank u', 'thx', 'ty',
  'ok', 'okay', 'alright', 'cool', 'got it', 'noted',
  'nothing', 'nothing else', 'none', 'no', 'nope', 'nah',
  'bye', 'goodbye', 'done', 'im done', "i'm done", 'all done',
  'cancel', 'stop', 'exit', 'quit',
  "that's all", 'thats all', 'all good', "i'm good", 'im good',
  'no thanks', 'not really', 'not now', 'later', 'never mind',
  'nevermind', 'fine', 'good', 'great', 'perfect', 'nice',
  'not anymore', 'no more', 'nothing more', 'i am done', 'iam done',
];

const isConversationalCloser = (text) => {
  // Strip punctuation and normalise before matching
  const t = text
    .toLowerCase()
    .trim()
    .replace(/[.!?,]+/g, ' ')   // commas, periods etc → space
    .replace(/\s+/g, ' ')       // collapse multiple spaces
    .trim();

  // Exact match or "starts/ends with a closer" after stripping
  if (CONVERSATIONAL_CLOSERS.some(c => t === c)) return true;

  // Also catch compound phrases like "im done, thanks" or "ok thanks bye"
  // by checking if ALL meaningful words are closer-words
  const closerWords = new Set([
    'thanks', 'thank', 'you', 'ok', 'okay', 'alright', 'bye', 'goodbye',
    'done', 'im', 'i\'m', 'fine', 'good', 'great', 'none', 'nothing',
    'no', 'nope', 'nah', 'cool', 'noted', 'thx', 'ty', 'all', 'later',
    'cancel', 'stop', 'sure', 'yep', 'yes', 'perfect', 'got', 'it',
  ]);
  const words = t.split(' ').filter(w => w.length > 0);
  if (words.length > 0 && words.length <= 5 && words.every(w => closerWords.has(w))) {
    return true;
  }

  return false;
};

const CLOSER_REPLIES = [
  "Don't hesitate to reach out if you need anything else. Have a great day!",
  "Happy to help! Feel free to come back anytime — we're always here for you. Take care!",
  "Your satisfaction is our priority. Reach out anytime you need us. Have a wonderful day!",
];

// ─────────────────────────────────────────────────────────────────────────────
// Empathy openers — matched by keyword to the customer's query
// ─────────────────────────────────────────────────────────────────────────────
const EMPATHY_OPENERS = [
  { keywords: ['card', 'declin', 'block', 'reject'], opener: "I understand how frustrating a declining card can be — let me help you sort this out." },
  { keywords: ['transfer', 'wrong', 'reversal', 'recall', 'sent'], opener: "I'm sorry to hear about this — wrong transfers can be really stressful. Here's what you can do:" },
  { keywords: ['atm', 'cash', 'dispense', 'withdraw', 'machine'], opener: "That's a dispense error, and we take it seriously. Here's how to handle it quickly:" },
  { keywords: ['limit', 'daily', 'tier', 'kyc', 'upgrade'], opener: "Good question — your transfer limits are tied to your account tier. Here's a full breakdown:" },
  { keywords: ['fraud', 'unauthori', 'scam', 'suspicious', 'hack', 'stolen'], opener: "Your security is our absolute priority. Please act on this quickly — here's exactly what to do:" },
  { keywords: ['pin', 'password', 'lock', 'reset', 'forgot'], opener: "No worries at all — this is straightforward to resolve. Here's what you need to do:" },
  { keywords: ['account', 'balance', 'statement', 'history'], opener: "Of course, I can help with your account. Here's what you need to know:" },
  { keywords: ['loan', 'borrow', 'credit', 'interest'], opener: "I'd be happy to help with information on that. Here's what you need to know:" },
];

const getEmpathyOpener = (query) => {
  const q = query.toLowerCase();
  const match = EMPATHY_OPENERS.find(e => e.keywords.some(k => q.includes(k)));
  return match?.opener || "Of course, I can help with that. Here's what you need to know:";
};

// ─────────────────────────────────────────────────────────────────────────────
// ChatScreen
// ─────────────────────────────────────────────────────────────────────────────
const ChatScreen = () => {
  const navigate = useNavigate();
  const user = useSelector(s => s.auth.user);
  const accounts = user?.accounts || [];

  const [messages, setMessages] = useState([]);
  const [faqQuery, setFaqQuery] = useState('');
  const [faqLoading, setFaqLoading] = useState(false);

  const [escStep, setEscStep] = useState(ESC_STEPS.IDLE);
  const [escQuery, setEscQuery] = useState('');
  const [escAccount, setEscAccount] = useState('');
  const [escAccountObj, setEscAccountObj] = useState(null);
  const [escResult, setEscResult] = useState(null);
  const [escError, setEscError] = useState('');

  // Only the active unresolved escalation card shows action buttons.
  // Prevents stale cards from earlier in the conversation staying interactive.
  const [activeEscMsgId, setActiveEscMsgId] = useState(null);

  const scrollRef = useRef(null);

  useEffect(() => {
    const firstName = user?.name?.split(' ')[0] || 'there';
    setMessages([{
      id: 1, sender: 'ai', type: 'text',
      text: `Hello ${firstName}! Welcome to Sentinel Bank support. How can I assist you today? You can pick a common issue below or describe your situation in your own words.`,
      options: ['My card keeps declining', 'Wrong transfer reversal', 'ATM debit but no cash'],
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }]);
  }, [user?.name]);

  useEffect(() => {
    if (scrollRef.current)
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, faqLoading, escStep]);

  const addMsg = (msg) => setMessages(prev => [...prev, msg]);
  const now = () => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  // ─── Clean raw API answer text ──────────────────────────────────────────────
  const cleanAnswer = (raw) => {
    let cleaned = raw
      .replace(/channel\s*=\s*"atm"/gi, 'our ATM system')
      .replace(/failure_reason\s*=\s*"[^"]*"/gi, 'a daily limit')
      .replace(/transaction_status\s*=\s*"[^"]*"/gi, 'a temporary delay')
      .replace(/Step\s\d:/gi, '•')
      .trim();
    if (cleaned.includes('[HUMAN_RESPONSE]'))
      cleaned = cleaned.split('[HUMAN_RESPONSE]').pop().trim();
    else if (cleaned.includes('[CUSTOMER MESSAGE]'))
      cleaned = cleaned.split('[CUSTOMER MESSAGE]').pop().trim();
    return cleaned;
  };

  // ─── Warm reply for conversational closers ──────────────────────────────────
  const handleConversationalClose = (userText) => {
    addMsg({ id: Date.now(), sender: 'user', type: 'text', text: userText, time: now() });
    setTimeout(() => {
      addMsg({
        id: Date.now() + 1, sender: 'ai', type: 'text',
        text: CLOSER_REPLIES[Math.floor(Math.random() * CLOSER_REPLIES.length)],
        time: now(),
      });
    }, 400);
  };

  // ─── FAQ send ───────────────────────────────────────────────────────────────
  const handleFaqSend = async (overrideQuery) => {
    const q = (overrideQuery || faqQuery).trim();
    if (!q) return;
    setFaqQuery('');

    // Gate 1: conversational closers never reach the API
    if (isConversationalCloser(q)) {
      handleConversationalClose(q);
      return;
    }

    // Reset escalation state for each new question
    setEscStep(ESC_STEPS.IDLE);
    setEscQuery('');
    setEscResult(null);
    setActiveEscMsgId(null);

    addMsg({ id: Date.now(), sender: 'user', type: 'text', text: q, time: now() });
    setFaqLoading(true);

    try {
      const res = await api.getFaqs(q);
      const d = res?.data || {};
      const matchFound = d.success === true;

      const rawAnswer = matchFound
        ? (d.match?.answer || 'Please refer to our FAQ for more details.')
        : (d.message || "I wasn't able to find a specific answer for this.");

      const cleaned = cleanAnswer(rawAnswer);

      if (matchFound) {
        // Prepend a warm empathy opener before the FAQ answer
        const opener = getEmpathyOpener(q);
        const fullText = `${opener}\n\n${cleaned}`;
        addMsg({ id: Date.now(), sender: 'ai', type: 'text', text: fullText, time: now() });

        // Follow-up "did this help?" after a short natural delay
        setTimeout(() => {
          addMsg({
            id: Date.now() + 1, sender: 'ai', type: 'resolution-check',
            originalQuery: q, time: now(),
          });
        }, 600);
      } else {
        // Gate 2: short topic labels (no verb, ≤4 words) ask for more detail
        // instead of jumping straight to escalation
        const wordCount = q.trim().split(/\s+/).length;
        const hasVerb = /\b(is|are|was|were|have|has|had|do|does|did|can|could|keep|keeps|want|need|help|fix|check|update|change|why|how|what|when|where|getting|showing|failed|failing|blocked|declined|missing|sent|charged|deducted|reversed|locked|stolen|lost)\b/i.test(q);
        const hasSupportIntent = /\b(card|transfer|atm|account|limit|fraud|pin|balance|loan|statement|charge|debit|credit|transaction|payment|bank|money|fund|wallet|complaint)\b/i.test(q);
        const isTopicLabel = wordCount <= 4 && !hasVerb && hasSupportIntent;
        const isMeaningless = wordCount <= 3 && !hasSupportIntent;

        if (isMeaningless) {
          // Catches "none", "idk", "hmm", random short non-support text
          addMsg({
            id: Date.now(), sender: 'ai', type: 'text',
            text: "I'm here whenever you're ready! Feel free to describe your issue and I'll do my best to help.",
            time: now(),
          });
    } else if (isTopicLabel) {
      addMsg({
        id: Date.now(), sender: 'ai', type: 'text',
        text: `I'd be happy to help with that. Could you describe what's happening in a little more detail? For example — which transaction, what error message you're seeing, or what you've already tried. The more you share, the better I can assist.`,
        time: now(),
      });
    } else {
      // Real descriptive query with no match — offer warm escalation
      const escMsgId = Date.now();
      const warmEscText = `I wasn't able to find a specific answer for your concern about "${q}" in our knowledge base. Let me connect you with the right support team — they'll review this personally and follow up with you directly.`;
      addMsg({
        id: escMsgId, sender: 'ai', type: 'escalation',
        text: warmEscText, time: now(),
      });
      setEscQuery(q);
      setActiveEscMsgId(escMsgId);

        }
      }
    } catch (err) {
      console.error('[FAQ] Error:', err);
      addMsg({
        id: Date.now(), sender: 'ai', type: 'text',
        text: "I'm sorry, I'm having trouble reaching our knowledge base right now. Please try again in a moment, or contact us directly at 0700-SENTINEL.",
        time: now(),
      });
    } finally {
      setFaqLoading(false);
    }
  };

  // ─── Customer says "need more help" after an AI answer ─────────────────────
  const handleNotResolved = (originalQuery) => {
    setEscQuery(originalQuery);
    const escMsgId = Date.now();
    addMsg({
      id: escMsgId, sender: 'ai', type: 'escalation',
      text: "I understand this needs more attention. Let me connect you with a specialist on our team — they'll look into this personally and get back to you as soon as possible.",
      time: now(),
    });
    setActiveEscMsgId(escMsgId);
    setEscStep(ESC_STEPS.IDLE);
  };

  // ─── Customer confirms resolved ─────────────────────────────────────────────
  const handleResolved = () => {
    addMsg({
      id: Date.now(), sender: 'ai', type: 'text',
      text: "Wonderful! I'm glad we could sort that out for you. Is there anything else I can help you with today?",
      options: ['My card keeps declining', 'Wrong transfer reversal', 'ATM debit but no cash'],
      time: now(),
    });
    setActiveEscMsgId(null);
    setEscStep(ESC_STEPS.IDLE);
  };

  // ─── Escalation submit ──────────────────────────────────────────────────────
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
      setActiveEscMsgId(null);

      const reasoning = res.data?.reasoning || '';
      const cleanedReasoning = reasoning.includes('[CUSTOMER MESSAGE]')
        ? reasoning.split('[CUSTOMER MESSAGE]').pop().trim()
        : reasoning;

      const department = res.data?.department || res.data?.routed_to || 'our specialist team';
      const refNumber = `SNT-${Math.floor(100000 + Math.random() * 900000)}`;
      const baseReasoning = cleanedReasoning || 'Your concern has been received and reviewed by our system.';
      const warmConfirmation = `${baseReasoning}\n\nYour complaint has been escalated to ${department}. **Reference: ${refNumber}**\n\nA team member will follow up via your registered contact details within **24–48 hours**. You don't need to call in — we have everything we need to look into this for you.`;

      addMsg({
        id: Date.now(), sender: 'ai', type: 'routing-result',
        text: warmConfirmation, result: res.data, time: now(),
      });

      // Natural follow-up after the confirmation lands
      setTimeout(() => {
        addMsg({
          id: Date.now() + 1, sender: 'ai', type: 'text',
          text: "While you wait for our team, is there anything else I can help you with today?",
          options: ['My card keeps declining', 'Wrong transfer reversal', 'ATM debit but no cash'],
          time: now(),
        });
      }, 700);
    } catch (err) {
      setEscError(err?.detail || 'We were unable to submit your complaint at this time. Please try again or call 0700-SENTINEL.');
      setEscStep(ESC_STEPS.ERROR);
    }
  };

  const resetEscalation = () => {
    setEscStep(ESC_STEPS.IDLE);
    setEscAccount('');
    setEscAccountObj(null);
    setEscResult(null);
    setEscError('');
    setActiveEscMsgId(null);
  };

  // ─── Header ─────────────────────────────────────────────────────────────────
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

  // ─── Message renderer ────────────────────────────────────────────────────────
  const renderMessage = (msg) => {

    // User bubble
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

    // AI bubble with option chips — welcome message and post-resolution follow-ups
    if (msg.options && msg.type !== 'resolution-check') {
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

    // "Did this help?" — appears only after a successful FAQ match
    if (msg.type === 'resolution-check') {
      return (
        <div key={msg.id} className="flex flex-col">
          <div className="flex items-center gap-2 mb-1">
            <div className="w-5 h-5 vault-gradient text-white rounded-full flex items-center justify-center">
              <Bot size={12} />
            </div>
            <span className="text-xs font-bold text-gray-400 dark:text-slate-500">AI Assistant</span>
          </div>
          <div className="bg-white dark:bg-vault-dark-card p-4 rounded-[20px] rounded-tl-none shadow-sm border border-gray-100 dark:border-white/5 max-w-[90%]">
            <p className="text-[14px] font-medium text-gray-800 dark:text-white leading-relaxed mb-3">
              Was that helpful? I want to make sure your issue is fully resolved.
            </p>
            <div className="flex gap-2">
              <button
                onClick={handleResolved}
                className="flex-1 flex items-center justify-center gap-1.5 py-2.5 bg-green-50 dark:bg-green-500/10 text-green-700 dark:text-green-400 rounded-xl font-bold text-sm border border-green-200 dark:border-green-500/20 hover:bg-green-100 dark:hover:bg-green-500/20 transition-all active:scale-95"
              >
                <CheckCircle size={14} /> Yes, resolved
              </button>
              <button
                onClick={() => handleNotResolved(msg.originalQuery || '')}
                className="flex-1 flex items-center justify-center gap-1.5 py-2.5 bg-gray-50 dark:bg-white/5 text-gray-600 dark:text-slate-300 rounded-xl font-bold text-sm border border-gray-200 dark:border-white/10 hover:bg-gray-100 dark:hover:bg-white/10 transition-all active:scale-95"
              >
                <HelpCircle size={14} /> Need more help
              </button>
            </div>
          </div>
          <span className="text-[10px] text-gray-400 dark:text-slate-500 mt-1">{msg.time}</span>
        </div>
      );
    }

    // Escalation card — action buttons visible only on the active unresolved card
    if (msg.type === 'escalation') {
      const isActive = msg.id === activeEscMsgId;
      return (
        <div key={msg.id} className="flex flex-col">
          <div className="flex items-center gap-2 mb-1">
            <div className="w-5 h-5 vault-gradient text-white rounded-full flex items-center justify-center">
              <Bot size={12} />
            </div>
            <span className="text-xs font-bold text-gray-400 dark:text-slate-500">AI Assistant</span>
          </div>
          <div className="bg-white dark:bg-vault-dark-card p-4 rounded-[20px] rounded-tl-none shadow-sm border border-gray-100 dark:border-white/5 max-w-[90%]">
            {isActive && (
              <div className="flex items-center gap-2 mb-3">
                <AlertTriangle size={16} className="text-amber-500" />
                <span className="text-[11px] font-black text-amber-500 uppercase tracking-wide">Connecting you with support</span>
              </div>
            )}
            <p className="text-[14px] font-medium text-gray-800 dark:text-white leading-relaxed mb-4">
              {msg.text}
            </p>
            {isActive && escStep === ESC_STEPS.IDLE && (
              <div>
                <p className="text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-2">How would you like to proceed?</p>
                <div className="flex gap-3">
                  <button
                    onClick={() => setEscStep(ESC_STEPS.ACCOUNT)}
                    className="flex-1 vault-gradient text-white py-3 rounded-xl font-bold text-sm shadow-lg vault-glow active:scale-95 transition-all"
                  >
                    Escalate
                  </button>
                  <button
                    onClick={resetEscalation}
                    className="flex-1 bg-white dark:bg-white/5 text-gray-600 dark:text-slate-300 py-3 rounded-xl font-bold text-sm border border-gray-200 dark:border-white/5 active:scale-95 transition-all"
                  >
                    Not right now
                  </button>
                </div>
              </div>
            )}
          </div>
          <span className="text-[10px] text-gray-400 dark:text-slate-500 mt-1">{msg.time}</span>
        </div>
      );
    }

    // Routing result — dispatcher confirmation with reference number and timeline
    if (msg.type === 'routing-result' && msg.result) {
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
              <span className="text-sm font-black text-green-700 dark:text-green-400">Your complaint has been received</span>
            </div>
            <div className="p-4 space-y-1">
              {parseAnswer(msg.text)}
            </div>
          </div>
          <span className="text-[10px] text-gray-400 dark:text-slate-500 mt-1">{msg.time}</span>
        </div>
      );
    }

    // Default AI text bubble — parseAnswer handles bullets, numbered lists, bold
    return (
      <div key={msg.id} className="flex flex-col">
        <div className="flex items-center gap-2 mb-1">
          <div className="w-5 h-5 vault-gradient text-white rounded-full flex items-center justify-center">
            <Bot size={12} />
          </div>
          <span className="text-xs font-bold text-gray-400 dark:text-slate-500">AI Assistant</span>
        </div>
        <div className="bg-white dark:bg-vault-dark-card p-4 rounded-[20px] rounded-tl-none shadow-sm border border-gray-100 dark:border-white/5 max-w-[90%]">
          {parseAnswer(msg.text)}
        </div>
        <span className="text-[10px] text-gray-400 dark:text-slate-500 mt-1">{msg.time}</span>
      </div>
    );
  };

  // ─── Account selector panel ──────────────────────────────────────────────────
  const renderAccountSelector = () => {
    if (escStep !== ESC_STEPS.ACCOUNT) return null;

    return (
      <div className="bg-white dark:bg-vault-dark-card rounded-2xl p-5 shadow-sm border border-gray-100 dark:border-white/5 mx-1 mt-2">
        <p className="text-xs font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-1">Select Account</p>
        <p className="text-base font-black text-gray-900 dark:text-white mb-1">Which account is this related to?</p>
        <p className="text-xs text-gray-500 dark:text-slate-400 mb-4">
          Select the account linked to your complaint. Our AI will route it to the right department immediately.
        </p>

        {accounts.length > 0 ? (
          <div className="space-y-3">
            {accounts.map(acc => {
              const typeLabel = acc.account_type || 'Account';
              const typeColor =
                typeLabel.toLowerCase() === 'savings'
                  ? { bg: 'bg-blue-50 dark:bg-blue-500/10', text: 'text-blue-700 dark:text-blue-400', border: 'border-blue-200 dark:border-blue-500/20' }
                  : typeLabel.toLowerCase() === 'current'
                  ? { bg: 'bg-green-50 dark:bg-green-500/10', text: 'text-green-700 dark:text-green-400', border: 'border-green-200 dark:border-green-500/20' }
                  : typeLabel.toLowerCase() === 'solo'
                  ? { bg: 'bg-purple-50 dark:bg-purple-500/10', text: 'text-purple-700 dark:text-purple-400', border: 'border-purple-200 dark:border-purple-500/20' }
                  : { bg: 'bg-gray-50 dark:bg-white/5', text: 'text-gray-700 dark:text-slate-300', border: 'border-gray-200 dark:border-white/10' };

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
                        Balance: <span className="font-bold text-gray-700 dark:text-white">
                          ₦{Number(acc.balance).toLocaleString('en-NG', { minimumFractionDigits: 2 })}
                        </span>
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
              type="text"
              maxLength={20}
              value={escAccount}
              onChange={e => setEscAccount(e.target.value)}
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
        <p className="font-bold text-gray-700 dark:text-white">Connecting you with our team...</p>
        <p className="text-xs text-gray-400 dark:text-slate-500 text-center max-w-xs">
          Our AI is reviewing your complaint and routing it to the most appropriate department right now.
        </p>
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
        <p className="font-bold text-gray-800 dark:text-white">Something went wrong</p>
        <p className="text-xs text-gray-500 dark:text-slate-400 text-center max-w-xs">{escError}</p>
        <button
          onClick={() => setEscStep(ESC_STEPS.ACCOUNT)}
          className="px-6 py-3 vault-gradient text-white rounded-xl font-bold text-sm active:scale-95 transition-all vault-glow"
        >
          Try Again
        </button>
      </div>
    );
  };

  // ─── Main render ─────────────────────────────────────────────────────────────
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
            <Loader2 size={14} className="animate-spin" /> Looking that up for you...
          </div>
        )}
      </div>

      <div className="bg-white dark:bg-vault-dark-card border-t border-gray-50 dark:border-white/5 px-4 pt-3 pb-1 vault-transition">
        <p className="text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-2">Quick Actions</p>
        <div className="flex gap-2 overflow-x-auto hide-scrollbar pb-2">
          {[
            'My card keeps declining',
            'Wrong transfer reversal',
            'ATM debit but no cash',
          ].map((q, i) => (
            <button
              key={i}
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
              type="text"
              value={faqQuery}
              onChange={e => setFaqQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleFaqSend()}
              placeholder="Describe your issue..."
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