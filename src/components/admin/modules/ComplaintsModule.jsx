
import React, { useState } from 'react';
import AIThoughtProcess from '../AIThoughtProcess';

const ComplaintsModule = ({ tickets, stats }) => {
  const [selectedTicket, setSelectedTicket] = useState(tickets?.[0] || null);

  return (
    <div className="max-w-6xl mx-auto space-y-6">
        <AIThoughtProcess ticket={selectedTicket} />
        <div>
            <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-bold text-gray-900">
                Pending Resolution Queue
                {stats && <span className="ml-2 text-xs font-medium text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">{stats.pendingTickets} Active</span>}
                </h3>
            </div>
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
                <table className="w-full text-left">
                    <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                        <th className="px-6 py-4 text-[10px] font-bold text-gray-400 uppercase tracking-wider">Ticket ID</th>
                        <th className="px-6 py-4 text-[10px] font-bold text-gray-400 uppercase tracking-wider">Customer</th>
                        <th className="px-6 py-4 text-[10px] font-bold text-gray-400 uppercase tracking-wider">Issue Type</th>
                        <th className="px-6 py-4 text-[10px] font-bold text-gray-400 uppercase tracking-wider">Confidence</th>
                        <th className="px-6 py-4 text-[10px] font-bold text-gray-400 uppercase tracking-wider text-right">Action</th>
                    </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                    {tickets && tickets.map((t, i) => (
                        <tr key={i} onClick={() => setSelectedTicket(t)} className={`cursor-pointer transition-colors ${selectedTicket?.id === t.id ? 'bg-red-50' : 'hover:bg-gray-50'}`}>
                        <td className="px-6 py-4 text-xs font-bold text-gray-500">{t.id}</td>
                        <td className="px-6 py-4"><p className="text-sm font-bold text-gray-900">{t.user}</p></td>
                        <td className="px-6 py-4"><span className={`px-2 py-1 rounded text-[10px] font-bold uppercase ${t.color}`}>{t.issue}</span></td>
                        <td className="px-6 py-4 w-48">
                            <div className="flex items-center gap-2">
                            <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden"><div className={`h-full rounded-full ${t.confidence > 90 ? 'bg-green-500' : 'bg-yellow-500'}`} style={{ width: `${t.confidence}%` }}></div></div>
                            <span className="text-xs font-bold text-gray-600">{t.confidence}%</span>
                            </div>
                        </td>
                        <td className="px-6 py-4 text-right"><button className="text-[#A01030] text-xs font-bold hover:underline">Review AI</button></td>
                        </tr>
                    ))}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
  );
};

export default ComplaintsModule;
