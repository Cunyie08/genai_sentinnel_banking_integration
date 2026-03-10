
import axios from 'axios';
const MOCK_MODE    = true;
const API_BASE_URL = 'https://api.nexusbank.com/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 20000,
});


apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('sentinel_token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  },
  (error) => Promise.reject(error)
);


apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('sentinel_token');
      
    }
    return Promise.reject(error.response?.data || error);
  }
);
const mockData = {
  
  user: {
    id: 'u1',
    name: 'Reuben',
    email: 'reuben@sentinel.ng',
    phone: '08012345678',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Reuben',
    role: 'user', 
  },
  
  
  account: {
    balance: 4850200.50,
    number: '0123456789',
    tier: 'Tier 3',
    status: 'Active',
    type: 'Savings',
    currency: 'NGN'
  },

  
  transactions: [
    { id: 't1', type: 'debit', category: 'airtime', name: 'MTN Airtime', amount: 500, date: new Date().toISOString(), status: 'success', ref: 'AIR-882' },
    { id: 't2', type: 'credit', category: 'salary', name: 'Salary Sept', amount: 450000, date: new Date(Date.now() - 86400000).toISOString(), status: 'success', ref: 'SAL-001' },
    { id: 't3', type: 'debit', category: 'bills', name: 'EKEDC Bill', amount: 15000, date: new Date(Date.now() - 172800000).toISOString(), status: 'success', ref: 'BIL-992' },
    { id: 't4', type: 'debit', category: 'betting', name: 'Bet9ja Deposit', amount: 5000, date: new Date(Date.now() - 250000000).toISOString(), status: 'success', ref: 'BET-331' },
    { id: 't5', type: 'credit', category: 'transfer', name: 'Transfer from Chidi', amount: 25000, date: new Date(Date.now() - 500000000).toISOString(), status: 'success', ref: 'TRF-112' },
  ],

  
  smartFeed: [
    { 
      id: 1, 
      label: 'Education First', labelColor: '#FFD700', 
      title: 'Student Loan', subtitle: 'Up to ₦500k', 
      gradient: ['#2F4F4F', '#1A2E2E'], 
      cta: 'APPLY NOW', ctaRoute: 'loans' 
    },
    { 
      id: 2, 
      label: 'High Yield', labelColor: '#6EE7B7', 
      title: 'Fixed Deposit', subtitle: '15% Interest', 
      gradient: ['#0F766E', '#0D5E56'], 
      cta: 'START SAVING', ctaRoute: 'savings' 
    },
  ],

  
  paymentRequest: {
    id: 'req_88291',
    merchant: 'Amazon',
    amount: 45000.00,
    date: 'Oct 24, 14:20',
    currency: 'NGN',
    expiry: 300 
  },

  
  adminStats: {
    totalUsers: 24592,
    activeToday: 1840,
    pendingTickets: 42,
    flaggedTxns: 8,
    systemHealth: '99.9%'
  },

  
  adminTickets: [
    { 
      id: '#49202', 
      user: 'Chinedu Okafor', 
      issue: 'ATM ERROR', 
      category: 'Dispense Error',
      route: 'Reconciliation Team',
      confidence: 98, 
      status: 'pending', 
      time: '12 mins ago' 
    },
    { 
      id: '#49203', 
      user: 'Zainab Abubakar', 
      issue: 'FRAUD ALERT', 
      category: 'Suspicious Activity',
      route: 'Fraud Unit',
      confidence: 72, 
      status: 'review', 
      time: '28 mins ago' 
    },
    { 
      id: '#49204', 
      user: 'Emeka Taiwo', 
      issue: 'TRANSFER LAG', 
      category: 'Network Delay',
      route: 'Technical Support',
      confidence: 92, 
      status: 'resolved', 
      time: '45 mins ago' 
    },
    { 
      id: '#49205', 
      user: 'Tunde Bakare', 
      issue: 'DISPUTE', 
      category: 'Chargeback Request',
      route: 'Dispute Resolution',
      confidence: 65, 
      status: 'pending', 
      time: '1 hr ago' 
    },
  ],

  
  adminUsers: [
    { id: 'u1', name: 'Reuben', email: 'reuben@sentinel.ng', tier: 'Tier 3', status: 'Active', balance: '₦4,850,200.50' },
    { id: 'u2', name: 'Chinedu Okafor', email: 'chinedu@gmail.com', tier: 'Tier 2', status: 'Restricted', balance: '₦45,000.00' },
    { id: 'u3', name: 'Zainab Abubakar', email: 'zainab@yahoo.com', tier: 'Tier 1', status: 'Active', balance: '₦120,500.00' },
    { id: 'u4', name: 'Emeka Taiwo', email: 'emeka@business.ng', tier: 'Business', status: 'Active', balance: '₦12,450,000.00' },
    { id: 'u5', name: 'Funmi Bello', email: 'funmi@outlook.com', tier: 'Tier 3', status: 'Active', balance: '₦890,000.00' },
    { id: 'u6', name: 'Tunde Bakare', email: 'tunde@gmail.com', tier: 'Tier 2', status: 'Review', balance: '₦210,000.00' },
  ]
};


