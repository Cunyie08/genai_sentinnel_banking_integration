// import React, { useState, useRef, useEffect } from 'react';
// import { useDispatch, useSelector } from 'react-redux';
// import { ChevronLeft, Mic, Send, Bot, ChevronRight, AlertTriangle, CheckCircle, Paperclip } from 'lucide-react';
// import { setRoute } from '../features/uiSlice';
// import { addChatMessage, createTicket } from '../features/aiSlice';

// const ChatScreen = () => {
//   const dispatch = useDispatch();
//   const chatHistory = useSelector(state => state.ai.chatHistory);
//   const [input, setInput] = useState('');
//   const [isTyping, setIsTyping] = useState(false);
//   const scrollRef = useRef(null);

//   // Auto-scroll
//   useEffect(() => {
//     if (scrollRef.current) {
//       scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
//     }
//   }, [chatHistory, isTyping]);

//   const handleSend = () => {
//     if (!input.trim()) return;
    
//     // 1. Add User Message
//     const userMsg = { 
//       id: Date.now(), 
//       sender: 'user', 
//       type: 'text', 
//       text: input,
//       time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) 
//     };
//     dispatch(addChatMessage(userMsg));
//     setInput('');
//     setIsTyping(true);

//     // 2. Simulate AI Reply
//     setTimeout(() => {
//         setIsTyping(false);
//         const aiMsg = { 
//             id: Date.now() + 1, 
//             sender: 'ai', 
//             type: 'text', 
//             text: "I'm checking that for you right now...", 
//             time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) 
//         };
//         dispatch(addChatMessage(aiMsg));
//     }, 1500);
//   };

//   const handleEscalate = () => {
//     setIsTyping(true);
//     setTimeout(() => {
//       const newTicket = { id: `TKT-${Math.floor(Math.random() * 10000)}`, user: 'User', issue: 'Billing', time: new Date().toLocaleTimeString() };
//       dispatch(createTicket(newTicket));
      
//       dispatch(addChatMessage({ 
//         id: Date.now(), 
//         sender: 'ai', 
//         type: 'success', 
//         text: `Ticket #${newTicket.id} created. Refund initiated.`, 
//         time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) 
//       }));
//       setIsTyping(false);
//     }, 1500);
//   };

//   return (
//     <div className="flex flex-col h-full bg-[#F9FAFB]">
      
//       {/* --- HEADER --- */}
//       <div className="bg-white px-4 py-4 flex items-center justify-between border-b border-gray-100 shadow-sm shrink-0 z-20">
//         <div className="flex items-center gap-3">
//           <button onClick={() => dispatch(setRoute('home'))} className="text-gray-600 hover:bg-gray-50 p-1 rounded-full">
//             <ChevronLeft size={26} />
//           </button>
//           <div>
//             <h2 className="font-extrabold text-gray-900 text-lg leading-tight">AI Support</h2>
//             <div className="flex items-center gap-1.5">
//               <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
//               <p className="text-[10px] text-gray-500 uppercase font-bold tracking-wide">Always Active</p>
//             </div>
//           </div>
//         </div>
//         <div className="w-10 h-10 rounded-full bg-red-50 border border-gray-100 flex items-center justify-center">
//            <Bot size={20} className="text-[#A01030]" />
//         </div>
//       </div>

//       {/* --- MESSAGES AREA (Scrollable) --- */}
//       <div className="flex-1 overflow-y-auto p-4 space-y-6" ref={scrollRef}>
//         {chatHistory.map((msg) => (
//           <div key={msg.id} className="flex flex-col animate-in slide-in-from-bottom-2 fade-in duration-300">
            
//             {/* AI Avatar Label */}
//             {msg.sender === 'ai' && (
//               <div className="flex items-center gap-2 mb-2">
//                 <div className="w-6 h-6 bg-red-100 text-[#A01030] rounded-full flex items-center justify-center">
//                   <span className="text-[10px] font-bold">AI</span>
//                 </div>
//                 <span className="text-xs font-bold text-gray-400">Assistant</span>
//               </div>
//             )}

//             {/* MESSAGE TYPES */}
//             {msg.type === 'options' && (
//               <div className="bg-white p-5 rounded-[20px] rounded-tl-none shadow-sm border border-gray-100 max-w-[95%]">
//                 <p className="text-[15px] font-medium text-gray-800 mb-4 leading-relaxed">{msg.text}</p>
//                 <div className="space-y-3">
//                   {msg.options.map((opt, i) => (
//                     <button key={i} onClick={() => { setInput(opt); handleSend(); }} className="w-full flex justify-between items-center p-3.5 border border-red-100 rounded-xl text-[13px] text-[#A01030] font-bold bg-white hover:bg-red-50 transition-colors shadow-sm text-left">
//                       {opt} <ChevronRight size={16} className="text-[#A01030]"/>
//                     </button>
//                   ))}
//                 </div>
//               </div>
//             )}

