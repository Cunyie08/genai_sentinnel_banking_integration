import { createSlice } from '@reduxjs/toolkit';

const uiSlice = createSlice({
  name: 'ui',
  initialState: {
    activeRoute: 'welcome',
    isVoiceActive: false,
    showPaymentModal: false,
    showWelcome: false,
    adminActiveTab: 'complaints', // <--- NEW: Tracks Admin Sidebar selection
  },
  reducers: {
    setRoute: (state, action) => {
      state.activeRoute = action.payload;
      window.scrollTo(0, 0);
    },
    setAdminTab: (state, action) => { // <--- NEW ACTION
      state.adminActiveTab = action.payload;
    },
    toggleVoice: (state, action) => {
      state.isVoiceActive = action.payload !== undefined ? action.payload : !state.isVoiceActive;
    },
    triggerPayment: (state) => { state.showPaymentModal = true; },
    closePayment: (state) => { state.showPaymentModal = false; },
    triggerWelcome: (state) => { state.showWelcome = true; },
    dismissWelcome: (state) => { state.showWelcome = false; }
  },
});

export const { 
    setRoute, toggleVoice, 
    triggerPayment, closePayment, 
    triggerWelcome, dismissWelcome,
    setAdminTab // Export this
} = uiSlice.actions;

export default uiSlice.reducer;