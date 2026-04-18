import React, { useEffect, useState, useCallback } from 'react';
import { useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/axiosConfig';

import DashboardLayout from '../components/layout/DashboardLayout';
import OverviewModule from '../components/admin/modules/OverviewModule';
import UsersModule from '../components/admin/modules/UsersModule';
import ComplaintsModule from '../components/admin/modules/ComplaintsModule';
import FraudModule from '../components/admin/modules/FraudModule';

const AdminDashboard = () => {
  const activeTab = useSelector(state => state.ui.adminActiveTab);
  const navigate = useNavigate();

  const [tickets, setTickets]           = useState([]);
  const [users, setUsers]               = useState([]);
  const [stats, setStats]               = useState(null);
  const [loadingTickets, setLoadingTickets] = useState(false);
  const [loadingUsers, setLoadingUsers]     = useState(false);
  const [error, setError]               = useState('');

  useEffect(() => {
    const session = localStorage.getItem('sentinel_admin');
    if (!session) {
      navigate('/admin');
    }
  }, [navigate]);

  const fetchTickets = useCallback(async () => {
    setLoadingTickets(true);
    setError('');
    try {
      const res = await api.getAdminTickets({ limit: 200 });
      const raw = res?.data?.decisions || res?.data?.tickets || res?.data || [];
      setTickets(Array.isArray(raw) ? raw : []);
    } catch (err) {
      console.error('Failed to fetch tickets:', err);
      setError('Could not load complaints. Make sure the backend is running and you are logged in as a user.');
      setTickets([]);
    } finally {
      setLoadingTickets(false);
    }
  }, []);

  const fetchUsers = useCallback(async () => {
    setLoadingUsers(true);
    try {
      const res = await api.getAdminUsers();
      const raw = res?.data?.users || res?.data || [];
      setUsers(Array.isArray(raw) ? raw : []);
    } catch (err) {
      console.error('Failed to fetch users:', err);
      setUsers([]);
    } finally {
      setLoadingUsers(false);
    }
  }, []);

  const fetchStats = useCallback(async () => {
    try {
      const res = await api.getAdminDashboard();
      setStats(res?.data || null);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
      setStats(null);
    }
  }, []);

  useEffect(() => {
    fetchTickets();
    fetchStats();

    if (activeTab === 'users') {
      fetchUsers();
    }
  }, [activeTab, fetchTickets, fetchStats, fetchUsers]);

  return (
    <DashboardLayout stats={stats}>

      {activeTab === 'overview' && (
        <OverviewModule stats={stats} ticketCount={tickets.length} />
      )}

      {activeTab === 'users' && (
        <UsersModule users={users} loading={loadingUsers} />
      )}

      {activeTab === 'complaints' && (
        <ComplaintsModule
          tickets={tickets}
          stats={stats}
          loading={loadingTickets}
          error={error}
          onRefresh={fetchTickets}
        />
      )}

      {activeTab === 'fraud' && (
        <FraudModule />
      )}

      {activeTab === 'config' && (
        <div className="flex flex-col items-center justify-center h-full text-center opacity-50">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">System Config</h2>
          <p className="text-sm text-gray-500 dark:text-slate-400">Under Construction</p>
        </div>
      )}

    </DashboardLayout>
  );
};

export default AdminDashboard;