//             {msg.type === 'escalation' && (
//               <div className="bg-white rounded-[20px] rounded-tl-none shadow-sm border border-gray-100 max-w-[95%] overflow-hidden">
//                 <div className="bg-[#A01030] px-4 py-2 flex items-center gap-2">
//                     <AlertTriangle size={14} className="text-white"/>
//                     <span className="text-[10px] font-black text-white uppercase tracking-widest">{msg.title}</span>
//                 </div>
//                 <div className="p-5">
//                   <p className="text-[14px] font-medium text-gray-800 leading-relaxed mb-4">
//                      I've identified two identical transactions to <span className="font-bold">PHCN Utility</span>. Would you like to escalate this?
//                   </p>
//                   <div className="flex gap-3">
//                       <button onClick={handleEscalate} className="flex-1 bg-[#A01030] text-white py-3 rounded-full font-bold text-xs shadow-md shadow-red-200 active:scale-95 transition-transform">{msg.routeTo}</button>
//                       <button onClick={() => dispatch(addChatMessage({id: Date.now(), sender:'ai', text: 'Cancelled.'}))} className="flex-1 bg-white border border-gray-200 text-gray-500 py-3 rounded-full font-bold text-xs">Cancel</button>
//                   </div>
//                 </div>
//               </div>
//             )}

//             {msg.sender === 'user' && (
//               <div className="self-end max-w-[85%] bg-[#A01030] text-white p-4 rounded-[20px] rounded-tr-none shadow-md text-[14px] leading-relaxed font-medium">
//                 {msg.text}
//               </div>
//             )}

//             {msg.type === 'success' && (
//               <div className="bg-green-50 p-4 rounded-[20px] rounded-tl-none border border-green-100 max-w-[90%] flex gap-3 items-start">
//                 <CheckCircle size={20} className="text-green-600 mt-0.5 shrink-0" />
//                 <div><p className="text-[14px] font-bold text-green-800 mb-1">Success</p><p className="text-[13px] text-green-700 leading-relaxed">{msg.text}</p></div>
//               </div>
//             )}

//             {msg.sender === 'ai' && msg.type === 'text' && (
//               <div className="bg-white p-4 rounded-[20px] rounded-tl-none shadow-sm border border-gray-100 max-w-[90%] text-[14px] font-medium text-gray-800">
//                 {msg.text}
//               </div>
//             )}
//           </div>
//         ))}
        
//         {isTyping && (
//            <div className="bg-white p-4 rounded-[20px] rounded-tl-none shadow-sm border border-gray-100 w-16">
//              <div className="flex gap-1 justify-center">
//                <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"></div>
//                <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce delay-100"></div>
//                <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce delay-200"></div>
//              </div>
//            </div>
//         )}
//       </div>

//       {/* --- FOOTER INPUT (Fixed at Bottom) --- */}
//       <div className="bg-white pt-2 pb-6 px-4 border-t border-gray-50 shrink-0 z-30">
        
//         {/* Quick Chips */}
//         <div className="flex gap-2 overflow-x-auto hide-scrollbar mb-3">
//           {['Check balance', 'Account statement', 'History'].map((chip, i) => (
//             <button key={i} onClick={() => setInput(chip)} className="whitespace-nowrap px-4 py-2 bg-gray-50 border border-gray-100 rounded-full text-xs font-bold text-gray-600 hover:bg-gray-100 transition-colors">
//               {chip}
//             </button>
//           ))}
//         </div>

//         {/* Input Field */}
//         <div className="flex items-center gap-2">
//           <button className="p-3 bg-gray-50 rounded-full text-gray-400 hover:bg-gray-100 transition-colors">
//             <Mic size={20} />
//           </button>
          
//           <div className="flex-1 bg-gray-50 h-12 rounded-full px-5 flex items-center border border-transparent focus-within:border-[#A01030]/20 focus-within:ring-2 focus-within:ring-[#A01030]/10 transition-all">
//             <input 
//               type="text" 
//               value={input} 
//               onChange={e => setInput(e.target.value)} 
//               onKeyDown={e => e.key === 'Enter' && handleSend()} 
//               placeholder="Type your complaint..." 
//               className="flex-1 bg-transparent outline-none text-sm font-medium text-gray-900 placeholder:text-gray-400"
//             />
//             <button className="ml-2 text-gray-400 hover:text-gray-600"><Paperclip size={18}/></button>
//           </div>

