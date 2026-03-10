import React from 'react';
import { Smartphone, Search, ArrowRight, Users, CheckCircle, Edit2, BrainCircuit } from 'lucide-react';

const AIThoughtProcess = ({ ticket }) => {
  
  const isDefault = !ticket || ticket.id === '#49202';

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden font-sans">
      
      {}
      <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50/30">
         <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-red-100 rounded-xl flex items-center justify-center text-[#A01030]">
              <BrainCircuit size={20} />
            </div>
            <div>
              <h3 className="text-sm font-bold text-gray-900">
                AI Thought Process: Ticket {ticket?.id || '#49202'}
              </h3>
              <p className="text-xs text-gray-500">Processing live resolution routing...</p>
            </div>
         </div>
         <div className="flex gap-2">
           <span className="px-2 py-1 bg-green-100 text-green-700 text-[10px] font-bold rounded uppercase flex items-center gap-1.5 border border-green-200">
             <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></span> Live
           </span>
           <span className="px-2 py-1 bg-gray-100 text-gray-600 text-[10px] font-bold rounded uppercase border border-gray-200">
             Confidence: {ticket?.confidence || 98.4}%
           </span>
         </div>
      </div>

      {}
      <div className="p-8 relative">
         {}
         <div className="absolute left-[59px] top-12 bottom-20 w-0.5 bg-gradient-to-b from-[#A01030] to-gray-200 z-0"></div>

         {}
         <div className="flex gap-6 mb-8 relative z-10">
            <div className="w-10 h-10 rounded-full bg-white border-2 border-[#A01030] flex items-center justify-center text-[#A01030] shadow-sm shrink-0">
              <Smartphone size={18} />
            </div>
            <div className="flex-1">
              <h4 className="text-sm font-bold text-gray-900 mb-2">Step 1: Input Received</h4>
              <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
                <p className="text-sm text-gray-700 font-medium mb-3 leading-relaxed">
                  "{ticket?.issue || "My card was charged NGN 50,000 at a Zenith Bank ATM but no cash was dispensed. Please revert immediately."}"
                </p>
                <div className="flex gap-2">
                  <span className="px-2.5 py-1 bg-gray-100 text-gray-500 text-[10px] font-bold rounded uppercase border border-gray-200">
                    CATEGORY: COMPLAINT
                  </span>
                  <span className="px-2.5 py-1 bg-gray-100 text-gray-500 text-[10px] font-bold rounded uppercase border border-gray-200">
                    LANGUAGE: ENGLISH
                  </span>
                </div>
              </div>
            </div>
         </div>

         {}
         <div className="flex gap-6 mb-8 relative z-10">
            <div className="w-10 h-10 rounded-full bg-white border-2 border-[#A01030] flex items-center justify-center text-[#A01030] shadow-sm shrink-0">
              <Search size={18} />
            </div>
            <div className="flex-1">
              <h4 className="text-sm font-bold text-gray-900 mb-2">Step 2: Intent Detected</h4>
              <div className="bg-red-50 border border-red-100 rounded-xl p-5 flex justify-between items-start shadow-sm">
                <div>
                  <span className="text-sm font-bold text-[#A01030] block mb-1">
                    Dispense Error (98% confidence)
                  </span>
                  <p className="text-xs text-gray-500">
                    Cross-referenced with Transaction ID: #TXN_982348. Status: Pending Reversal.
                  </p>
                </div>
                <span className="px-2 py-1 bg-white/60 text-[#A01030] text-[10px] font-bold rounded border border-red-200 uppercase">
                  AUTO-TAGGED
                </span>
              </div>
            </div>
         </div>

         {}
         <div className="flex gap-6 relative z-10">
            <div className="w-10 h-10 rounded-full bg-[#A01030] flex items-center justify-center text-white shadow-sm shrink-0">
              <ArrowRight size={18} />
            </div>
            <div className="flex-1">
              <h4 className="text-sm font-bold text-gray-900 mb-2">Step 3: Route Selected</h4>
              <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm flex flex-col gap-1">
                <div className="flex items-center gap-2">
                   <Users size={16} className="text-gray-400"/>
                   <span className="text-sm font-bold text-gray-900">Reconciliation Team (Tier 2)</span>
                </div>
                <p className="text-xs text-gray-500 pl-6">
                  SLA target: 4 hours. Escalated due to high-value transaction (NGN 50k+).
                </p>
              </div>
            </div>
         </div>
      </div>

      {}
      <div className="px-6 py-4 border-t border-gray-100 bg-gray-50 flex justify-end gap-3">
        <button className="px-4 py-2 flex items-center gap-1.5 bg-white border border-red-200 text-[#A01030] rounded-lg text-xs font-bold hover:bg-red-50 transition-colors">
           <Edit2 size={14} /> Override Manually
        </button>
        <button className="px-4 py-2 bg-[#A01030] text-white rounded-lg text-xs font-bold hover:bg-[#850d28] transition-colors shadow-md shadow-red-900/10 flex items-center gap-2">
           <CheckCircle size={14} /> Approve Routing
        </button>
      </div>
    </div>
  );
};

export default AIThoughtProcess;