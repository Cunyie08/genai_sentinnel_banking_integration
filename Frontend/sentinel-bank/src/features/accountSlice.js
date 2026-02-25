
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { api } from '../api/axiosConfig';

// Fetch Dashboard Data (Balance, Account Info, Stats)
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
      number: '....',
      status: 'Active',
      tier: 'Tier 1'
    },
    stats: null,
    isLoading: false,
    error: null
  },
  reducers: {
    // Optimistic update if needed
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
        // Map API response structure to state
        state.details = action.payload.account;
        state.stats = action.payload.stats;
      })
      .addCase(fetchDashboard.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload;
      });
  }
});

export const { updateBalance } = accountSlice.actions;
export default accountSlice.reducer;