import React from 'react';
import { Smartphone, Search, ArrowRight, Users, CheckCircle, Edit2, BrainCircuit } from 'lucide-react';

const AIThoughtProcess = ({ ticket }) => {
  if (!ticket) return null;

  // Normalize: support both real backend tickets and mock tickets
  const ticketId     = ticket.complaint_id || ticket.id || '—';
  const complaintText = ticket.complaint_text || ticket.complaint_narration || ticket.issue || 'No complaint text available.';
  const department   = ticket.department_name || ticket.route || 'Pending AI Routing';
  const deptCode     = ticket.department_code || '';
  const priority     = ticket.priority_level || 'Normal';
  const confVal      = ticket.confidence != null ? ticket.confidence : (ticket.confidence_score != null ? ticket.confidence_score : null);
  const confidence   = confVal != null
    ? (Number(confVal) > 1 ? Number(confVal) : Math.round(Number(confVal) * 100))
    : null;
  const channel      = ticket.complaint_channel || 'App';
  
  const formatDate = (ts) => {
    if (!ts) return '—';
    try {
      return new Date(ts).toLocaleString('en-NG', {
        day: '2-digit', month: 'short', year: 'numeric',
        hour: '2-digit', minute: '2-digit'
      });
    } catch { return ts; }
  };
  const dateStr      = formatDate(ticket.complaint_timestamp || ticket.created_at);
  const slaHours     = ticket.sla_hours || ticket.sla_hours_limit || '—';
  const reasoning    = ticket.reasoning || 'No reasoning provided.';

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden font-sans">

      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50/30">
         <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-red-100 rounded-xl flex items-center justify-center text-[#A01030]">
              <BrainCircuit size={20} />
            </div>
            <div>
              <h3 className="text-sm font-bold text-gray-900">
                AI Thought Process: {ticketId}
              </h3>
              <p className="text-xs text-gray-500">Processing live resolution routing...</p>
            </div>
         </div>
         <div className="flex gap-2">
           <span className="px-2 py-1 bg-green-100 text-green-700 text-[10px] font-bold rounded uppercase flex items-center gap-1.5 border border-green-200">
             <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></span> Live
           </span>
           {confidence != null && (
             <span className="px-2 py-1 bg-gray-100 text-gray-600 text-[10px] font-bold rounded uppercase border border-gray-200">
               Confidence: {confidence}%
             </span>
           )}
         </div>
      </div>

      {/* Steps */}
      <div className="p-8 relative">
         {/* Vertical line */}
         <div className="absolute left-[59px] top-12 bottom-20 w-0.5 bg-gradient-to-b from-[#A01030] to-gray-200 z-0"></div>

         {/* Step 1: Input */}
         <div className="flex gap-6 mb-8 relative z-10">
            <div className="w-10 h-10 rounded-full bg-white border-2 border-[#A01030] flex items-center justify-center text-[#A01030] shadow-sm shrink-0">
              <Smartphone size={18} />
            </div>
            <div className="flex-1">
              <h4 className="text-sm font-bold text-gray-900 mb-2">Step 1: Input Received</h4>
              <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
                <p className="text-sm text-gray-700 font-medium mb-3 leading-relaxed">
                  "{complaintText}"
                </p>
                <div className="flex flex-wrap gap-2">
                  <span className="px-2.5 py-1 bg-gray-100 text-gray-500 text-[10px] font-bold rounded uppercase border border-gray-200">
                    Channel: {channel}
                  </span>
                  <span className="px-2.5 py-1 bg-gray-100 text-gray-500 text-[10px] font-bold rounded uppercase border border-gray-200">
                    Priority: {priority}
                  </span>
                  {confidence != null && (
                    <span className="px-2.5 py-1 bg-gray-100 text-gray-500 text-[10px] font-bold rounded uppercase border border-gray-200">
                      Confidence: {confidence}%
                    </span>
                  )}
                  <span className="px-2.5 py-1 bg-gray-100 text-gray-500 text-[10px] font-bold rounded uppercase border border-gray-200">
                    Date: {dateStr}
                  </span>
                  <span className="px-2.5 py-1 bg-gray-100 text-gray-500 text-[10px] font-bold rounded uppercase border border-gray-200">
                    SLA: {slaHours} hrs
                  </span>
                </div>
              </div>
            </div>
         </div>

         {/* Step 2: Intent Detected */}
         <div className="flex gap-6 mb-8 relative z-10">
            <div className="w-10 h-10 rounded-full bg-white border-2 border-[#A01030] flex items-center justify-center text-[#A01030] shadow-sm shrink-0">
              <Search size={18} />
            </div>
            <div className="flex-1">
              <h4 className="text-sm font-bold text-gray-900 mb-2">Step 2: Intent Detected</h4>
              <div className="bg-red-50 border border-red-100 rounded-xl p-5 flex flex-col gap-3 shadow-sm">
                <div className="flex justify-between items-start">
                  <div>
                    <span className="text-sm font-bold text-[#A01030] block mb-1">
                      {department} {confidence != null ? `(${confidence}% confidence)` : ''}
                    </span>
                  </div>
                  <span className="px-2 py-1 bg-white/60 text-[#A01030] text-[10px] font-bold rounded border border-red-200 uppercase shrink-0">
                    AI-ROUTED
                  </span>
                </div>
                {/* AI Reasoning block */}
                <div className="bg-white/60 border border-red-200/50 rounded-lg p-3">
                  <p className="text-xs font-bold text-[#A01030] mb-1">AI Reasoning</p>
                  <p className="text-xs text-gray-700 leading-relaxed">
                    {reasoning}
                  </p>
                </div>
              </div>
            </div>
         </div>

         {/* Step 3: Route Selected */}
         <div className="flex gap-6 relative z-10">
            <div className="w-10 h-10 rounded-full bg-[#A01030] flex items-center justify-center text-white shadow-sm shrink-0">
              <ArrowRight size={18} />
            </div>
            <div className="flex-1">
              <h4 className="text-sm font-bold text-gray-900 mb-2">Step 3: Route Selected</h4>
              <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm flex flex-col gap-1">
                <div className="flex items-center gap-2">
                   <Users size={16} className="text-gray-400"/>
                   <span className="text-sm font-bold text-gray-900">{department}</span>
                   {deptCode && <span className="text-xs text-gray-400 font-mono">({deptCode})</span>}
                </div>
                <p className="text-xs text-gray-500 pl-6">
                  Priority: {priority} • Routed via Sentinel AI Dispatcher Agent
                </p>
              </div>
            </div>
         </div>
      </div>

      {/* Footer Actions */}
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