import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import {
  ChevronLeft, Send, Bot, ChevronRight,
  AlertTriangle, CheckCircle,
  HelpCircle, MessageSquareWarning, Loader2,
  ShieldAlert, CreditCard, ArrowLeftRight, Landmark,
  Phone, Mail, Info, AlertCircle, Banknote, Lock,
  TrendingUp, Clock, Star, ExternalLink, Copy, CheckCheck
} from 'lucide-react';
import { api } from '../api/axiosConfig';

const ESC_STEPS = { IDLE: 0, ACCOUNT: 1, SENDING: 2, DONE: 3, ERROR: 4 };

// ─────────────────────────────────────────────────────────────────────────────
// Detect content type for smart rendering
// ─────────────────────────────────────────────────────────────────────────────
const detectContentType = (text) => {
  if (!text) return 'plain';
  if (/step\s*\d+[:.]|^\d+\.\s/im.test(text)) return 'steps';
  if (/tier\s*\d|₦[\d,]+\/day|limit/i.test(text)) return 'table';
  if (/call\s+0700|email.*@|dial\s+\*/i.test(text)) return 'contact';
  if (/\bwarn|never share|scam|block.*immediately|act immediately/i.test(text)) return 'alert';
  if (/₦[\d,]+.*₦[\d,]+|fee.*free|charge.*₦/i.test(text)) return 'fees';
  return 'standard';
};

// ─────────────────────────────────────────────────────────────────────────────
// CopyButton — lets customers copy key info (account numbers, codes, refs)
// ─────────────────────────────────────────────────────────────────────────────
const CopyButton = ({ text }) => {
  const [copied, setCopied] = useState(false);
  const handleCopy = () => {
    navigator.clipboard?.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };
  return (
    <button
      onClick={handleCopy}
      className="ml-1.5 inline-flex items-center gap-1 px-1.5 py-0.5 bg-gray-100 dark:bg-white/10 rounded text-[10px] font-bold text-gray-500 dark:text-slate-400 hover:bg-cyan-50 dark:hover:bg-vault-cyan/15 hover:text-vault-cyan transition-all"
    >
      {copied ? <CheckCheck size={10} /> : <Copy size={10} />}
      {copied ? 'Copied' : 'Copy'}
    </button>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// parseBold — inline **bold** and `code` rendering
// ─────────────────────────────────────────────────────────────────────────────
const parseBold = (str) => {
  if (!str) return null;
  // Handle both **bold** and `code` inline
  const parts = str.split(/(\*\*.*?\*\*|`[^`]+`)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i} className="font-black text-gray-900 dark:text-white">{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return (
        <code key={i} className="px-1.5 py-0.5 bg-gray-100 dark:bg-white/10 rounded text-[12px] font-mono text-vault-cyan">
          {part.slice(1, -1)}
        </code>
      );
    }
    // Highlight phone numbers and emails
    const phoneMatch = part.match(/(0700-SENTINEL|0700-\d+|\*\d+[#*]\S*)/g);
    if (phoneMatch) {
      const segments = part.split(/(0700-SENTINEL|0700-\d+|\*\d+[#*]\S*)/g);
      return segments.map((seg, j) => {
        if (/(0700-SENTINEL|0700-\d+|\*\d+[#*]\S*)/.test(seg)) {
          return (
            <span key={`${i}-${j}`} className="inline-flex items-center gap-0.5 font-mono font-bold text-vault-cyan">
              {seg}
            </span>
          );
        }
        return seg;
      });
    }
    return part;
  });
};

// ─────────────────────────────────────────────────────────────────────────────
// StepCard — renders numbered steps with visual progression
// ─────────────────────────────────────────────────────────────────────────────
const StepCard = ({ number, text }) => (
  <div className="flex gap-3 items-start">
    <div className="shrink-0 w-7 h-7 rounded-full vault-gradient flex items-center justify-center shadow-sm">
      <span className="text-[11px] font-black text-white">{number}</span>
    </div>
    <div className="flex-1 pt-0.5">
      <p className="text-[13.5px] font-medium text-gray-800 dark:text-white leading-relaxed">
        {parseBold(text)}
      </p>
    </div>
  </div>
);

// ─────────────────────────────────────────────────────────────────────────────
// TierTable — renders tiered limit tables beautifully
// ─────────────────────────────────────────────────────────────────────────────
const TierTable = ({ rows }) => (
  <div className="mt-2 rounded-xl overflow-hidden border border-gray-100 dark:border-white/8">
    {rows.map((row, i) => (
      <div key={i} className={`flex items-center justify-between px-3 py-2.5 ${i % 2 === 0 ? 'bg-gray-50/80 dark:bg-white/3' : 'bg-white dark:bg-transparent'}`}>
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${i === 0 ? 'bg-gray-400' : i === 1 ? 'bg-blue-400' : 'bg-green-500'}`} />
          <span className="text-[12.5px] font-semibold text-gray-700 dark:text-slate-300">{row.label}</span>
        </div>
        <span className="text-[12.5px] font-black text-gray-900 dark:text-white">{row.value}</span>
      </div>
    ))}
  </div>
);

