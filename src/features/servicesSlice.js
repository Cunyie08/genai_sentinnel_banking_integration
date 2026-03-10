
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';


export const buyAirtime = createAsyncThunk(
  'services/buyAirtime',
  async ({ network, phone, amount }, { rejectWithValue }) => {
    try {
      await new Promise(res => setTimeout(res, 1400));
      if (!phone || !amount) throw new Error('Phone and amount are required');
      return { service: 'airtime', network, phone, amount: Number(amount), ref: 'AIR' + Date.now() };
    } catch (err) { return rejectWithValue(err.message); }
  }
);

export const buyData = createAsyncThunk(
  'services/buyData',
  async ({ network, phone, plan }, { rejectWithValue }) => {
    try {
      await new Promise(res => setTimeout(res, 1400));
      if (!phone || !plan) throw new Error('Phone and plan are required');
      return { service: 'data', network, phone, plan, ref: 'DAT' + Date.now() };
    } catch (err) { return rejectWithValue(err.message); }
  }
);

export const payBill = createAsyncThunk(
  'services/payBill',
  async ({ billType, meterNumber, amount }, { rejectWithValue }) => {
    try {
      await new Promise(res => setTimeout(res, 1600));
      if (!meterNumber || !amount) throw new Error('Meter number and amount required');
      return { service: 'bills', billType, meterNumber, amount: Number(amount), ref: 'BIL' + Date.now() };
    } catch (err) { return rejectWithValue(err.message); }
  }
);

export const fundBetting = createAsyncThunk(
  'services/fundBetting',
  async ({ platform, userId, amount }, { rejectWithValue }) => {
    try {
      await new Promise(res => setTimeout(res, 1400));
      if (!userId || !amount) throw new Error('User ID and amount required');
      return { service: 'betting', platform, userId, amount: Number(amount), ref: 'BET' + Date.now() };
    } catch (err) { return rejectWithValue(err.message); }
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