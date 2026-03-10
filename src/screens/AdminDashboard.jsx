import React, { useEffect, useState } from 'react';
import { useSelector } from 'react-redux';
import { api } from '../api/axiosConfig'; 


import DashboardLayout from '../components/layout/DashboardLayout';
import OverviewModule from '../components/admin/modules/OverviewModule';
import UsersModule from '../components/admin/modules/UsersModule';
import ComplaintsModule from '../components/admin/modules/ComplaintsModule';

const AdminDashboard = () => {
  const activeTab = useSelector(state => state.ui.adminActiveTab);
  
  
  const [tickets, setTickets] = useState([]);
  const [users, setUsers] = useState([]);
  const [stats, setStats] = useState(null);

  
  const fetchData = async () => {
    try {
      const dashRes = await api.getAdminDashboard(); 
      setStats(dashRes.data);

      const mappedTickets = dashRes.data.recentTickets.map((t, index) => ({
        id: t.id,
        user: t.user,
        tier: index % 2 === 0 ? 'Tier 3 Account' : 'Tier 1 Account', 
        avatar: t.user.substring(0, 2).toUpperCase(),
        issue: t.issue.toUpperCase(),
        confidence: t.confidence,
        status: t.status,
        time: t.time || 'Just now',
        color: t.confidence > 90 ? 'bg-blue-100 text-blue-700' : 
               t.confidence > 80 ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'
      }));
      setTickets(mappedTickets);

      if (activeTab === 'users') {
        const userRes = await api.getAdminUsers();
        setUsers(userRes.data);
      }
    } catch (error) {
      console.error("Failed to fetch admin data:", error);
    }
  };

  useEffect(() => {
    fetchData();
  }, [activeTab]);

  return (
    <DashboardLayout stats={stats}>
        
        {activeTab === 'overview' && (
            <OverviewModule stats={stats} />
        )}

        {activeTab === 'users' && (
            <UsersModule users={users} />
        )}

        {activeTab === 'complaints' && (
            <ComplaintsModule tickets={tickets} stats={stats} />
        )}

        {}
        {['fraud', 'config'].includes(activeTab) && (
            <div className="flex flex-col items-center justify-center h-full text-center opacity-50">
                <h2 className="text-xl font-bold text-gray-900 mb-2 capitalize">{activeTab} Module</h2>
                <p className="text-sm text-gray-500">Under Construction</p>
            </div>
        )}

    </DashboardLayout>
  );
};

export default AdminDashboard;