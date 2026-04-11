import { createSlice } from '@reduxjs/toolkit';

const uiSlice = createSlice({
  name: 'ui',
  initialState: {
    isVoiceActive: false,
    showPaymentModal: false,
    showWelcome: false,
    adminActiveTab: 'complaints', 
  },
  reducers: {
    setAdminTab: (state, action) => { 
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
    toggleVoice, 
    triggerPayment, closePayment, 
    triggerWelcome, dismissWelcome,
    setAdminTab 
} = uiSlice.actions;

export default uiSlice.reducer;