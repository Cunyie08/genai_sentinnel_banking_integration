import { useState, useEffect } from 'react';
import {
  MdCreditCard, MdAdd, MdLock, MdLockOpen,
  MdTune, MdCheckCircle, MdErrorOutline
} from 'react-icons/md';
import Layout from '../components/Layout';
import axiosInstance from '../api/axiosInstance';

const Cards = () => {
  const [cards, setCards] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState('');
  const [showRequest, setShowRequest] = useState(false);
  const [requestForm, setRequestForm] = useState({ account_id: '', card_type: 'Debit' });
  const [toast, setToast] = useState({ msg: '', type: '' });

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast({ msg: '', type: '' }), 3500);
  };

  const load = async () => {
    try {
      const [cardsRes, userRes] = await Promise.all([
        axiosInstance.get('/cards/'),
        axiosInstance.get('/users/me'),
      ]);
      setCards(cardsRes.data || []);
      setAccounts(userRes.data?.account_details || []);
    } catch {
      showToast('Failed to load cards.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const toggleFreeze = async (card) => {
    setActionLoading(card.card_id);
    const endpoint = card.status === 'frozen' ? 'activate' : 'freeze';
    try {
      await axiosInstance.patch(`/cards/${card.card_id}/${endpoint}`);
      showToast(`Card ${endpoint === 'freeze' ? 'frozen' : 'activated'} successfully.`);
      load();
    } catch {
      showToast('Action failed. Try again.', 'error');
    } finally {
      setActionLoading('');
    }
  };

  const requestCard = async e => {
    e.preventDefault();
    setActionLoading('request');
    try {
      await axiosInstance.post('/cards/request', requestForm);
      showToast('Card requested successfully!');
      setShowRequest(false);
      load();
    } catch (err) {
      showToast(err.response?.data?.detail || 'Request failed.', 'error');
    } finally {
      setActionLoading('');
    }
  };

  const maskNumber = (num) => num ? `**** **** **** ${num.slice(-4)}` : '**** **** **** ****';

  return (
    <Layout>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900">My Cards</h1>
          <p className="text-slate-500 text-sm mt-1">Manage your virtual and physical debit cards.</p>
        </div>
        <button onClick={() => setShowRequest(true)}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-white text-sm font-bold transition-all"
          style={{ backgroundColor: '#0000ff' }}>
          <MdAdd size={18} /> New Card
        </button>
      </div>

      {toast.msg && (
        <div className={`flex items-center gap-3 rounded-xl px-4 py-3 mb-5 text-sm font-semibold ${
          toast.type === 'error' ? 'bg-red-50 text-red-600 border border-red-200' : 'bg-green-50 text-green-700 border border-green-200'
        }`}>
          {toast.type === 'error' ? <MdErrorOutline size={20} /> : <MdCheckCircle size={20} />}
          {toast.msg}
        </div>
      )}

      {isLoading ? (
        <div className="flex justify-center py-16">
          <div className="w-8 h-8 rounded-full border-4 border-slate-200 animate-spin" style={{ borderTopColor: '#0000ff' }} />
        </div>
      ) : cards.length === 0 ? (
        <div className="bg-white rounded-2xl shadow-sm p-12 text-center">
          <MdCreditCard size={48} className="text-slate-200 mx-auto mb-3" />
          <p className="text-slate-500 font-medium">No cards yet. Request your first card!</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          {cards.map((card) => (
            <div key={card.card_id}
              className={`rounded-2xl p-5 text-white relative overflow-hidden ${card.status === 'frozen' ? 'opacity-70' : ''}`}
              style={{ background: 'linear-gradient(135deg, #0000ff 0%, #1414ff 50%, #4a86e8 100%)' }}>
              <div className="absolute -top-6 -right-6 w-24 h-24 rounded-full opacity-20 bg-white" />
              <div className="flex justify-between items-start mb-6">
                <div>
                  <p className="text-xs opacity-70 font-medium">Sentinel Bank</p>
                  <p className="text-sm font-bold mt-0.5">{card.card_type} Card</p>
                </div>
                <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${
                  card.status === 'active' ? 'bg-green-400/30 text-green-100' : 'bg-red-400/30 text-red-100'
                }`}>{card.status}</span>
              </div>
              <p className="text-lg font-bold tracking-widest mb-4">{maskNumber(card.card_number)}</p>
              <div className="flex justify-between items-end">
                <div>
                  <p className="text-xs opacity-70">Expires</p>
                  <p className="text-sm font-semibold">{card.expiry_date || '—'}</p>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => toggleFreeze(card)} disabled={actionLoading === card.card_id}
                    className="flex items-center gap-1.5 bg-white/20 hover:bg-white/30 text-white text-xs font-bold px-3 py-1.5 rounded-lg transition-all disabled:opacity-50">
                    {card.status === 'frozen' ? <MdLockOpen size={14} /> : <MdLock size={14} />}
                    {card.status === 'frozen' ? 'Unfreeze' : 'Freeze'}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Request Card Modal */}
      {showRequest && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm p-6">
            <div className="flex items-center gap-2 mb-5">
              <MdCreditCard size={22} style={{ color: '#0000ff' }} />
              <h3 className="text-lg font-bold text-slate-900">Request New Card</h3>
            </div>
            <form onSubmit={requestCard} className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1.5">Account</label>
                <select value={requestForm.account_id}
                  onChange={e => setRequestForm(p => ({ ...p, account_id: e.target.value }))}
                  required className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-50 text-sm text-slate-900 focus:outline-none"
                  onFocus={e => e.target.style.borderColor = '#0000ff'}
                  onBlur={e => e.target.style.borderColor = '#e2e8f0'}>
                  <option value="">Select account</option>
                  {accounts.map(a => <option key={a.account_id} value={a.account_id}>{a.account_number || a.account_id}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1.5">Card Type</label>
                <div className="flex gap-3">
                  {['Debit', 'Credit'].map(t => (
                    <button key={t} type="button"
                      onClick={() => setRequestForm(p => ({ ...p, card_type: t }))}
                      className={`flex-1 py-2.5 rounded-xl text-sm font-bold border-2 transition-all ${
                        requestForm.card_type === t ? 'text-white border-transparent' : 'bg-white text-slate-600 border-slate-200'
                      }`}
                      style={requestForm.card_type === t ? { backgroundColor: '#0000ff', borderColor: '#0000ff' } : {}}>
                      {t}
                    </button>
                  ))}
                </div>
              </div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowRequest(false)}
                  className="flex-1 py-3 rounded-xl border border-slate-200 text-sm font-bold text-slate-600 hover:bg-slate-50">
                  Cancel
                </button>
                <button type="submit" disabled={actionLoading === 'request'}
                  className="flex-1 py-3 rounded-xl text-white text-sm font-bold disabled:opacity-60"
                  style={{ backgroundColor: '#0000ff' }}>
                  {actionLoading === 'request' ? 'Requesting...' : 'Request Card'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </Layout>
  );
};

export default Cards;
