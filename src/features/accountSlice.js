import { createSlice } from '@reduxjs/toolkit';

const accountSlice = createSlice({
  name: 'account',
  initialState: {
    details: {
      balance: 336450.97,
      number: '0244037192',
      status: 'Active',
      tier: 'Tier 3'
    }
  },
  reducers: {
    updateBalance: (state, action) => {
      state.details.balance = action.payload;
    }
  }
});

export const { updateBalance } = accountSlice.actions;
export default accountSlice.reducer;