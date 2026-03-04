import { create } from 'zustand';
import axiosInstance from '../api/axiosInstance';

export const useStore = create((set) => ({
  // ── State ──────────────────────────────────────────
  user: null,
  accounts: [],
  onboardingData: {},
  customer_id: null,
  account_number: null,
  isLoading: false,
  error: null,

  // ── Auth Actions ───────────────────────────────────
  fetchUser: async () => {
    set({ isLoading: true, error: null });
    try {
      const res = await axiosInstance.get('/users/me');
      set({
        user: res.data,
        accounts: res.data.account_details || [],
        isLoading: false,
      });
      return res.data;
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to load profile';
      set({ error: msg, isLoading: false });
      throw err;
    }
  },

  logout: () => {
    localStorage.removeItem('access_token');
    set({ user: null, accounts: [], error: null });
  },

  // ── Onboarding Actions ─────────────────────────────
  setOnboardingData: (data) => set({ onboardingData: data }),

  createCustomer: async (formData) => {
    set({ isLoading: true, error: null });
    try {
      const response = await axiosInstance.post('/customers', formData);
      set({
        customer_id: response.data.customer_id,
        account_number: response.data.account_number,
        isLoading: false,
      });
      return response.data;
    } catch (err) {
      const message = err.response?.data?.detail || 'Failed to create account';
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  resetOnboarding: () => set({
    onboardingData: {},
    customer_id: null,
    account_number: null,
    error: null,
  }),
}));

