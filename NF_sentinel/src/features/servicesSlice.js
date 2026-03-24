
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { api } from '../api/axiosConfig';


export const buyAirtime = createAsyncThunk(
  'services/buyAirtime',
  async ({ network, phone, amount, account_id }, { rejectWithValue }) => {
    try {
      const response = await api.buyAirtime({
        account_id,
        provider: network,
        phone_number: phone,
        amount
      });
      return response.data;
    } catch (err) {
      return rejectWithValue(err.detail || err.message || 'Airtime purchase failed');
    }
  }
);

export const buyData = createAsyncThunk(
  'services/buyData',
  async ({ network, phone, plan, amount, account_id }, { rejectWithValue }) => {
    try {
      const response = await api.buyData({
        account_id,
        provider: network,
        phone_number: phone,
        data_plan: plan,
        amount
      });
      return response.data;
    } catch (err) {
      return rejectWithValue(err.detail || err.message || 'Data purchase failed');
    }
  }
);

export const payBill = createAsyncThunk(
  'services/payBill',
  async ({ billType, meterNumber, amount, provider, category, account_id }, { rejectWithValue }) => {
    try {
      const response = await api.payBill({
        account_id,
        provider: provider,
        category: category,
        bill_account_number: meterNumber,
        amount
      });
      return response.data;
    } catch (err) {
      return rejectWithValue(err.detail || err.message || 'Bill payment failed');
    }
  }
);

export const fundBetting = createAsyncThunk(
  'services/fundBetting',
  async ({ platform, userId, amount, account_number }, { rejectWithValue }) => {
    try {
      const response = await api.fundBetting({
        provider: platform,
        customer_id: userId,
        amount,
        account_number
      });
      return response.data;
    } catch (err) {
      return rejectWithValue(err.detail || err.message || 'Betting funding failed');
    }
  }
);


const servicesSlice = createSlice({
  name: 'services',
  initialState: {
    isLoading: false,
    error:     null,
    lastResult: null,   
    status:     'idle', 
  },
  reducers: {
    resetService: (state) => {
      state.isLoading  = false;
      state.error      = null;
      state.lastResult = null;
      state.status     = 'idle';
    },
  },
  extraReducers: (builder) => {
    const pending   = (state)          => { state.isLoading = true;  state.error = null; state.status = 'loading'; };
    const fulfilled = (state, action)  => { state.isLoading = false; state.lastResult = action.payload; state.status = 'success'; };
    const rejected  = (state, action)  => { state.isLoading = false; state.error = action.payload; state.status = 'error'; };

    [buyAirtime, buyData, payBill, fundBetting].forEach(thunk => {
      builder
        .addCase(thunk.pending,   pending)
        .addCase(thunk.fulfilled, fulfilled)
        .addCase(thunk.rejected,  rejected);
    });
  },
});

export const { resetService } = servicesSlice.actions;
export default servicesSlice.reducer;