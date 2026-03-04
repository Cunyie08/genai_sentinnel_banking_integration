import { useState, useEffect } from 'react';
import { MdNotifications, MdDoneAll, MdDelete, MdCircle } from 'react-icons/md';
import Layout from '../components/Layout';
import axiosInstance from '../api/axiosInstance';

const Notifications = () => {
  const [notifications, setNotifications] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  const load = async () => {
    try {
      const res = await axiosInstance.get('/notifications/');
      setNotifications(res.data || []);
    } catch { /* ignore */ }
    finally { setIsLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const markRead = async (id) => {
    await axiosInstance.patch(`/notifications/${id}/read`).catch(() => {});
    setNotifications(prev => prev.map(n => n.notification_id === id ? { ...n, is_read: true } : n));
  };

  const deleteNotif = async (id) => {
    await axiosInstance.delete(`/notifications/${id}`).catch(() => {});
    setNotifications(prev => prev.filter(n => n.notification_id !== id));
  };

  const unreadCount = notifications.filter(n => !n.is_read).length;

  return (
    <Layout>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 flex items-center gap-2">
            Notifications
            {unreadCount > 0 && (
              <span className="text-xs font-bold px-2 py-0.5 rounded-full text-white" style={{ backgroundColor: '#0000ff' }}>{unreadCount}</span>
            )}
          </h1>
          <p className="text-slate-500 text-sm mt-1">Your in-app alerts and account updates.</p>
        </div>
      </div>

      <div className="max-w-xl">
        {isLoading ? (
          <div className="flex justify-center py-16">
            <div className="w-8 h-8 rounded-full border-4 border-slate-200 animate-spin" style={{ borderTopColor: '#0000ff' }} />
          </div>
        ) : notifications.length === 0 ? (
          <div className="bg-white rounded-2xl shadow-sm p-12 text-center">
            <MdNotifications size={48} className="text-slate-200 mx-auto mb-3" />
            <p className="text-slate-400 text-sm font-medium">No notifications yet</p>
          </div>
        ) : (
          <div className="space-y-3">
            {notifications.map(n => (
              <div key={n.notification_id}
                className={`bg-white rounded-2xl shadow-sm px-5 py-4 flex items-start gap-4 ${!n.is_read ? 'border-l-4' : ''}`}
                style={!n.is_read ? { borderLeftColor: '#0000ff' } : {}}>
                <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 mt-0.5`}
                  style={{ backgroundColor: n.is_read ? '#f1f5f9' : 'rgba(0,0,255,0.08)' }}>
                  <MdCircle size={16} style={{ color: n.is_read ? '#94a3b8' : '#0000ff' }} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className={`text-sm ${n.is_read ? 'text-slate-600' : 'text-slate-900 font-bold'}`}>{n.title}</p>
                  <p className="text-xs text-slate-400 mt-0.5 leading-relaxed">{n.message}</p>
                  <p className="text-xs text-slate-300 mt-1">{n.created_at ? new Date(n.created_at).toLocaleString() : ''}</p>
                </div>
                <div className="flex gap-1 shrink-0">
                  {!n.is_read && (
                    <button onClick={() => markRead(n.notification_id)} title="Mark as read"
                      className="p-1.5 rounded-lg hover:bg-blue-50 text-slate-400 hover:text-blue-600 transition-colors">
                      <MdDoneAll size={18} />
                    </button>
                  )}
                  <button onClick={() => deleteNotif(n.notification_id)} title="Delete"
                    className="p-1.5 rounded-lg hover:bg-red-50 text-slate-400 hover:text-red-500 transition-colors">
                    <MdDelete size={18} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
};

export default Notifications;