//           <button 
//             onClick={handleSend}
//             className="w-12 h-12 bg-[#A01030] rounded-full flex items-center justify-center text-white shadow-lg shadow-red-900/20 active:scale-95 transition-transform"
//           >
//             <Send size={18} className="ml-0.5" />
//           </button>
//         </div>
//       </div>

//     </div>
//   );
// };
// export default ChatScreen;








import React, { useState, useRef, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { ChevronLeft, Mic, Send, Bot, ChevronRight, AlertTriangle, CheckCircle, Paperclip } from 'lucide-react';
import { setRoute } from '../features/uiSlice';
import { addChatMessage, sendMessage, createTicket } from '../features/aiSlice';

const ChatScreen = () => {
  const dispatch = useDispatch();
  const { chatHistory, isLoading } = useSelector(state => state.ai);
  const [input, setInput] = useState('');
  const scrollRef = useRef(null);

  // Auto-scroll to bottom on new message
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [chatHistory, isLoading]);

  const handleSend = () => {
    if (!input.trim()) return;
    
    // 1. Add User Message
    const userMsg = { 
      id: Date.now(), 
      sender: 'user', 
      type: 'text', 
      text: input,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) 
    };
    dispatch(addChatMessage(userMsg));
    
    // 2. Trigger AI Response
    dispatch(sendMessage(input));
    setInput('');
  };

  const handleEscalate = () => {
    const newTicket = { id: `TKT-${Math.floor(Math.random() * 10000)}`, user: 'User', issue: 'Billing', time: new Date().toLocaleTimeString() };
    dispatch(createTicket(newTicket));
    
    dispatch(addChatMessage({ 
      id: Date.now(), 
      sender: 'ai', 
      type: 'success', 
      text: `Ticket #${newTicket.id} created. Refund initiated.`, 
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) 
    }));
  };

  return (
    <div className="flex flex-col h-full bg-[#F9FAFB] relative">
      
      {/* --- HEADER --- */}
      <div className="bg-white px-4 py-4 flex items-center justify-between border-b border-gray-100 shadow-sm shrink-0 z-20">
        <div className="flex items-center gap-3">
          <button onClick={() => dispatch(setRoute('home'))} className="text-gray-600 hover:bg-gray-50 p-1 rounded-full">
            <ChevronLeft size={26} />
          </button>
          <div>
            <h2 className="font-extrabold text-gray-900 text-lg leading-tight">AI Support</h2>
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <p className="text-[10px] text-gray-500 uppercase font-bold tracking-wide">Always Active</p>
            </div>
          </div>
        </div>
        <div className="w-10 h-10 rounded-full bg-red-50 border border-gray-100 flex items-center justify-center">
           <Bot size={20} className="text-[#A01030]" />
        </div>
      </div>

      {/* --- MESSAGES AREA --- */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6" ref={scrollRef}>
        {chatHistory.map((msg) => (
          <div key={msg.id} className="flex flex-col animate-in slide-in-from-bottom-2 fade-in duration-300">
            
            {/* Sender Label for AI */}
            {msg.sender === 'ai' && (
              <div className="flex items-center gap-2 mb-2">
                <div className="w-6 h-6 bg-red-100 text-[#A01030] rounded-full flex items-center justify-center">
                  <span className="text-[10px] font-bold">AI</span>
                </div>
                <span className="text-xs font-bold text-gray-400">Assistant</span>
              </div>
            )}

            {/* TYPE: OPTIONS (Buttons) */}
            {msg.type === 'options' && (
              <div className="bg-white p-5 rounded-[20px] rounded-tl-none shadow-sm border border-gray-100 max-w-[95%]">
                <p className="text-[15px] font-medium text-gray-800 mb-4 leading-relaxed">{msg.text}</p>
                <div className="space-y-3">
                  {msg.options.map((opt, i) => (
                    <button key={i} onClick={() => { setInput(opt); handleSend(); }} className="w-full flex justify-between items-center p-3.5 border border-red-100 rounded-xl text-[13px] text-[#A01030] font-bold bg-white hover:bg-red-50 transition-colors shadow-sm text-left">
                      {opt} <ChevronRight size={16} className="text-[#A01030]"/>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* TYPE: ESCALATION (Action Card) */}
            {msg.type === 'escalation' && (
              <div className="bg-white rounded-[20px] rounded-tl-none shadow-sm border border-gray-100 max-w-[95%] overflow-hidden">
                <div className="bg-[#A01030] px-4 py-2 flex items-center gap-2">
                    <AlertTriangle size={14} className="text-white"/>
                    <span className="text-[10px] font-black text-white uppercase tracking-widest">{msg.title}</span>
                </div>
                <div className="p-5">
                  <p className="text-[14px] font-medium text-gray-800 leading-relaxed mb-4">
                     {msg.text}
                  </p>
                  <div className="flex gap-3">
                      <button onClick={handleEscalate} className="flex-1 bg-[#A01030] text-white py-3 rounded-full font-bold text-xs shadow-md shadow-red-200 active:scale-95 transition-transform">{msg.routeTo}</button>
                      <button onClick={() => dispatch(addChatMessage({id: Date.now(), sender:'ai', text: 'Cancelled.'}))} className="flex-1 bg-white border border-gray-200 text-gray-500 py-3 rounded-full font-bold text-xs">Cancel</button>
                  </div>
                </div>
              </div>
            )}

            {/* TYPE: SUCCESS (Green Box) */}
            {msg.type === 'success' && (
              <div className="bg-green-50 p-4 rounded-[20px] rounded-tl-none border border-green-100 max-w-[90%] flex gap-3 items-start">
                <CheckCircle size={20} className="text-green-600 mt-0.5 shrink-0" />
                <div><p className="text-[14px] font-bold text-green-800 mb-1">Success</p><p className="text-[13px] text-green-700 leading-relaxed">{msg.text}</p></div>
              </div>
            )}

            {/* TYPE: USER TEXT */}
            {msg.sender === 'user' && (
              <div className="self-end max-w-[85%] bg-[#A01030] text-white p-4 rounded-[20px] rounded-tr-none shadow-md text-[14px] leading-relaxed font-medium">
                {msg.text}
              </div>
            )}

            {/* TYPE: NORMAL AI TEXT */}
            {msg.sender === 'ai' && (!msg.type || msg.type === 'text') && (
              <div className="bg-white p-4 rounded-[20px] rounded-tl-none shadow-sm border border-gray-100 max-w-[90%] text-[14px] font-medium text-gray-800">
                {msg.text}
              </div>
            )}
          </div>
        ))}
        
        {/* Typing Indicator */}
        {isLoading && (
           <div className="bg-white p-4 rounded-[20px] rounded-tl-none shadow-sm border border-gray-100 w-16 animate-in slide-in-from-bottom-1 fade-in">
             <div className="flex gap-1 justify-center">
               <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"></div>
               <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce delay-100"></div>
               <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce delay-200"></div>
             </div>
           </div>
        )}
      </div>

      {/* --- FOOTER INPUT --- */}
      <div className="bg-white pt-2 pb-6 px-4 border-t border-gray-50 shrink-0 z-30">
        <div className="flex gap-2 overflow-x-auto hide-scrollbar mb-3">
          {['Check balance', 'Account statement', 'History'].map((chip, i) => (
            <button key={i} onClick={() => setInput(chip)} className="whitespace-nowrap px-4 py-2 bg-gray-50 border border-gray-100 rounded-full text-xs font-bold text-gray-600 hover:bg-gray-100 transition-colors">
              {chip}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <button className="p-3 bg-gray-50 rounded-full text-gray-400 hover:bg-gray-100 transition-colors">
            <Mic size={20} />
          </button>
          
          <div className="flex-1 bg-gray-50 h-12 rounded-full px-5 flex items-center border border-transparent focus-within:border-[#A01030]/20 focus-within:ring-2 focus-within:ring-[#A01030]/10 transition-all">
            <input 
              type="text" 
              value={input} 
              onChange={e => setInput(e.target.value)} 
              onKeyDown={e => e.key === 'Enter' && handleSend()} 
              placeholder="Type your complaint..." 
              className="flex-1 bg-transparent outline-none text-sm font-medium text-gray-900 placeholder:text-gray-400"
            />
            <button className="ml-2 text-gray-400 hover:text-gray-600"><Paperclip size={18}/></button>
          </div>

          <button 
            onClick={handleSend}
            disabled={isLoading || !input.trim()}
            className="w-12 h-12 bg-[#A01030] rounded-full flex items-center justify-center text-white shadow-lg shadow-red-900/20 active:scale-95 transition-transform disabled:opacity-70 disabled:active:scale-100"
          >
            <Send size={18} className="ml-0.5" />
          </button>
        </div>
      </div>

    </div>
  );
};
export default ChatScreen;