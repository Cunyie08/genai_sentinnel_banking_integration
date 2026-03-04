import { useState, useEffect } from 'react';
import { MdPerson, MdEmail, MdPhone, MdLock, MdEdit, MdCheckCircle, MdErrorOutline } from 'react-icons/md';
import Layout from '../components/Layout';
import axiosInstance from '../api/axiosInstance';

const Profile = () => {
  const [user, setUser] = useState(null);
  const [profileForm, setProfileForm] = useState({ first_name: '', last_name: '', phone_number: '' });
  const [pwForm, setPwForm] = useState({ current_password: '', new_password: '', confirm: '' });
  const [editProfile, setEditProfile] = useState(false);
  const [editPw, setEditPw] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [toast, setToast] = useState({ msg: '', type: '' });

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast({ msg: '', type: '' }), 3500);
  };

  useEffect(() => {
    axiosInstance.get('/users/me').then(res => {
      setUser(res.data);
      const c = res.data.customer_details || {};
      setProfileForm({ first_name: c.first_name || '', last_name: c.last_name || '', phone_number: c.phone_number || '' });
    }).catch(() => {});
  }, []);

  const saveProfile = async e => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await axiosInstance.patch('/users/update-profile', profileForm);
      showToast('Profile updated successfully!');
      setEditProfile(false);
    } catch (err) {
      showToast(err.response?.data?.detail || 'Update failed.', 'error');
    } finally { setIsLoading(false); }
  };

  const savePassword = async e => {
    e.preventDefault();
    if (pwForm.new_password !== pwForm.confirm) { showToast('Passwords do not match.', 'error'); return; }
    if (pwForm.new_password.length < 8) { showToast('Password must be at least 8 characters.', 'error'); return; }
    setIsLoading(true);
    try {
      await axiosInstance.patch('/auth/change-password', { current_password: pwForm.current_password, new_password: pwForm.new_password });
      showToast('Password changed successfully!');
      setEditPw(false);
      setPwForm({ current_password: '', new_password: '', confirm: '' });
    } catch (err) {
      showToast(err.response?.data?.detail || 'Change failed.', 'error');
    } finally { setIsLoading(false); }
  };

  const inputClass = "w-full px-4 py-3.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 text-sm placeholder:text-slate-400 focus:outline-none transition-all";
  const firstName = profileForm.first_name || user?.email?.split('@')[0] || 'U';

  return (
    <Layout>
      <div className="mb-6">
        <h1 className="text-2xl font-extrabold text-slate-900">My Profile</h1>
        <p className="text-slate-500 text-sm mt-1">Manage your personal information and security settings.</p>
      </div>

      {toast.msg && (
        <div className={`flex items-center gap-3 rounded-xl px-4 py-3 mb-5 text-sm font-semibold ${
          toast.type === 'error' ? 'bg-red-50 text-red-600 border border-red-200' : 'bg-green-50 text-green-700 border border-green-200'
        }`}>
          {toast.type === 'error' ? <MdErrorOutline size={20} /> : <MdCheckCircle size={20} />}
          {toast.msg}
        </div>
      )}

      <div className="max-w-xl space-y-5">
        {/* Avatar */}
        <div className="bg-white rounded-2xl shadow-sm p-6 flex items-center gap-5">
          <div className="w-20 h-20 rounded-full flex items-center justify-center text-white text-3xl font-extrabold shrink-0"
            style={{ backgroundColor: '#0000ff' }}>
            {firstName[0]?.toUpperCase()}
          </div>
          <div>
            <p className="text-lg font-bold text-slate-900">{[profileForm.first_name, profileForm.last_name].filter(Boolean).join(' ') || 'Customer'}</p>
            <p className="text-sm text-slate-400">{user?.email}</p>
            <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-blue-50 mt-1 inline-block" style={{ color: '#0000ff' }}>
              {user?.role || 'Customer'}
            </span>
          </div>
        </div>

        {/* Profile form */}
        <div className="bg-white rounded-2xl shadow-sm p-6">
          <div className="flex justify-between items-center mb-5">
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2"><MdPerson size={18} style={{ color: '#0000ff' }} /> Personal Info</h2>
            {!editProfile && <button onClick={() => setEditProfile(true)} className="flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-lg" style={{ color: '#0000ff', backgroundColor: 'rgba(0,0,255,0.06)' }}><MdEdit size={15} /> Edit</button>}
          </div>
          <form onSubmit={saveProfile} className="space-y-4">
            {[
              { name: 'first_name', label: 'First Name', icon: MdPerson },
              { name: 'last_name', label: 'Last Name', icon: MdPerson },
              { name: 'phone_number', label: 'Phone Number', icon: MdPhone },
            ].map(({ name, label, icon: Icon }) => (
              <div key={name}>
                <label className="block text-sm font-semibold text-slate-700 mb-1.5">{label}</label>
                <div className="relative">
                  <Icon className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                  <input name={name} value={profileForm[name]} onChange={e => setProfileForm(p => ({ ...p, [e.target.name]: e.target.value }))}
                    disabled={!editProfile} className={`${inputClass} pl-11 ${!editProfile ? 'opacity-70 cursor-not-allowed' : ''}`}
                    onFocus={e => { if (editProfile) e.target.style.borderColor = '#0000ff'; }}
                    onBlur={e => e.target.style.borderColor = '#e2e8f0'} />
                </div>
              </div>
            ))}
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1.5">Email Address</label>
              <div className="relative">
                <MdEmail className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                <input value={user?.email || ''} disabled className={`${inputClass} pl-11 opacity-60 cursor-not-allowed`} />
              </div>
            </div>
            {editProfile && (
              <div className="flex gap-3 pt-1">
                <button type="button" onClick={() => setEditProfile(false)} className="flex-1 py-3 rounded-xl border border-slate-200 text-sm font-bold text-slate-600">Cancel</button>
                <button type="submit" disabled={isLoading} className="flex-1 py-3 rounded-xl text-white text-sm font-bold disabled:opacity-60" style={{ backgroundColor: '#0000ff' }}>
                  {isLoading ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            )}
          </form>
        </div>

        {/* Change password */}
        <div className="bg-white rounded-2xl shadow-sm p-6">
          <div className="flex justify-between items-center mb-5">
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2"><MdLock size={18} style={{ color: '#0000ff' }} /> Security</h2>
            {!editPw && <button onClick={() => setEditPw(true)} className="flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-lg" style={{ color: '#0000ff', backgroundColor: 'rgba(0,0,255,0.06)' }}><MdEdit size={15} /> Change Password</button>}
          </div>
          {editPw && (
            <form onSubmit={savePassword} className="space-y-4">
              {[
                { name: 'current_password', label: 'Current Password' },
                { name: 'new_password', label: 'New Password' },
                { name: 'confirm', label: 'Confirm New Password' },
              ].map(({ name, label }) => (
                <div key={name}>
                  <label className="block text-sm font-semibold text-slate-700 mb-1.5">{label}</label>
                  <div className="relative">
                    <MdLock className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                    <input name={name} type="password" required value={pwForm[name]}
                      onChange={e => setPwForm(p => ({ ...p, [e.target.name]: e.target.value }))}
                      className={`${inputClass} pl-11`}
                      onFocus={e => e.target.style.borderColor = '#0000ff'}
                      onBlur={e => e.target.style.borderColor = '#e2e8f0'} />
                  </div>
                </div>
              ))}
              <div className="flex gap-3 pt-1">
                <button type="button" onClick={() => setEditPw(false)} className="flex-1 py-3 rounded-xl border border-slate-200 text-sm font-bold text-slate-600">Cancel</button>
                <button type="submit" disabled={isLoading} className="flex-1 py-3 rounded-xl text-white text-sm font-bold disabled:opacity-60" style={{ backgroundColor: '#0000ff' }}>
                  {isLoading ? 'Saving...' : 'Update Password'}
                </button>
              </div>
            </form>
          )}
          {!editPw && <p className="text-sm text-slate-400">Click "Change Password" to update your login credentials.</p>}
        </div>
      </div>
    </Layout>
  );
};

export default Profile;
