import React, { useState, useMemo } from 'react';
import AIThoughtProcess from '../AIThoughtProcess';
import { Filter, Loader2, RefreshCw, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react';

const ComplaintsModule = ({ tickets = [], stats, loading, error, onRefresh }) => {
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [selectedDept, setSelectedDept]     = useState('All Departments');
  const [expandedRow, setExpandedRow]       = useState(null);

  const departments = useMemo(() => {
    if (!tickets.length) return ['All Departments'];
    const deptSet = new Set();
    tickets.forEach(t => {
      if (t.department_name) deptSet.add(t.department_name);
    });
    const sorted = [...deptSet].sort();
    return ['All Departments', ...sorted];
  }, [tickets]);

  const filteredTickets = useMemo(() => {
    if (selectedDept === 'All Departments') return tickets;
    return tickets.filter(t => t.department_name === selectedDept);
  }, [tickets, selectedDept]);

  React.useEffect(() => {
    if (filteredTickets.length > 0 && !selectedTicket) {
      setSelectedTicket(filteredTickets[0]);
    }
  }, [filteredTickets, selectedTicket]);

  const getPriorityStyle = (level) => {
    const p = (level || '').toLowerCase();
    if (p === 'high' || p === 'critical')  return 'bg-red-100 dark:bg-red-500/10 text-red-700 dark:text-red-400 border-red-200 dark:border-red-500/20';
    if (p === 'medium')                     return 'bg-orange-100 dark:bg-orange-500/10 text-orange-700 dark:text-orange-400 border-orange-200 dark:border-orange-500/20';
    if (p === 'low')                        return 'bg-green-100 dark:bg-green-500/10 text-green-700 dark:text-green-400 border-green-200 dark:border-green-500/20';
    return 'bg-gray-100 dark:bg-white/5 text-gray-600 dark:text-slate-400 border-gray-200 dark:border-white/10';
  };

  const getStatusStyle = (status) => {
    const s = (status || '').toLowerCase();
    if (s === 'open')        return 'bg-yellow-50 dark:bg-yellow-500/10 text-yellow-700 dark:text-yellow-400 border-yellow-200 dark:border-yellow-500/20';
    if (s === 'resolved')    return 'bg-green-50 dark:bg-green-500/10 text-green-700 dark:text-green-400 border-green-200 dark:border-green-500/20';
    if (s === 'in_progress') return 'bg-blue-50 dark:bg-blue-500/10 text-blue-700 dark:text-blue-400 border-blue-200 dark:border-blue-500/20';
    if (s === 'escalated')   return 'bg-red-50 dark:bg-red-500/10 text-red-700 dark:text-red-400 border-red-200 dark:border-red-500/20';
    return 'bg-gray-50 dark:bg-white/5 text-gray-600 dark:text-slate-400 border-gray-200 dark:border-white/10';
  };

  const formatDate = (ts) => {
    if (!ts) return '—';
    try {
      return new Date(ts).toLocaleString('en-NG', {
        day: '2-digit', month: 'short', year: 'numeric',
        hour: '2-digit', minute: '2-digit'
      });
    } catch { return ts; }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {selectedTicket && <AIThoughtProcess ticket={selectedTicket} />}

      <div className="flex flex-wrap justify-between items-center gap-4">
        <div className="flex items-center gap-3">
          <h3 className="text-lg font-bold text-gray-900 dark:text-white">Complaints Queue</h3>
          <span className="text-xs font-bold text-vault-cyan bg-cyan-50 dark:bg-vault-cyan/10 px-2.5 py-1 rounded-full border border-cyan-100 dark:border-vault-cyan/20">
            {filteredTickets.length} of {tickets.length}
          </span>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={onRefresh}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-2 bg-white dark:bg-vault-dark-card border border-gray-200 dark:border-white/5 rounded-xl text-xs font-bold text-gray-600 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-white/5 active:scale-95 transition-all shadow-sm disabled:opacity-50"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh
          </button>

          <div className="relative flex items-center gap-2 bg-white dark:bg-vault-dark-card border border-gray-200 dark:border-white/5 rounded-xl px-3 py-2 shadow-sm">
            <Filter size={14} className="text-gray-400 dark:text-slate-500 shrink-0" />
            <select
              value={selectedDept}
              onChange={(e) => setSelectedDept(e.target.value)}
              className="bg-transparent text-sm font-bold text-gray-700 dark:text-white outline-none cursor-pointer pr-6 appearance-none min-w-[140px]"
            >
              {departments.map(dept => (
                <option key={dept} value={dept}>{dept}</option>
              ))}
            </select>
            <ChevronDown size={14} className="text-gray-400 dark:text-slate-500 absolute right-3 pointer-events-none" />
          </div>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-3 bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 rounded-xl p-4">
          <AlertCircle size={20} className="text-red-500 dark:text-red-400 shrink-0" />
          <div className="flex-1">
            <p className="text-sm font-bold text-red-700 dark:text-red-400">Failed to load complaints</p>
            <p className="text-xs text-red-500 dark:text-red-400/70 mt-0.5">{error}</p>
          </div>
          <button onClick={onRefresh} className="px-3 py-1.5 vault-gradient text-white text-xs font-bold rounded-lg active:scale-95 transition-all">
            Retry
          </button>
        </div>
      )}

      <div className="bg-white dark:bg-vault-dark-card border border-gray-200 dark:border-white/5 rounded-xl overflow-hidden shadow-sm">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 text-gray-400 dark:text-slate-500 gap-3">
            <Loader2 size={32} className="animate-spin text-vault-cyan" />
            <span className="text-sm font-bold">Loading complaints from database...</span>
          </div>
        ) : filteredTickets.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-gray-400 dark:text-slate-500 gap-2">
            <p className="text-sm font-bold">
              {tickets.length === 0
                ? 'No complaints recorded in the database yet.'
                : `No complaints found for "${selectedDept}".`}
            </p>
            {tickets.length === 0 && (
              <p className="text-xs text-gray-400 dark:text-slate-500">Complaints made by users will appear here automatically.</p>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-gray-50 dark:bg-white/5 border-b border-gray-200 dark:border-white/5">
                <tr>
                  <th className="px-4 py-3 text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider">Complaint ID</th>
                  <th className="px-4 py-3 text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider">Customer</th>
                  <th className="px-4 py-3 text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider">Department</th>
                  <th className="px-4 py-3 text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider">Priority</th>
                  <th className="px-4 py-3 text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider">Confidence</th>
                  <th className="px-4 py-3 text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider">Date</th>
                  <th className="px-4 py-3 text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider text-center">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50 dark:divide-white/5">
                {filteredTickets.map((t) => {
                  const confVal = t.confidence != null ? t.confidence : (t.confidence_score != null ? t.confidence_score : null);
                  const confidence = confVal != null ? (Number(confVal) > 1 ? Number(confVal) : Math.round(Number(confVal) * 100)) : null;
                  const isExpanded = expandedRow === t.complaint_id;

                  return (
                    <React.Fragment key={t.complaint_id}>
                      <tr
                        onClick={() => setSelectedTicket(t)}
                        className={`cursor-pointer transition-colors ${
                          selectedTicket?.complaint_id === t.complaint_id ? 'bg-cyan-50/60 dark:bg-vault-cyan/5' : 'hover:bg-gray-50/70 dark:hover:bg-white/5'
                        }`}
                      >
                        <td className="px-4 py-3.5 text-xs font-mono font-bold text-gray-800 dark:text-white whitespace-nowrap">
                          {t.complaint_id}
                        </td>
                        <td className="px-4 py-3.5 text-xs text-gray-600 dark:text-slate-400 max-w-[120px] truncate" title={t.customer_id}>
                          {t.customer_id}
                        </td>
                        <td className="px-4 py-3.5">
                          <span className="inline-flex items-center gap-1.5 text-xs font-bold text-gray-800 dark:text-white">
                            <span className="w-2 h-2 rounded-full bg-vault-cyan shrink-0"></span>
                            {t.department_name || 'Pending'}
                          </span>
                          {t.department_code && (
                            <span className="ml-1.5 text-[10px] text-gray-400 dark:text-slate-500 font-mono">({t.department_code})</span>
                          )}
                        </td>
                        <td className="px-4 py-3.5">
                          <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold uppercase border ${getPriorityStyle(t.priority_level)}`}>
                            {t.priority_level || '—'}
                          </span>
                        </td>
                        <td className="px-4 py-3.5 w-32">
                          {confidence != null ? (
                            <div className="flex items-center gap-2">
                              <div className="flex-1 h-1.5 bg-gray-100 dark:bg-white/10 rounded-full overflow-hidden">
                                <div
                                  className={`h-full rounded-full transition-all ${
                                    confidence >= 90 ? 'bg-green-500' : confidence >= 70 ? 'bg-yellow-500' : 'bg-red-500'
                                  }`}
                                  style={{ width: `${Math.min(confidence, 100)}%` }}
                                />
                              </div>
                              <span className="text-[11px] font-bold text-gray-600 dark:text-slate-300 w-8 text-right">{confidence}%</span>
                            </div>
                          ) : (
                            <span className="text-xs text-gray-300 dark:text-slate-600">—</span>
                          )}
                        </td>
                        <td className="px-4 py-3.5 text-[11px] text-gray-500 dark:text-slate-400 whitespace-nowrap">
                          {formatDate(t.complaint_timestamp || t.created_at)}
                        </td>
                        <td className="px-4 py-3.5 text-center">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setExpandedRow(isExpanded ? null : t.complaint_id);
                              setSelectedTicket(t);
                            }}
                            className="text-vault-cyan hover:bg-cyan-50 dark:hover:bg-vault-cyan/10 p-1.5 rounded-lg transition-colors"
                          >
                            {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                          </button>
                        </td>
                      </tr>

                      {isExpanded && (
                        <tr className="bg-gray-50/80 dark:bg-white/5">
                          <td colSpan={8} className="px-6 py-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl">
                              <div className="bg-white dark:bg-vault-dark-card rounded-xl p-4 border border-gray-100 dark:border-white/5">
                                <p className="text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider mb-2">Complaint Text</p>
                                <p className="text-sm text-gray-800 dark:text-white leading-relaxed">
                                  {t.complaint_text || t.complaint_narration || 'No complaint text recorded.'}
                                </p>
                              </div>

                              <div className="bg-white dark:bg-vault-dark-card rounded-xl p-4 border border-gray-100 dark:border-white/5 space-y-2.5">
                                <p className="text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider mb-2">AI Routing Details</p>
                                <div className="flex justify-between text-xs">
                                  <span className="text-gray-400 dark:text-slate-500">Routed To</span>
                                  <span className="font-bold text-gray-800 dark:text-white">{t.department_name || 'Pending'}</span>
                                </div>
                                <div className="flex justify-between text-xs">
                                  <span className="text-gray-400 dark:text-slate-500">Dept Code</span>
                                  <span className="font-mono font-bold text-gray-800 dark:text-white">{t.department_code || '—'}</span>
                                </div>
                                <div className="flex justify-between text-xs">
                                  <span className="text-gray-400 dark:text-slate-500">Priority Level</span>
                                  <span className="font-bold text-gray-800 dark:text-white">{t.priority_level || '—'}</span>
                                </div>
                                <div className="flex justify-between text-xs">
                                  <span className="text-gray-400 dark:text-slate-500">Confidence Score</span>
                                  <span className="font-bold text-gray-800 dark:text-white">{t.confidence != null ? `${Math.round(Number(t.confidence) * 100)}%` : '—'}</span>
                                </div>
                                <div className="flex justify-between text-xs">
                                  <span className="text-gray-400 dark:text-slate-500">Date</span>
                                  <span className="font-bold text-gray-800 dark:text-white">{formatDate(t.complaint_timestamp || t.created_at)}</span>
                                </div>
                                <div className="flex justify-between text-xs">
                                  <span className="text-gray-400 dark:text-slate-500">SLA Hours</span>
                                  <span className="font-bold text-gray-800 dark:text-white">{t.sla_hours || t.sla_hours_limit || '—'}</span>
                                </div>
                                <div className="flex justify-between text-xs">
                                  <span className="text-gray-400 dark:text-slate-500">Channel</span>
                                  <span className="font-bold text-gray-800 dark:text-white">{t.complaint_channel || '—'}</span>
                                </div>
                                {t.assigned_to && (
                                  <div className="flex justify-between text-xs">
                                    <span className="text-gray-400 dark:text-slate-500">Assigned To</span>
                                    <span className="font-bold text-gray-800 dark:text-white">{t.assigned_to}</span>
                                  </div>
                                )}
                                <div className="flex flex-col text-xs mt-3">
                                  <span className="text-gray-400 dark:text-slate-500 mb-1">Reasoning</span>
                                  <span className="font-medium text-gray-800 dark:text-white leading-relaxed bg-gray-50 dark:bg-white/5 p-2.5 rounded-lg border border-gray-100 dark:border-white/5">{t.reasoning || 'No reasoning provided.'}</span>
                                </div>
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default ComplaintsModule;