// ─────────────────────────────────────────────────────────────────────────────
// ContactCard — renders phone/email contact info as tappable cards
// ─────────────────────────────────────────────────────────────────────────────
const ContactCard = ({ type, value }) => {
  const isPhone = type === 'phone';
  return (
    <a
      href={isPhone ? `tel:${value.replace(/\D/g, '')}` : `mailto:${value}`}
      className="flex items-center gap-2.5 p-2.5 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-100 dark:border-white/8 hover:bg-cyan-50 dark:hover:bg-vault-cyan/10 hover:border-cyan-200 dark:hover:border-vault-cyan/25 transition-all group"
    >
      <div className="w-7 h-7 vault-gradient rounded-lg flex items-center justify-center shrink-0">
        {isPhone ? <Phone size={13} className="text-white" /> : <Mail size={13} className="text-white" />}
      </div>
      <span className="text-[13px] font-bold text-gray-800 dark:text-white group-hover:text-vault-cyan transition-colors">{value}</span>
      <ExternalLink size={12} className="ml-auto text-gray-300 dark:text-slate-600 group-hover:text-vault-cyan" />
    </a>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// AlertBanner — urgent/security warnings
// ─────────────────────────────────────────────────────────────────────────────
const AlertBanner = ({ text }) => (
  <div className="flex gap-2.5 p-3 bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 rounded-xl">
    <ShieldAlert size={16} className="text-red-500 shrink-0 mt-0.5" />
    <p className="text-[13px] font-semibold text-red-700 dark:text-red-400 leading-relaxed">{parseBold(text)}</p>
  </div>
);

// ─────────────────────────────────────────────────────────────────────────────
// InfoChip — inline metadata chips (fees, timelines, etc.)
// ─────────────────────────────────────────────────────────────────────────────
const InfoChip = ({ icon: Icon, label, value, color = 'blue' }) => {
  const colors = {
    blue: 'bg-blue-50 dark:bg-blue-500/10 text-blue-700 dark:text-blue-400 border-blue-100 dark:border-blue-500/20',
    green: 'bg-green-50 dark:bg-green-500/10 text-green-700 dark:text-green-400 border-green-100 dark:border-green-500/20',
    amber: 'bg-amber-50 dark:bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-100 dark:border-amber-500/20',
    cyan: 'bg-cyan-50 dark:bg-cyan-500/10 text-vault-cyan border-cyan-100 dark:border-vault-cyan/25',
  };
  return (
    <div className={`inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border text-[12px] font-bold ${colors[color]}`}>
      {Icon && <Icon size={11} />}
      <span className="text-[10.5px] font-semibold opacity-75">{label}:</span>
      <span>{value}</span>
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// NoteCard — highlighted notes / important callouts
// ─────────────────────────────────────────────────────────────────────────────
const NoteCard = ({ text }) => (
  <div className="flex gap-2 p-2.5 bg-amber-50 dark:bg-amber-500/8 border border-amber-200 dark:border-amber-500/20 rounded-xl">
    <Info size={14} className="text-amber-500 shrink-0 mt-0.5" />
    <p className="text-[12.5px] font-medium text-amber-800 dark:text-amber-400 leading-relaxed">{parseBold(text)}</p>
  </div>
);

// ─────────────────────────────────────────────────────────────────────────────
// BulletItem — enhanced bullet with left accent
// ─────────────────────────────────────────────────────────────────────────────
const BulletItem = ({ text }) => {
  const isNote = /^note[:\s]/i.test(text);
  const isWarning = /warning|never|do not|don't|important/i.test(text);

  if (isNote) return <NoteCard text={text.replace(/^note[:\s]*/i, '')} />;
  if (isWarning) return (
    <div className="flex gap-2.5 items-start">
      <AlertCircle size={14} className="text-amber-500 shrink-0 mt-1" />
      <p className="text-[13.5px] font-medium text-amber-700 dark:text-amber-400 leading-relaxed">{parseBold(text)}</p>
    </div>
  );

  return (
    <div className="flex gap-2.5 items-start">
      <div className="w-1.5 h-1.5 rounded-full bg-vault-cyan shrink-0 mt-2" />
      <p className="text-[13.5px] font-medium text-gray-800 dark:text-white leading-relaxed flex-1">
        {parseBold(text)}
      </p>
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// extractTierRows — parse tier/limit lines into table rows
// ─────────────────────────────────────────────────────────────────────────────
const extractTierRows = (lines) => {
  return lines
    .filter(l => /tier\s*\d|basic|premium|standard|savings|current|solo/i.test(l))
    .map(l => {
      const [label, ...rest] = l.replace(/^[-•]\s*/, '').split(':');
      return { label: label.trim(), value: rest.join(':').trim() };
    })
    .filter(r => r.label && r.value);
};

// ─────────────────────────────────────────────────────────────────────────────
// extractContacts — pull phone numbers and emails from text
// ─────────────────────────────────────────────────────────────────────────────
const extractContacts = (text) => {
  const contacts = [];
  const phoneMatches = text.match(/0700-SENTINEL|0700-[\d-]+|\+234-[\d-]+/gi) || [];
  const emailMatches = text.match(/[\w.-]+@[\w.-]+\.\w+/gi) || [];
  phoneMatches.forEach(p => contacts.push({ type: 'phone', value: p }));
  emailMatches.forEach(e => contacts.push({ type: 'email', value: e }));
  return [...new Map(contacts.map(c => [c.value, c])).values()]; // dedupe
};

// ─────────────────────────────────────────────────────────────────────────────
// parseAnswer — the ENHANCED version: smart, structured, beautiful
// ─────────────────────────────────────────────────────────────────────────────
const parseAnswer = (text) => {
  if (!text) return null;

  const lines = text.split('\n').map(l => l.trim()).filter(Boolean);
  const elements = [];
  let stepBuffer = [];
  let bulletBuffer = [];
  let inFeeSection = false;

  const flushSteps = (key) => {
    if (!stepBuffer.length) return;
    elements.push(
      <div key={`steps-${key}`} className="space-y-3 my-2">
        {stepBuffer.map((s, i) => <StepCard key={i} number={i + 1} text={s} />)}
      </div>
    );
    stepBuffer = [];
  };

  const flushBullets = (key) => {
    if (!bulletBuffer.length) return;

    // Check if these look like tier/limit rows → render as table
    const tierRows = extractTierRows(bulletBuffer.map(b => b));
    if (tierRows.length >= 2) {
      elements.push(<TierTable key={`table-${key}`} rows={tierRows} />);
      bulletBuffer = [];
      return;
    }

    elements.push(
      <div key={`bullets-${key}`} className="space-y-2 my-1.5">
        {bulletBuffer.map((b, i) => <BulletItem key={i} text={b} />)}
      </div>
    );
    bulletBuffer = [];
  };

  lines.forEach((line, idx) => {
    const isNumberedStep = /^(step\s*\d+[:.]|\d+\.\s+)/i.test(line);
    const isBullet = /^[-•]\s+/.test(line);
    const isNote = /^note[:\s]/i.test(line);
    const isAlert = /^(warning|important|caution)[:\s!]/i.test(line);
    const isFeeHeader = /fee|charge|cost|price/i.test(line) && !isBullet && !isNumberedStep;

    if (isNumberedStep) {
      flushBullets(idx);
      const cleanStep = line.replace(/^(step\s*\d+[:.\s]+|\d+\.\s+)/i, '').trim();
      stepBuffer.push(cleanStep);
      return;
    }

    if (isBullet) {
      flushSteps(idx);
      const cleanBullet = line.replace(/^[-•]\s+/, '').trim();
      bulletBuffer.push(cleanBullet);
      return;
    }

    // Flush any pending buffers before a paragraph
    flushSteps(idx);
    flushBullets(idx);

    if (isNote) {
      elements.push(<NoteCard key={`note-${idx}`} text={line.replace(/^note[:\s]*/i, '')} />);
      return;
    }

    if (isAlert) {
      elements.push(<AlertBanner key={`alert-${idx}`} text={line.replace(/^(warning|important|caution)[:\s!]*/i, '')} />);
      return;
    }

    // Paragraph with potential inline highlights
    elements.push(
      <p key={`p-${idx}`} className="text-[14px] font-medium text-gray-800 dark:text-white leading-relaxed">
        {parseBold(line)}
      </p>
    );
  });

  flushSteps('end');
  flushBullets('end');

  // Append extracted contact cards if present
  const contacts = extractContacts(text);
  if (contacts.length > 0) {
    elements.push(
      <div key="contacts" className="mt-3 space-y-2">
        <p className="text-[10px] font-black text-gray-400 dark:text-slate-500 uppercase tracking-widest">Contact Support</p>
        {contacts.map((c, i) => <ContactCard key={i} type={c.type} value={c.value} />)}
      </div>
    );
  }

  return <div className="space-y-2">{elements}</div>;
};

// ─────────────────────────────────────────────────────────────────────────────
// QuickInfoBar — shows at top of AI answer with relevant metadata chips
// ─────────────────────────────────────────────────────────────────────────────
const QuickInfoBar = ({ text, query }) => {
  const chips = [];
  const q = (query || '').toLowerCase();

  // Resolution time — only show if not a limit/tier answer
  const timeMatch = text.match(/(\d+[-–]\d+\s*(?:hours?|days?|business\s*days?|minutes?))/i);
  if (timeMatch && !/limit|tier|daily/i.test(text.slice(0, 80))) {
    chips.push({ icon: Clock, label: 'Resolution', value: timeMatch[1], color: 'blue' });
  }

  // Actual service fee — must match fee/charge/cost/flat context, NOT limit amounts like ₦500,000/day
  // We specifically exclude patterns like ₦X/day or ₦X (Standard) which are limits, not fees
  const feeMatch = text.match(/₦([\d,]+)\s*(?:flat fee|per letter|fee applies|replacement fee|card fee|per alert|per session|per withdrawal)/i);
  if (feeMatch) {
    chips.push({ icon: Banknote, label: 'Fee', value: `₦${feeMatch[1]}`, color: 'amber' });
  }

  // Free — only if answer explicitly says same-bank is free or service is free
  const hasFreeService = /same.?bank.*free|free.*transfer|no.*fee|free of charge|completely free/i.test(text);
  if (hasFreeService && !feeMatch) {
    chips.push({ icon: Star, label: 'Cost', value: 'Free', color: 'green' });
  }

  // Instant — for loan disbursements, salary advance, own-account transfers
  if (/\binstant(ly|ly disbursed|ly credited)?\b/i.test(text) && !/instant message|instantly replace/i.test(text)) {
    chips.push({ icon: TrendingUp, label: 'Speed', value: 'Instant', color: 'cyan' });
  }

  // SLA / processing time — e.g. "3–5 business days"
  const slaMatch = text.match(/(3[-–]5|5[-–]7|24[-–]48|1[-–]3)\s*business\s*days?/i);
  if (slaMatch && !timeMatch) {
    chips.push({ icon: Clock, label: 'Processing', value: slaMatch[0], color: 'blue' });
  }

  if (chips.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-1.5 mb-3">
      {chips.slice(0, 3).map((chip, i) => (
        <InfoChip key={i} icon={chip.icon} label={chip.label} value={chip.value} color={chip.color} />
      ))}
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// TopicIcon — small icon that matches the topic of the message
// ─────────────────────────────────────────────────────────────────────────────
const getTopicIcon = (text) => {
  if (!text) return null;
  const t = text.toLowerCase();
  if (/card|declin|pin|block|stolen|chip|atm/.test(t)) return CreditCard;
  if (/transfer|send|money|reversal|wrong|beneficiary/.test(t)) return ArrowLeftRight;
  if (/fraud|scam|unauthori|hack|security|phish/.test(t)) return ShieldAlert;
  if (/account|kyc|tier|upgrade|bvn|nin/.test(t)) return Landmark;
  if (/loan|credit|overdraft|salary/.test(t)) return Banknote;
  if (/password|otp|lock|login|biometric/.test(t)) return Lock;
  return null;
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
  const t = text
    .toLowerCase()
    .trim()
    .replace(/[.!?,]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

  if (CONVERSATIONAL_CLOSERS.some(c => t === c)) return true;

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
// Empathy openers — ordered most-specific FIRST to avoid wrong matches
// ─────────────────────────────────────────────────────────────────────────────
const EMPATHY_OPENERS = [
  // Card lost/stolen/block — must come before generic 'card' match
  { keywords: ['lost my card', 'card is lost', 'stolen card', 'card stolen', 'card missing', 'lost card', 'block my card', 'block card', 'card blocked', 'card theft', 'freeze my card'], opener: "I'm really sorry to hear that — here's exactly how to protect your account right away:" },
  // Fraud / unauthorised — before generic 'card'
  { keywords: ['fraud', 'unauthori', 'scam', 'suspicious', 'hacked', 'phish', 'someone used my card', 'unauthorised transaction'], opener: "Your security is our absolute priority. Please act on this quickly — here's exactly what to do:" },
  // Card declining specifically
  { keywords: ['card keeps declining', 'card declin', 'card rejected', 'card not working', 'card failed', 'keeps failing', 'card not accepted'], opener: "I understand how frustrating a declining card can be — let me help you sort this out." },
  // Wrong / mistaken transfers
  { keywords: ['wrong transfer', 'wrong account', 'mistaken transfer', 'sent to wrong', 'wrong person', 'reversal', 'recall transfer'], opener: "I'm sorry to hear about this — wrong transfers can be really stressful. Here's what you can do:" },
  // ATM cash issues
  { keywords: ['atm', 'cash not dispensed', 'no cash', 'dispense', 'machine debited', 'atm debit'], opener: "That's a dispense error, and we take it seriously. Here's how to handle it quickly:" },
  // Transfer / daily limits
  { keywords: ['transfer limit', 'daily limit', 'sending limit', 'limit exceeded', 'increase my limit', 'increase limit'], opener: "Your transfer limits are tied to your account tier. Here's the full breakdown:" },
  // Account upgrade / KYC
  { keywords: ['upgrade my account', 'upgrade account', 'upgrade tier', 'increase tier', 'kyc upgrade', 'tier upgrade'], opener: "Great — upgrading your account is straightforward. Here's exactly what you need to do:" },
  // PIN / password / login
  { keywords: ['pin', 'password', 'lock', 'reset', 'forgot', 'login', 'otp', 'biometric'], opener: "No worries at all — this is straightforward to resolve. Here's what you need to do:" },
  // Transfer debited / pending / not received
  { keywords: ['debited but', 'not received', 'transfer pending', 'pending transfer', 'transfer failed', 'money not sent', 'beneficiary not received'], opener: "I understand how worrying this can be. Let me walk you through exactly what to do:" },
  // Loan / credit
  { keywords: ['loan', 'borrow', 'credit', 'overdraft', 'salary advance', 'interest rate'], opener: "I'd be happy to help with that. Here's everything you need to know:" },
  // Savings / investment
  { keywords: ['savings', 'fixed deposit', 'investment', 'interest', 'solo account'], opener: "Great question on growing your money. Here's what Sentinel Bank offers:" },
  // Account / balance / statement
  { keywords: ['account', 'balance', 'statement', 'history', 'transaction history'], opener: "Of course, I can help with your account. Here's what you need to know:" },
];

const getEmpathyOpener = (query) => {
  const q = query.toLowerCase();
  // Use find — first match wins (most specific rules are listed first)
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
      // IMPORTANT: Do NOT strip "Step N:" — the parseAnswer renderer uses it to build StepCards
      .trim();
    if (cleaned.includes('[HUMAN_RESPONSE]'))
      cleaned = cleaned.split('[HUMAN_RESPONSE]').pop().trim();
    else if (cleaned.includes('[CUSTOMER MESSAGE]'))
      cleaned = cleaned.split('[CUSTOMER MESSAGE]').pop().trim();
    return cleaned;
  };

  // ─── Normalize query before sending to FAQ API ──────────────────────────────
  // Maps colloquial / shorthand phrasing to canonical questions the RAG expects,
  // so queries like "I want to block my card" or "how do I upgrade" actually
  // hit the right FAQ entry instead of returning no match.
  const normalizeQuery = (raw) => {
    const q = raw.toLowerCase().trim();

    const QUERY_MAP = [
      // Card lost / stolen / block
      [/lost\s+my\s+card|my\s+card\s+(is\s+)?lost|card\s+missing/i,         'My card is lost. What should I do?'],
      [/stolen\s+card|card\s+(got\s+)?stolen|someone\s+stole\s+my\s+card/i,  'My card got stolen. How do I block it immediately?'],
      [/block\s+my\s+card|i\s+want\s+to\s+block|how\s+(do\s+i\s+)?block\s+(my\s+)?card/i, 'My card got stolen. How do I block it immediately?'],
      [/freeze\s+my\s+card|temporarily\s+block/i,                             'How do I block my card temporarily?'],
      // Card declining
      [/card\s+(keeps?\s+)?declin|card\s+(keeps?\s+)?failing|card\s+rejected|card\s+not\s+working/i, 'Why was my card declined even though I have sufficient balance?'],
      // ATM
      [/atm\s+(debit|debited|charged)\s+(but\s+)?no\s+cash|no\s+cash\s+(from\s+)?atm|atm\s+dispense/i, 'The ATM did not dispense cash but my account was debited.'],
      // Transfer issues
      [/transfer\s+(was\s+)?debited\s+but|money\s+(sent\s+)?not\s+received|receiver\s+(did\s+not|didn.t)\s+get/i, 'My transfer was debited but the receiver did not get the money.'],
      [/transfer\s+(is\s+)?pending|pending\s+transfer/i,                      'My transfer is showing as pending. What does that mean?'],
      [/sent\s+(money\s+)?to\s+(the\s+)?wrong|wrong\s+(account|transfer)|mistaken\s+transfer/i, 'I sent money to the wrong account. Can it be reversed?'],
      [/debited\s+twice|double\s+debit|charged\s+twice/i,                     'My account was debited twice for one transaction.'],
      // Limits & upgrades
      [/daily\s+transfer\s+limit|what.s\s+my\s+(daily\s+)?limit|what\s+is\s+my\s+(daily\s+)?limit|transfer\s+limit/i, 'What are my daily transfer limits?'],
      [/increase\s+(my\s+)?(transfer\s+)?limit|how\s+(do\s+i\s+)?increase.*limit/i, 'How do I increase my transfer limit?'],
      [/upgrade\s+my\s+account|how\s+(do\s+i\s+)?upgrade|account\s+upgrade|upgrade\s+tier/i, 'How do I upgrade my account tier?'],
      // Scheduling
      [/schedul(e|ing)\s+(a\s+)?transfer|future.dated|future\s+transfer/i,   'Can I schedule a future-dated transfer?'],
      // PIN / password / login
      [/change\s+(my\s+)?card\s+pin|how\s+(to|do\s+i)\s+change.*pin/i,       'How do I change my card PIN?'],
      [/forgot\s+(my\s+)?(app\s+)?password|reset\s+(my\s+)?password|can.t\s+log\s+in/i, 'How do I reset my app password?'],
      [/not\s+receiving\s+otp|otp\s+not\s+(coming|arriving)|no\s+otp/i,      'I am not receiving OTPs.'],
      // Balance & statement
      [/check\s+(my\s+)?balance|what.s\s+my\s+balance|how\s+(do\s+i\s+)?check.*balance/i, 'How do I check my account balance?'],
      [/bank\s+statement|request\s+(a\s+)?statement|download\s+statement/i,   'How do I request a bank statement?'],
      // New card
      [/request\s+(a\s+)?(new\s+)?card|order\s+(a\s+)?card|get\s+(a\s+new\s+)?card/i, 'How do I request a new debit card?'],
      // Fraud / unauthorised
      [/unauthori[sz]ed\s+transaction|fraud(ulent)?\s+transaction|someone\s+used\s+my\s+account/i, 'I noticed an unauthorised transaction on my account.'],
      [/account\s+(been\s+)?hacked|think\s+my\s+account.*hacked|account\s+compromised/i, 'I think my account has been hacked.'],
      // Loan / salary
      [/apply\s+for\s+(a\s+)?loan|get\s+(a\s+)?loan|loan\s+application/i,    'What loan products does Sentinel Bank offer?'],
      [/salary\s+advance|advance\s+(on\s+)?salary/i,                          'How do I apply for an instant salary advance?'],
      // Complaints
      [/file\s+(a\s+)?complaint|make\s+(a\s+)?complaint|how\s+(do\s+i\s+)?complain/i, 'How do I file a formal complaint?'],
    ];

    for (const [pattern, canonical] of QUERY_MAP) {
      if (pattern.test(q)) return canonical;
    }
    return raw; // return original if no mapping matched
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

    if (isConversationalCloser(q)) {
      handleConversationalClose(q);
      return;
    }

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
        const opener = getEmpathyOpener(q);
        const fullText = `${opener}\n\n${cleaned}`;
        // Pass topic for icon rendering
        addMsg({ id: Date.now(), sender: 'ai', type: 'text', text: fullText, topic: q, time: now() });

        setTimeout(() => {
          addMsg({
            id: Date.now() + 1, sender: 'ai', type: 'resolution-check',
            originalQuery: q, time: now(),
          });
        }, 600);
      } else {
        const wordCount = q.trim().split(/\s+/).length;
        const hasVerb = /\b(is|are|was|were|have|has|had|do|does|did|can|could|keep|keeps|want|need|help|fix|check|update|change|why|how|what|when|where|getting|showing|failed|failing|blocked|declined|missing|sent|charged|deducted|reversed|locked|stolen|lost)\b/i.test(q);
        const hasSupportIntent = /\b(card|transfer|atm|account|limit|fraud|pin|balance|loan|statement|charge|debit|credit|transaction|payment|bank|money|fund|wallet|complaint)\b/i.test(q);
        const isTopicLabel = wordCount <= 4 && !hasVerb && hasSupportIntent;
        const isMeaningless = wordCount <= 3 && !hasSupportIntent;

        if (isMeaningless) {
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

  // ─── Customer says "need more help" ─────────────────────────────────────────
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

    // "Did this help?"
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

    // Escalation card
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

    // Routing result
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

    // ── DEFAULT AI TEXT BUBBLE — enhanced FAQ rendering ──────────────────────
    const TopicIcon = getTopicIcon(msg.topic || msg.text);
    const isRichAnswer = msg.text && msg.text.length > 200;

    return (
      <div key={msg.id} className="flex flex-col">
        <div className="flex items-center gap-2 mb-1">
          <div className="w-5 h-5 vault-gradient text-white rounded-full flex items-center justify-center">
            <Bot size={12} />
          </div>
          <span className="text-xs font-bold text-gray-400 dark:text-slate-500">AI Assistant</span>
          {TopicIcon && isRichAnswer && (
            <div className="flex items-center gap-1 px-2 py-0.5 bg-gray-100 dark:bg-white/8 rounded-full">
              <TopicIcon size={10} className="text-vault-cyan" />
            </div>
          )}
        </div>
        <div className="bg-white dark:bg-vault-dark-card rounded-[20px] rounded-tl-none shadow-sm border border-gray-100 dark:border-white/5 max-w-[90%] overflow-hidden">
          {/* Topic header stripe for rich answers */}
          {isRichAnswer && TopicIcon && (
            <div className="flex items-center gap-2 px-4 pt-3.5 pb-2 border-b border-gray-50 dark:border-white/5">
              <div className="w-6 h-6 vault-gradient rounded-lg flex items-center justify-center shrink-0">
                <TopicIcon size={13} className="text-white" />
              </div>
              <span className="text-[11px] font-black text-gray-400 dark:text-slate-500 uppercase tracking-widest">Support Answer</span>
            </div>
          )}
          <div className={`p-4 space-y-2 ${isRichAnswer && TopicIcon ? 'pt-3' : ''}`}>
            {/* Quick metadata chips for rich answers */}
            {isRichAnswer && <QuickInfoBar text={msg.text} />}
            {parseAnswer(msg.text)}
          </div>
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