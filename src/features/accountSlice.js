
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { api } from '../api/axiosConfig';


export const fetchDashboard = createAsyncThunk(
  'account/fetchDashboard',
  async (_, { rejectWithValue }) => {
    try {
      const response = await api.getDashboard();
      return response.data;
    } catch (err) {
      return rejectWithValue(err.message || 'Failed to fetch dashboard');
    }
  }
);

const accountSlice = createSlice({
  name: 'account',
  initialState: {
    details: {
      balance: 0,
      number: '',
      status: '',
      tier: ''
    },
    stats: null,
    isLoading: false,
    error: null
  },
  reducers: {
    
    updateBalance: (state, action) => {
      state.details.balance = action.payload;
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchDashboard.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(fetchDashboard.fulfilled, (state, action) => {
        state.isLoading = false;
        // The real backend returns account_details array, while mock returns .account
        const acc = action.payload.account || (action.payload.account_details && action.payload.account_details[0]);
        if (acc) {
          state.details = {
            balance: acc.balance ?? acc.current_balance ?? 0,
            number:  acc.account_number || '....',
            status:  acc.status || 'Active',
            tier:    acc.tier || 'Tier 3'
          };
        }
        state.stats = action.payload.stats || null;
      })
      .addCase(fetchDashboard.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload;
      });
  }
});

export const { updateBalance } = accountSlice.actions;
export default accountSlice.reducer;