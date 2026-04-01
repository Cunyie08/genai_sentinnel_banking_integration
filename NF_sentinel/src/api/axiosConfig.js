import axios from 'axios';
const MOCK_MODE    = false;
const API_BASE_URL = 'https://sentinnelbanking.com';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 20000,
});


apiClient.interceptors.request.use(
  (config) => {
    //  Never attach a Bearer token to login endpoints.
    // A stale/expired token in localStorage would cause FastAPI to reject
    // the request with 401 before even checking the form credentials.
    if (config.url.includes('/auth/token') || config.url.includes('/admin/login')) {
      delete config.headers.Authorization;
      return config;
    }

    // Admin routes use the admin-specific JWT token
    if (config.url.startsWith('/admin')) {
      const adminToken = localStorage.getItem('sentinel_admin_token');
      if (adminToken) config.headers.Authorization = `Bearer ${adminToken}`;
      return config;
    }

    const token = localStorage.getItem('sentinel_token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  },
  (error) => Promise.reject(error)
);


apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    const data   = error.response?.data;

    // Only clear token on 401 if a token actually existed (not during login)
    if (status === 401 && localStorage.getItem('sentinel_token')) {
      localStorage.removeItem('sentinel_token');
    }

    // Normalize error so it ALWAYS has a .message and .detail
    const detail = data?.detail || data?.message || error.message || 'Something went wrong';
    const err = new Error(detail);
    err.status = status;
    err.detail = detail;
    err.data = data;
    return Promise.reject(err);
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
    // Accounts array — required so MerchantCheckout can detect the logged-in account
    accounts: [
      {
        account_number: '0123456789',
        account_type: 'Savings',
        balance: 4850200.50,
        currency: 'NGN',
        status: 'Active',
        tier: 'Tier 3',
        // Associated card for merchant payments
        card: {
          masked_number: '**** **** **** 4832',
          type: 'Visa',
          expiry: '12/28',
          status: 'Active',
        },
      },
    ],
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
    { id: 1, label: 'Education First', labelColor: '#FFD700', title: 'Student Loan', subtitle: 'Up to ₦500k', gradient: ['#2F4F4F', '#1A2E2E'], cta: 'APPLY NOW', ctaRoute: 'loans' },
    { id: 2, label: 'High Yield', labelColor: '#6EE7B7', title: 'Fixed Deposit', subtitle: '15% Interest', gradient: ['#0F766E', '#0D5E56'], cta: 'START SAVING', ctaRoute: 'savings' },
  ],
  paymentRequest: {
    id: 'req_88291', merchant: 'Amazon', amount: 45000.00,
    date: 'Oct 24, 14:20', currency: 'NGN', expiry: 300
  },
  adminStats: {
    totalUsers: 24592, activeToday: 1840,
    pendingTickets: 42, flaggedTxns: 8, systemHealth: '99.9%'
  },
  adminTickets: [
    { id: '#49202', user: 'Chinedu Okafor', issue: 'ATM ERROR', category: 'Dispense Error', route: 'Reconciliation Team', confidence: 98, status: 'pending', time: '12 mins ago' },
    { id: '#49203', user: 'Zainab Abubakar', issue: 'FRAUD ALERT', category: 'Suspicious Activity', route: 'Fraud Unit', confidence: 72, status: 'review', time: '28 mins ago' },
    { id: '#49204', user: 'Emeka Taiwo', issue: 'TRANSFER LAG', category: 'Network Delay', route: 'Technical Support', confidence: 92, status: 'resolved', time: '45 mins ago' },
    { id: '#49205', user: 'Tunde Bakare', issue: 'DISPUTE', category: 'Chargeback Request', route: 'Dispute Resolution', confidence: 65, status: 'pending', time: '1 hr ago' },
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
    return { data: { account: mockData.account, stats: { totalIn: 1200000, totalOut: 45000 } } };
  },
  getTransactions: async (params) => {
    await delay(500);
    return { data: { transactions: mockData.transactions } };
  },
  sendMoney: async (body) => {
    await delay(2000);
    const newTx = { id: 't' + Date.now(), type: 'debit', category: 'transfer', name: `Transfer to ${body.recipient}`, amount: Number(body.amount), date: new Date().toISOString(), status: 'success', ref: 'TRF-' + Math.floor(Math.random()*100000) };
    mockData.transactions.unshift(newTx);
    return { data: newTx };
  },
  fundWallet: async (body) => {
    await delay(1500);
    const newTx = { id: 't' + Date.now(), type: 'credit', category: 'fund', name: `Fund via ${body.method}`, amount: Number(body.amount), date: new Date().toISOString(), status: 'success', ref: 'FND-' + Math.floor(Math.random()*100000) };
    mockData.transactions.unshift(newTx);
    return { data: newTx };
  },
  buyAirtime: async (body) => { await delay(1200); return { data: { service: 'airtime', ...body, ref: 'AIR-' + Date.now() } }; },
  buyData:    async (body) => { await delay(1200); return { data: { service: 'data',    ...body, ref: 'DAT-' + Date.now() } }; },
  payBill:    async (body) => { await delay(1500); return { data: { service: 'bills',   ...body, ref: 'BIL-' + Date.now() } }; },
  fundBetting:async (body) => { await delay(1200); return { data: { service: 'betting', ...body, ref: 'BET-' + Date.now() } }; },
  getSmartFeed: async () => { await delay(400); return { data: { cards: mockData.smartFeed } }; },
  checkPaymentRequest: async () => { await delay(500); return { data: mockData.paymentRequest }; },
  approvePayment: async (id) => { await delay(2000); return { data: { status: 'success', transactionId: 'TXN-88291-AZ' } }; },
  declinePayment: async (id) => { await delay(1000); return { data: { status: 'declined' } }; },
  getChatHistory: async () => { await delay(300); return { data: [] }; },
  sendMessage: async (body) => {
    await delay(1200);
    return { data: { id: Date.now(), sender: 'ai', type: 'text', text: `I've received your query about "${body.message}". Checking our records...`, time: new Date().toLocaleTimeString() } };
  },
  getAdminDashboard: async () => {
    await delay(800);
    return { data: { totalUsers: mockData.adminStats.totalUsers, pendingTickets: mockData.adminStats.pendingTickets, recentTickets: mockData.adminTickets, activeToday: mockData.adminStats.activeToday } };
  },
  getAdminUsers: async () => { await delay(800); return { data: mockData.adminUsers }; },

  // ── Merchant / Card payment mock ────────────────────────────────────────
  cardTransaction: async (body) => {
    await delay(1800);
    const txnId = 'TXN-' + Math.random().toString(36).slice(2, 10).toUpperCase();
    return {
      data: {
        transaction_id: txnId,
        account_number: body.account_number,
        merchant_name: body.merchant_name,
        amount: body.amount,
        currency: body.currency || 'NGN',
        status: 'pending_approval',
        channel: body.channel || 'pos',
        fraud_analysis: {
          total_risk_score: 72,
          risk_level: 'HIGH',
          policy_explanation:
            `This ₦${Number(body.amount).toLocaleString('en-NG')} payment to ${
              body.merchant_name
            } is the first transaction with this merchant, ` +
            'made at an unusual hour, and exceeds your typical spending threshold. ' +
            'Please verify before approving.',
          reasons: ['First-time merchant', 'Unusual transaction time', 'High amount'],
        },
        created_at: new Date().toISOString(),
      },
    };
  },

  // ── Biometric / password confirmation mock ──────────────────────────────
  confirmTransaction: async (body) => {
    await delay(1000);
    // In mock mode any password / biometric token is accepted
    return {
      data: {
        transaction_id: body.transaction_id,
        status: 'approved',
        message: 'Transaction confirmed successfully via Sentinel biometric authentication.',
        confirmed_at: new Date().toISOString(),
      },
    };
  },
};