const delay = (ms) => new Promise(res => setTimeout(res, ms));

const mock = {
  
  login: async (creds) => {
    await delay(1000);
    if (creds.password === 'admin') {
      return { data: { token: 'mock-admin-token', user: { ...mockData.user, role: 'admin', name: 'Admin User' } } };
    }
    return { data: { token: 'mock-user-token', user: mockData.user } };
  },
  signup: async (creds) => {
    await delay(1500);
    return { data: { token: 'mock-new-user-token', user: { ...mockData.user, name: creds.name || 'New User' } } };
  },

  
  getDashboard: async () => {
    await delay(600);
    return { 
      data: { 
        account: mockData.account,
        stats: { totalIn: 1200000, totalOut: 45000 }
      } 
    };
  },

  
  getTransactions: async (params) => {
    await delay(500);
    return { data: { transactions: mockData.transactions } };
  },
  sendMoney: async (body) => {
    await delay(2000); 
    const newTx = { 
      id: 't' + Date.now(), type: 'debit', category: 'transfer', 
      name: `Transfer to ${body.recipient}`, amount: Number(body.amount), 
      date: new Date().toISOString(), status: 'success', ref: 'TRF-' + Math.floor(Math.random()*100000) 
    };
    mockData.transactions.unshift(newTx);
    return { data: newTx };
  },
  fundWallet: async (body) => {
    await delay(1500);
    const newTx = { 
      id: 't' + Date.now(), type: 'credit', category: 'fund', 
      name: `Fund via ${body.method}`, amount: Number(body.amount), 
      date: new Date().toISOString(), status: 'success', ref: 'FND-' + Math.floor(Math.random()*100000) 
    };
    mockData.transactions.unshift(newTx);
    return { data: newTx };
  },

  
  buyAirtime: async (body) => {
    await delay(1200);
    return { data: { service: 'airtime', ...body, ref: 'AIR-' + Date.now() } };
  },
  buyData: async (body) => {
    await delay(1200);
    return { data: { service: 'data', ...body, ref: 'DAT-' + Date.now() } };
  },
  payBill: async (body) => {
    await delay(1500);
    return { data: { service: 'bills', ...body, ref: 'BIL-' + Date.now() } };
  },
  fundBetting: async (body) => {
    await delay(1200);
    return { data: { service: 'betting', ...body, ref: 'BET-' + Date.now() } };
  },

  
  getSmartFeed: async () => {
    await delay(400);
    return { data: { cards: mockData.smartFeed } };
  },
  checkPaymentRequest: async () => {
    await delay(500);
    return { data: mockData.paymentRequest }; 
  },
  approvePayment: async (id) => {
    await delay(2000); 
    return { data: { status: 'success', transactionId: 'TXN-88291-AZ' } };
  },
  declinePayment: async (id) => {
    await delay(1000);
    return { data: { status: 'declined' } };
  },

  
  getChatHistory: async () => {
    await delay(300);
    return { data: [] }; 
  },
  sendMessage: async (body) => {
    await delay(1200);
    return { 
      data: { 
        id: Date.now(), sender: 'ai', type: 'text', 
        text: `I've received your query about "${body.message}". Checking our records...`, 
        time: new Date().toLocaleTimeString() 
      } 
    };
  },

  
  getAdminDashboard: async () => {
    await delay(800);
    return { 
      data: { 
        totalUsers: mockData.adminStats.totalUsers, 
        pendingTickets: mockData.adminStats.pendingTickets,
        recentTickets: mockData.adminTickets,
        activeToday: mockData.adminStats.activeToday
      } 
    };
  },
  getAdminUsers: async () => {
    await delay(800);
    return { data: mockData.adminUsers };
  },
};
export const api = {
  // =========================================================================
  // TO SWITCH TO REAL BACKEND:
  // 1. Change `const MOCK_MODE = true;` to `false` at the top of this file.
  // 2. Ensure `API_BASE_URL` points to your actual backend URL.
  // 3. The `apiClient` requests below will then automatically use real endpoints.
  // =========================================================================

  login:               (body) => MOCK_MODE ? mock.login(body)  : apiClient.post('/auth/login', body),
  signup:              (body) => MOCK_MODE ? mock.signup(body) : apiClient.post('/auth/signup', body),
  
  getDashboard:        ()     => MOCK_MODE ? mock.getDashboard() : apiClient.get('/account/dashboard'),
  
  getTransactions:     (p)    => MOCK_MODE ? mock.getTransactions(p) : apiClient.get('/transactions', { params: p }),
  sendMoney:           (body) => MOCK_MODE ? mock.sendMoney(body)    : apiClient.post('/transactions/send', body),
  fundWallet:          (body) => MOCK_MODE ? mock.fundWallet(body)    : apiClient.post('/transactions/fund', body),
  
  buyAirtime:          (body) => MOCK_MODE ? mock.buyAirtime(body)  : apiClient.post('/services/airtime', body),
  buyData:             (body) => MOCK_MODE ? mock.buyData(body)     : apiClient.post('/services/data', body),
  payBill:             (body) => MOCK_MODE ? mock.payBill(body)     : apiClient.post('/services/bills', body),
  fundBetting:         (body) => MOCK_MODE ? mock.fundBetting(body) : apiClient.post('/services/betting', body),
  
  getSmartFeed:        (p)    => MOCK_MODE ? mock.getSmartFeed()          : apiClient.get('/feed', { params: p }),
  checkPaymentRequest: ()     => MOCK_MODE ? mock.checkPaymentRequest()   : apiClient.get('/notifications/payment-requests'),
  approvePayment:      (id)   => MOCK_MODE ? mock.approvePayment(id)      : apiClient.post(`/notifications/payment-requests/${id}/approve`),
  declinePayment:      (id)   => MOCK_MODE ? mock.declinePayment(id)      : apiClient.post(`/notifications/payment-requests/${id}/decline`),
  
  getChatHistory:      ()     => MOCK_MODE ? mock.getChatHistory()   : apiClient.get('/ai/history'),
  sendMessage:         (body) => MOCK_MODE ? mock.sendMessage(body)  : apiClient.post('/ai/message', body),
  
  getAdminDashboard:   ()     => MOCK_MODE ? mock.getAdminDashboard() : apiClient.get('/admin/dashboard'),
  getAdminUsers:       ()     => MOCK_MODE ? mock.getAdminUsers()     : apiClient.get('/admin/users'),
};
