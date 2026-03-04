import { useState, useRef, useEffect } from 'react';
import { MdChat, MdClose, MdSend, MdSmartToy, MdPerson } from 'react-icons/md';
import axiosInstance from '../api/axiosInstance';

const Chatbot = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    { id: '1', sender: 'ai', text: 'Hello! I am Sentinel AI. How can I assist you with your banking today?', time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMsg = {
      id: Date.now().toString(),
      sender: 'user',
      text: input,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await axiosInstance.post('/ai/chat', { message: userMsg.text });
      setMessages(prev => [...prev, response.data]);
    } catch (error) {
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        sender: 'ai',
        text: "I'm sorry, I'm having trouble connecting to the bank service. Please try again later.",
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
      {/* Chat Window */}
      {isOpen && (
        <div className="mb-4 w-[350px] sm:w-[400px] h-[500px] bg-white rounded-2xl shadow-2xl border border-slate-200 flex flex-col overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-300">
          {/* Header */}
          <div className="p-4 flex items-center justify-between text-white" style={{ background: 'linear-gradient(135deg, #0000ff 0%, #1414ff 100%)' }}>
            <div className="flex items-center gap-3">
              <div className="bg-white/20 p-2 rounded-lg">
                <MdSmartToy size={24} />
              </div>
              <div>
                <h4 className="font-bold text-sm">Sentinel AI</h4>
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
                  <span className="text-[10px] uppercase font-bold tracking-wider opacity-80">Online</span>
                </div>
              </div>
            </div>
            <button onClick={() => setIsOpen(false)} className="hover:bg-white/10 p-1 rounded-md transition-colors">
              <MdClose size={24} />
            </button>
          </div>

          {/* Messages */}
          <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50/50">
            {messages.map((m) => (
              <div key={m.id} className={`flex ${m.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[80%] flex gap-2 ${m.sender === 'user' ? 'flex-row-reverse' : ''}`}>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${m.sender === 'user' ? 'bg-blue-100 text-blue-600' : 'bg-slate-200 text-slate-600'}`}>
                    {m.sender === 'user' ? <MdPerson size={18} /> : <MdSmartToy size={18} />}
                  </div>
                  <div className={`p-3 rounded-2xl text-sm ${
                    m.sender === 'user' 
                      ? 'bg-[#0000ff] text-white rounded-tr-none shadow-md' 
                      : 'bg-white text-slate-700 border border-slate-200 rounded-tl-none shadow-sm'
                  }`}>
                    {/* Render basic markdown-like bolding */}
                    <div dangerouslySetInnerHTML={{ __html: m.text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }} />
                    <p className={`text-[10px] mt-1.5 opacity-60 ${m.sender === 'user' ? 'text-right' : ''}`}>{m.time}</p>
                  </div>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="max-w-[80%] flex gap-2">
                  <div className="w-8 h-8 rounded-full bg-slate-200 text-slate-600 flex items-center justify-center">
                    <MdSmartToy size={18} />
                  </div>
                  <div className="p-3 bg-white border border-slate-200 rounded-2xl rounded-tl-none shadow-sm flex gap-1">
                    <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce"></span>
                    <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce delay-75"></span>
                    <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce delay-150"></span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Input */}
          <form onSubmit={handleSend} className="p-4 border-t border-slate-100 bg-white">
            <div className="relative">
              <input 
                type="text" 
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask Sentinel AI something..."
                className="w-full pl-4 pr-12 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:border-[#0000ff] transition-all"
              />
              <button 
                type="submit" 
                disabled={!input.trim() || isLoading}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-[#0000ff] text-white rounded-lg hover:bg-[#1414ff] disabled:opacity-50 transition-all shadow-md"
              >
                <MdSend size={18} />
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Floating Toggle */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-14 h-14 rounded-full shadow-lg flex items-center justify-center text-white transition-all transform hover:scale-110 active:scale-95 z-50 group overflow-hidden"
        style={{ background: 'linear-gradient(135deg, #0000ff 0%, #1414ff 100%)' }}
      >
        <div className="absolute inset-0 bg-white/20 opacity-0 group-hover:opacity-100 transition-opacity"></div>
        {isOpen ? <MdClose size={28} /> : <MdChat size={28} />}
      </button>
    </div>
  );
};

export default Chatbot;
