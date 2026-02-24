import axios from 'axios';

// ==========================================
// ⚙️ CONFIGURATION (EDIT THIS SECTION)
// ==========================================
const MOCK_MODE = true; // Set to FALSE when backend is ready
const API_BASE_URL = 'https://api.nexusbank.com/v1'; // Put real backend URL here

// ==========================================
// 1. AXIOS INSTANCE (The Real Connection)
// ==========================================
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
});

// Automatically add Token to every request
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('nexus_token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  },
  (error) => Promise.reject(error)
);

// ==========================================
// 2. MOCK SERVER (Simulates Backend)
// ==========================================
const mockServer = {
  login: (creds) => new Promise((resolve, reject) => {
    setTimeout(() => {
      if (creds.password === 'error') reject({ message: 'Invalid credentials' });
      else resolve({
        data: {
          token: 'mock-jwt-token-xyz',
          user: {
            id: 'USER-001',
            name: 'Reuben', // Matches your screenshot
            phone: '08000000000',
            role: creds.phone === 'admin' ? 'admin' : 'user'
          }
        }
      });
    }, 1500);
  }),

  getDashboard: () => new Promise((resolve) => {
    setTimeout(() => resolve({
      data: {
        account: {
          balance: 336450.97, // Matches screenshot
          number: '0244037192',
          tier: 'Tier 3 Savings'
        },
        feed: [
          { id: 1, type: 'loan', title: 'Student Loan Offer', desc: 'Get ₦50k for books. 0% interest.', color: 'bg-[#A01030] text-white' },
          { id: 2, type: 'alert', title: 'High Spending Alert', desc: "You've spent 80% of your food budget.", color: 'bg-yellow-100 text-yellow-800' }
        ]
      }
    }), 1000);
  }),

  getChatHistory: () => new Promise((resolve) => {
    setTimeout(() => resolve({
      data: [
        { id: 1, sender: 'user', text: 'I noticed a double charge of ₦15,000 for my utility bill payment this morning.' },
        { 
          id: 2, sender: 'ai', type: 'escalation', title: 'ACTION REQUIRED', 
          text: "I've identified two identical transactions to PHCN Utility at 08:45 AM. I can escalate this to our Billing Operations Sector.",
          routeTo: 'Escalate Now'
        }
      ]
    }), 800);
  })
};

// ==========================================
// 3. EXPORTED API METHODS
// ==========================================
export const api = {
  // Auth
  login: (creds) => MOCK_MODE ? mockServer.login(creds) : apiClient.post('/auth/login', creds),
  
  // Data
  getDashboardData: () => MOCK_MODE ? mockServer.getDashboard() : apiClient.get('/user/dashboard'),
  
  // AI Chat
  getChatHistory: () => MOCK_MODE ? mockServer.getChatHistory() : apiClient.get('/ai/chat/history'),
  sendMessage: (msg) => MOCK_MODE ? Promise.resolve({ data: { reply: "AI processing..." } }) : apiClient.post('/ai/chat/send', { message: msg }),
  
  // Admin
  getTicket: (id) => MOCK_MODE ? Promise.resolve({ data: { status: 'In Progress', confidence: 99 } }) : apiClient.get(`/admin/tickets/${id}`),
};

export default apiClient;