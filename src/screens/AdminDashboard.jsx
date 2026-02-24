import React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { setAdminTab, setRoute } from '../features/uiSlice';
import { 
  LayoutGrid, Users, Bell, ShieldAlert, Settings, 
  Search, RefreshCw, LogOut, CheckCircle, AlertTriangle, 
  ArrowRight, FileText, Smartphone, CreditCard, ChevronRight, ChevronLeft
} from 'lucide-react';

const AdminDashboard = () => {
  const dispatch = useDispatch();
  const activeTab = useSelector(state => state.ui.adminActiveTab);

  // --- MOCK DATA FOR THE TABLE ---
  const tickets = [
    { id: '#49202', user: 'Chinedu Okafor', tier: 'Tier 3 Account', avatar: 'CO', issue: 'ATM ERROR', confidence: 98, time: '12 mins ago', color: 'bg-yellow-100 text-yellow-700' },
    { id: '#49203', user: 'Zainab Abubakar', tier: 'Tier 1 Account', avatar: 'ZA', issue: 'FRAUD ALERT', confidence: 72, time: '28 mins ago', color: 'bg-red-100 text-red-700' },
    { id: '#49204', user: 'Emeka Taiwo', tier: 'Business Account', avatar: 'ET', issue: 'TRANSFER LAG', confidence: 92, time: '45 mins ago', color: 'bg-blue-100 text-blue-700' },
  ];

  // --- SIDEBAR COMPONENT ---
  const SidebarItem = ({ id, icon: Icon, label }) => (
    <button 
      onClick={() => dispatch(setAdminTab(id))}
      className={`w-full flex items-center gap-3 px-6 py-4 text-sm font-medium transition-colors border-l-4 ${
        activeTab === id 
          ? 'bg-red-50 text-[#A01030] border-[#A01030]' 
          : 'text-gray-500 border-transparent hover:bg-gray-50'
      }`}
    >
      <Icon size={20} />
      {label}
    </button>
  );

  return (
    <div className="flex h-screen bg-[#F8F9FB] font-sans overflow-hidden">
      
      {/* --- 1. LEFT SIDEBAR --- */}
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col shrink-0 z-20">
        {/* Logo */}
        <div className="h-20 flex items-center px-6 border-b border-gray-100">
           <div className="w-8 h-8 bg-[#A01030] rounded-lg flex items-center justify-center text-white font-black mr-3">N</div>
           <span className="text-xl font-bold text-gray-900 tracking-tight">Nexus<span className="text-[#A01030]">Bank</span></span>
        </div>

        {/* Menu */}
        <div className="flex-1 py-6 space-y-1">
          <SidebarItem id="overview" icon={LayoutGrid} label="Overview" />
          <SidebarItem id="users" icon={Users} label="Users" />
          <SidebarItem id="complaints" icon={Bell} label="Complaints" />
          <SidebarItem id="fraud" icon={ShieldAlert} label="Fraud Detection" />
          
          <div className="pt-8 pb-2 px-6 text-xs font-bold text-gray-400 uppercase tracking-wider">Settings</div>
          <SidebarItem id="config" icon={Settings} label="System Config" />
        </div>

        {/* Admin Profile */}
        <div className="p-4 border-t border-gray-100">
          <div className="bg-gray-50 rounded-xl p-3 flex items-center gap-3 cursor-pointer hover:bg-gray-100 transition-colors">
            <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=Admin" className="w-10 h-10 rounded-full bg-orange-200" alt="Admin"/>
            <div className="flex-1 min-w-0">
              <h4 className="text-sm font-bold text-gray-900 truncate">Adekunle Johnson</h4>
              <p className="text-[10px] text-gray-500 font-bold">SUPER ADMIN</p>
            </div>
            <button onClick={() => dispatch(setRoute('welcome'))}>
               <LogOut size={16} className="text-gray-400 hover:text-[#A01030]" />
            </button>
          </div>
        </div>
      </aside>

      {/* --- 2. MAIN CONTENT AREA --- */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
        
        {/* Header */}
        <header className="h-20 bg-white border-b border-gray-200 px-8 flex items-center justify-between shrink-0">
          <div>
            <div className="flex items-center gap-2 text-xs font-medium text-gray-400 mb-1">
              <span>Admin Hub</span> <ChevronRight size={12}/> <span className="text-[#A01030]">User Resolution Hub</span>
            </div>
            <h1 className="text-2xl font-bold text-gray-900">User Resolution Hub</h1>
          </div>

          <div className="flex items-center gap-4">
            <div className="relative">
               <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
               <input type="text" placeholder="Search ticket ID..." className="pl-10 pr-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-[#A01030] w-64" />
            </div>
            <button className="flex items-center gap-2 bg-[#A01030] text-white px-4 py-2.5 rounded-lg text-sm font-bold hover:bg-[#850d28] transition-colors shadow-lg shadow-red-900/20">
              <RefreshCw size={16} /> Refresh Queue
            </button>
          </div>
        </header>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto p-8">
          
          {/* CONTENT SWITCHER based on Tab */}
          {activeTab === 'complaints' ? (
            <div className="max-w-5xl mx-auto space-y-6">

              {/* --- A. AI THOUGHT PROCESS CARD --- */}
              <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
                {/* Card Header */}
                <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
                   <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-red-100 rounded-lg flex items-center justify-center">
                        <span className="text-lg">🤖</span>
                      </div>
                      <div>
                        <h3 className="text-sm font-bold text-gray-900">AI Thought Process: Ticket #49202</h3>
                        <p className="text-xs text-gray-500">Processing live resolution routing...</p>
                      </div>
                   </div>
                   <div className="flex gap-2">
                     <span className="px-2 py-1 bg-green-100 text-green-700 text-[10px] font-bold rounded uppercase flex items-center gap-1">
                       <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></span> Live
                     </span>
                     <span className="px-2 py-1 bg-gray-100 text-gray-600 text-[10px] font-bold rounded uppercase">
                       Confidence: 98.4%
                     </span>
                   </div>
                </div>

                {/* VISUAL STEPS */}
                <div className="p-8 relative">
                   {/* Vertical Connecting Line */}
                   <div className="absolute left-[59px] top-12 bottom-24 w-0.5 bg-gradient-to-b from-[#A01030] to-gray-200 z-0"></div>

                   {/* Step 1 */}
                   <div className="flex gap-6 mb-8 relative z-10">
                      <div className="w-10 h-10 rounded-full bg-white border-2 border-[#A01030] flex items-center justify-center text-[#A01030] shadow-sm shrink-0">
                        <Smartphone size={20} />
                      </div>
                      <div className="flex-1">
                        <h4 className="text-sm font-bold text-gray-900 mb-2">Step 1: Input Received</h4>
                        <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
                          <p className="text-sm text-gray-700 mb-3 font-medium">"My card was charged NGN 50,000 at a Zenith Bank ATM but no cash was dispensed. Please revert immediately."</p>
                          <div className="flex gap-2">
                            <span className="px-2 py-1 bg-gray-200 text-gray-600 text-[10px] font-bold rounded">CATEGORY: COMPLAINT</span>
                            <span className="px-2 py-1 bg-gray-200 text-gray-600 text-[10px] font-bold rounded">LANGUAGE: ENGLISH</span>
                          </div>
                        </div>
                      </div>
                   </div>

                   {/* Step 2 */}
                   <div className="flex gap-6 mb-8 relative z-10">
                      <div className="w-10 h-10 rounded-full bg-white border-2 border-[#A01030] flex items-center justify-center text-[#A01030] shadow-sm shrink-0">
                        <Search size={20} />
                      </div>
                      <div className="flex-1">
                        <h4 className="text-sm font-bold text-gray-900 mb-2">Step 2: Intent Detected</h4>
                        <div className="bg-red-50 border border-red-100 rounded-xl p-4 flex justify-between items-center">
                          <div>
                            <span className="text-sm font-bold text-[#A01030]">Dispense Error (98% confidence)</span>
                            <p className="text-xs text-gray-500 mt-1">Cross-referenced with Transaction ID: #TXN_982348. Status: Pending Reversal.</p>
                          </div>
                          <span className="px-2 py-1 bg-white/50 text-[#A01030] text-[10px] font-bold rounded border border-red-200 uppercase">Auto-Tagged</span>
                        </div>
                      </div>
                   </div>

                   {/* Step 3 */}
                   <div className="flex gap-6 relative z-10">
                      <div className="w-10 h-10 rounded-full bg-[#A01030] flex items-center justify-center text-white shadow-sm shrink-0">
                        <ArrowRight size={20} />
                      </div>
                      <div className="flex-1">
                        <h4 className="text-sm font-bold text-gray-900 mb-2">Step 3: Route Selected</h4>
                        <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
                          <div className="flex items-center gap-2 mb-1">
                             <Users size={16} className="text-gray-400"/>
                             <span className="text-sm font-bold text-gray-900">Reconciliation Team (Tier 2)</span>
                          </div>
                          <p className="text-xs text-gray-500">SLA target: 4 hours. Escalated due to high-value transaction (NGN 50k+).</p>
                        </div>
                      </div>
                   </div>
                </div>

                {/* Footer Buttons */}
                <div className="px-6 py-4 border-t border-gray-100 bg-gray-50 flex justify-end gap-3">
                  <button className="px-4 py-2 bg-white border border-red-200 text-[#A01030] rounded-lg text-sm font-bold hover:bg-red-50 transition-colors">
                     ✏️ Override Manually
                  </button>
                  <button className="px-4 py-2 bg-[#A01030] text-white rounded-lg text-sm font-bold hover:bg-[#850d28] transition-colors shadow-md shadow-red-900/10">
                     <CheckCircle size={16} className="inline mr-2"/> Approve Routing
                  </button>
                </div>
              </div>

              {/* --- B. PENDING RESOLUTION QUEUE (Table) --- */}
              <div>
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-bold text-gray-900">Pending Resolution Queue</h3>
                  <button className="flex items-center gap-2 px-3 py-1.5 bg-white border border-gray-200 rounded-lg text-xs font-bold text-gray-600">
                    All Statuses <ChevronRight size={14}/>
                  </button>
                </div>

                <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
                  <table className="w-full text-left">
                    <thead className="bg-gray-50 border-b border-gray-200">
                      <tr>
                        <th className="px-6 py-4 text-[10px] font-bold text-gray-400 uppercase tracking-wider">Ticket ID</th>
                        <th className="px-6 py-4 text-[10px] font-bold text-gray-400 uppercase tracking-wider">Customer</th>
                        <th className="px-6 py-4 text-[10px] font-bold text-gray-400 uppercase tracking-wider">Issue Type</th>
                        <th className="px-6 py-4 text-[10px] font-bold text-gray-400 uppercase tracking-wider">Confidence</th>
                        <th className="px-6 py-4 text-[10px] font-bold text-gray-400 uppercase tracking-wider">Time Elapsed</th>
                        <th className="px-6 py-4 text-[10px] font-bold text-gray-400 uppercase tracking-wider text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {tickets.map((t, i) => (
                        <tr key={i} className="hover:bg-gray-50 transition-colors">
                          <td className="px-6 py-4 text-xs font-bold text-gray-500">{t.id}</td>
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-3">
                               <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${i===0 ? 'bg-pink-100 text-pink-700' : i===1 ? 'bg-blue-100 text-blue-700' : 'bg-red-100 text-red-700'}`}>
                                  {t.avatar}
                               </div>
                               <div>
                                  <p className="text-sm font-bold text-gray-900">{t.user}</p>
                                  <p className="text-[10px] text-gray-400">{t.tier}</p>
                               </div>
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <span className={`px-2 py-1 rounded text-[10px] font-bold uppercase ${t.color}`}>
                              {t.issue}
                            </span>
                          </td>
                          <td className="px-6 py-4 w-48">
                             <div className="flex items-center gap-2">
                               <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                                 <div className={`h-full rounded-full ${t.confidence > 90 ? 'bg-green-500' : t.confidence > 70 ? 'bg-yellow-500' : 'bg-red-500'}`} style={{ width: `${t.confidence}%` }}></div>
                               </div>
                               <span className="text-xs font-bold text-gray-600">{t.confidence}%</span>
                             </div>
                          </td>
                          <td className="px-6 py-4 text-xs font-medium text-gray-500">{t.time}</td>
                          <td className="px-6 py-4 text-right">
                             <button className="text-[#A01030] text-xs font-bold hover:underline">Review AI</button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {/* Pagination Footer */}
                  <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-between items-center">
                     <p className="text-[10px] font-bold text-gray-400 uppercase">Showing 3 of 42 pending tickets</p>
                     <div className="flex gap-2">
                        <button className="w-8 h-8 bg-white border border-gray-200 rounded-lg flex items-center justify-center text-gray-400 hover:text-gray-900"><ChevronLeft size={16}/></button>
                        <button className="w-8 h-8 bg-white border border-gray-200 rounded-lg flex items-center justify-center text-gray-400 hover:text-gray-900"><ChevronRight size={16}/></button>
                     </div>
                  </div>
                </div>
              </div>

            </div>
          ) : (
            // --- PLACEHOLDERS FOR OTHER TABS ---
            <div className="flex flex-col items-center justify-center h-full text-center opacity-50">
              <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mb-4">
                 <Settings size={32} className="text-gray-400"/>
              </div>
              <h2 className="text-xl font-bold text-gray-900 mb-2">{activeTab.charAt(0).toUpperCase() + activeTab.slice(1)} Module</h2>
              <p className="text-sm text-gray-500">This module is active but currently has no pending alerts.</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default AdminDashboard;