import { useNavigate } from 'react-router-dom';
import React, { useState } from 'react';
import { useDispatch } from 'react-redux';

import { Lock, Shield, ArrowRight } from 'lucide-react';

const AdminLogin = () => {
  const navigate = useNavigate();

    const dispatch = useDispatch();
    const [id, setId] = useState('');
    const [key, setKey] = useState('');

    const handleLogin = () => {
        
        navigate('/admin/dashboard');
        
        
        window.history.pushState({}, '', '/admin/dashboard');
    };

    return (
        <div className="min-h-full bg-[#111] flex items-center justify-center p-4">
            <div className="max-w-sm w-full bg-[#222] rounded-[24px] border border-gray-800 p-8 text-center shadow-2xl">
                
                <div className="w-16 h-16 bg-[#A01030]/20 rounded-2xl flex items-center justify-center mx-auto mb-6 ring-1 ring-[#A01030]/50">
                    <Shield size={32} className="text-[#A01030]" />
                </div>

                <h1 className="text-2xl font-bold text-white">Sentinel Admin</h1>
                <p className="text-gray-500 text-sm mb-8">Secure Gateway v2.0</p>

                <div className="space-y-4 text-left">
                    <div>
                        <label className="text-[10px] font-bold text-gray-500 uppercase ml-1">Admin ID</label>
                        <input 
                            value={id} onChange={e => setId(e.target.value)}
                            type="text" 
                            className="w-full p-4 bg-[#333] border border-gray-700 rounded-xl outline-none focus:border-[#A01030] text-white transition-colors font-mono placeholder:text-gray-600"
                            placeholder="ADMIN-001"
                        />
                    </div>
                    <div>
                        <label className="text-[10px] font-bold text-gray-500 uppercase ml-1">Secure Key</label>
                        <div className="relative">
                            <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500" size={18} />
                            <input 
                                value={key} onChange={e => setKey(e.target.value)}
                                type="password" 
                                className="w-full p-4 pl-12 bg-[#333] border border-gray-700 rounded-xl outline-none focus:border-[#A01030] text-white transition-colors placeholder:text-gray-600"
                                placeholder="••••••••"
                            />
                        </div>
                    </div>
                </div>

                <button 
                    onClick={handleLogin}
                    className="w-full bg-[#A01030] text-white py-4 rounded-xl font-bold mt-8 hover:bg-[#8a0e29] transition-all shadow-lg shadow-red-900/20 active:scale-95 flex items-center justify-center gap-2"
                >
                    Authenticate <ArrowRight size={18}/>
                </button>

                <button 
                    onClick={() => navigate('/')}
                    className="mt-6 text-xs font-bold text-gray-500 hover:text-white transition-colors"
                >
                    ← Return to Mobile App
                </button>
            </div>
        </div>
    );
};

export default AdminLogin;