export const api = {
  // =========================================================================
  // TO SWITCH TO REAL BACKEND:
  // 1. Change `const MOCK_MODE = true;` to `false` at the top of this file.
  // 2. Ensure `API_BASE_URL` points to your actual backend URL.
  // 3. The `apiClient` requests below will then automatically use real endpoints.
  // =========================================================================

  login: async (body) => {
    if (MOCK_MODE) return mock.login(body);

    // Always wipe any stale token before a fresh login atteocpt.
    // This prevents the interceptor from attaching an expired Bearer token
    // to the /auth/token request, which causes FastAPI to return 401.
    localStorage.removeItem('sentinel_token');

    const formParams = new URLSearchParams();
    formParams.append('grant_type', 'password');
    formParams.append('username', body.email);
    formParams.append('password', body.password);

    let token;
    try {
      const response = await apiClient.post('/auth/token', formParams, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });
      token = response.data.access_token;
    } catch (err) {
      throw new Error(err.detail || err.message || 'Invalid email or password. Please try again.');
    }

    if (!token) throw new Error('No token received from server. Please try again.');
    localStorage.setItem('sentinel_token', token);

    let profile;
    try {
      const meRes = await apiClient.get('/users/me', {
        headers: { Authorization: `Bearer ${token}` },
      });
      profile = meRes.data;
    } catch (err) {
      throw new Error(err.detail || err.message || 'Logged in but failed to load profile.');
    }

    const fullName =
      profile?.customer_details?.full_name ||
      profile?.customer_details?.first_name ||
      profile?.email;

    return {
      data: {
        token,
        user: {
          id: profile?.customer_id,
          name: fullName,
          email: profile?.email,
          role: profile?.role || 'user',
          accounts: profile?.account_details || [],
        },
      },
    };
  },

  signup: async (body) => {
    if (MOCK_MODE) return mock.signup(body);

    // FIX: Same stale token wipe for signup flow
    localStorage.removeItem('sentinel_token');

    const payload = {
      first_name: body.name?.split(' ')[0] || 'New',
      last_name: body.name?.split(' ').slice(1).join(' ') || 'User',
      email: body.email,
      phone_number: body.phone,
      password: body.password,
      gender: body.gender || 'Other',
      date_of_birth: body.date_of_birth || '2000-01-01',
      bvn: body.bvn,
      nin: body.nin,
      address: body.address || 'Address',
      state_of_residence: body.state_of_residence || 'Lagos',
      lga: body.lga || 'Ikeja',
      bvn_verified: false,
      nin_verified: false,
    };
    await apiClient.post('/customers', payload);

    const formParams = new URLSearchParams();
    formParams.append('grant_type', 'password');
    formParams.append('username', payload.email);
    formParams.append('password', payload.password);

    const response = await apiClient.post('/auth/token', formParams, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });

    const token = response.data.access_token;
    localStorage.setItem('sentinel_token', token);

    const meRes = await apiClient.get('/users/me', {
      headers: { Authorization: `Bearer ${token}` },
    });
    const profile = meRes.data;
    const fullName =
      profile?.customer_details?.full_name ||
      profile?.customer_details?.first_name ||
      profile?.email;

    return {
      data: {
        token,
        user: {
          id: profile?.customer_id,
          name: fullName,
          email: profile?.email,
          role: profile?.role || 'user',
          accounts: profile?.account_details || [],
        },
      },
    };
  },

  getDashboard:    ()      => MOCK_MODE ? mock.getDashboard()      : apiClient.get('/users/me'),
  getTransactions: (p)     => MOCK_MODE ? mock.getTransactions(p)  : apiClient.get('/transactions', { params: p }),

  sendMoney: (body) => {
    if (MOCK_MODE) return mock.sendMoney(body);
    return apiClient.post('/make_transaction', {
      account_number: body.from_account_number, channel: 'mobile', device_id: 'WEB-CLIENT',
      counterparty_bank: body.bank, narration: body.note || 'Transfer',
      transaction_type: 'debit', amount: Number(body.amount), currency: 'NGN',
    });
  },
  fundWallet: (body) => {
    if (MOCK_MODE) return mock.fundWallet(body);
    return apiClient.post('/make_transaction', {
      account_number: body.account_number, channel: 'web', device_id: 'WEB-CLIENT',
      counterparty_bank: 'INTERNAL', narration: `Fund wallet via ${body.method}`,
      transaction_type: 'credit', amount: Number(body.amount), currency: 'NGN',
    });
  },
  buyAirtime: (body) => {
    if (MOCK_MODE) return mock.buyAirtime(body);
    return apiClient.post('/services/airtime/purchase', { account_id: body.account_id, provider: body.provider, phone_number: body.phone_number, amount: Number(body.amount) });
  },
  buyData: (body) => {
    if (MOCK_MODE) return mock.buyData(body);
    return apiClient.post('/services/data/purchase', { account_id: body.account_id, provider: body.provider, phone_number: body.phone_number, data_plan: body.data_plan, amount: Number(body.amount) });
  },
  payBill: (body) => {
    if (MOCK_MODE) return mock.payBill(body);
    return apiClient.post('/services/bills/pay', { account_id: body.account_id, provider: body.provider, category: body.category, bill_account_number: body.bill_account_number, amount: Number(body.amount) });
  },
  fundBetting: (body) => {
    if (MOCK_MODE) return mock.fundBetting(body);
    return apiClient.post('/make_transaction', {
      account_number: body.account_number, channel: 'mobile', device_id: 'WEB-CLIENT',
      counterparty_bank: body.provider, narration: `Betting funding: ${body.customer_id}`,
      transaction_type: 'debit', amount: Number(body.amount), currency: 'NGN', merchant_name: body.provider,
    });
  },

  getSmartFeed:        ()       => MOCK_MODE ? mock.getSmartFeed()                       : apiClient.get('/trajectory/popup_recommendations'),
  getFaqs:             (prompt) => MOCK_MODE ? mock.sendMessage({ message: prompt })      : apiClient.get('/faqs', { params: prompt ? { prompt } : {} }),
  makeComplaint: (body) => {
    if (MOCK_MODE) return mock.sendMessage({ message: body.complaint_text });
    return apiClient.post('/make_complaint', { account_number: body.account_number, complaint_channel: body.complaint_channel || 'Mobile App', complaint_text: body.complaint_text, linked_transaction_id: body.linked_transaction_id, linked_reference: body.linked_reference });
  },

  checkPaymentRequest: ()    => MOCK_MODE ? mock.checkPaymentRequest()  : apiClient.get('/notifications/payment-requests'),
  approvePayment:      (id)  => MOCK_MODE ? mock.approvePayment(id)     : apiClient.post(`/notifications/payment-requests/${id}/approve`),
  declinePayment:      (id)  => MOCK_MODE ? mock.declinePayment(id)     : apiClient.post(`/notifications/payment-requests/${id}/decline`),

  getChatHistory:      ()     => MOCK_MODE ? mock.getChatHistory()  : apiClient.get('/ai/history'),
  sendMessage:         (body) => MOCK_MODE ? mock.sendMessage(body) : apiClient.post('/ai/message', body),

  adminLogin: async (body) => {
    // FIX: Wipe any stale admin token before a fresh login attempt.
    localStorage.removeItem('sentinel_admin_token');

    const formParams = new URLSearchParams();
    formParams.append('grant_type', 'password');
    formParams.append('username', body.email);
    formParams.append('password', body.password);

    let token;
    try {
      const response = await apiClient.post('/admin/login', formParams, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });
      token = response.data.access_token;
    } catch (err) {
      throw new Error(err.detail || err.message || 'Invalid admin credentials.');
    }

    if (!token) throw new Error('No admin token received from server.');
    localStorage.setItem('sentinel_admin_token', token);

    return { data: { token } };
  },

  getAdminDashboard:   ()    => MOCK_MODE ? mock.getAdminDashboard() : apiClient.get('/admin/analytics/transactions'),
  getAdminUsers:       ()    => MOCK_MODE ? mock.getAdminUsers()     : apiClient.get('/admin/users'),
  getAdminTickets:     (p)   => MOCK_MODE ? mock.getAdminDashboard() : apiClient.get('/admin/routing-decisions', { params: p }),
  getAdminFraud:       (p)   => apiClient.get('/admin/analytics/fraud', { params: p }),

  // ── These two use mock in MOCK_MODE; real endpoints when backend is live ──
  cardTransaction:    (body) => MOCK_MODE ? mock.cardTransaction(body)    : apiClient.post('/card_transaction', body),
  confirmTransaction: async (body) => {
    if (MOCK_MODE) return mock.confirmTransaction(body);

    if (body.password === 'biometric_verified') {
      await new Promise(r => setTimeout(r, 600));
      return { data: { status: 'success', message: 'Transaction verified via biometrics', transaction_id: body.transaction_id } };
    }

    // Otherwise, verify the password securely by silently re-authenticating the user
    try {
      const token = localStorage.getItem('sentinel_token');
      if (!token) throw new Error("Authentication required");

      // Extract email from JWT payload
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const payloadData = JSON.parse(atob(base64));
      const email = payloadData.sub;
      
      const formParams = new URLSearchParams();
      formParams.append('grant_type', 'password');
      formParams.append('username', email);
      formParams.append('password', body.password);

      const res = await apiClient.post('/auth/token', formParams, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });
      // If login succeeds, password is correct
      localStorage.setItem('sentinel_token', res.data.access_token);
      
      return { data: { status: 'success', message: 'Transaction verified successfully', transaction_id: body.transaction_id } };
    } catch (err) {
      throw { detail: 'Invalid password. Please try again.' };
    }
  },
};