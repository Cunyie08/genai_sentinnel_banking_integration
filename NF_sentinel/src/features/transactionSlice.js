

































































































































import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { api } from '../api/axiosConfig';



export const fetchTransactions = createAsyncThunk(
  'transactions/fetchAll',
  async (params, { rejectWithValue }) => {
    try {
      const response = await api.getTransactions(params);
      // Map backend fields to frontend fields
      const txs = (response.data || []).map(tx => ({
        id:       tx.transaction_id,
        name:     tx.narration || 'Transaction',
        amount:   Number(tx.amount),
        date:     tx.transaction_timestamp,
        ref:      tx.transaction_reference_number,
        type:     tx.transaction_type, // 'credit' | 'debit'
        status:   tx.transaction_status || 'completed',
        // Infer category based on narration keywords
        category: (tx.narration || '').toLowerCase().includes('airtime')  ? 'airtime' :
                  (tx.narration || '').toLowerCase().includes('data')     ? 'data' :
                  (tx.narration || '').toLowerCase().includes('bill')     ? 'bills' :
                  (tx.narration || '').toLowerCase().includes('transfer') ? 'transfer' :
                  (tx.narration || '').toLowerCase().includes('fund')     ? 'fund' :
                  (tx.narration || '').toLowerCase().includes('bet')      ? 'betting' : 'default'
      }));
      return txs;
    } catch (err) {
      return rejectWithValue(err.message || 'Failed to load transactions');
    }
  }
);

export const sendMoney = createAsyncThunk(
  'transactions/send',
  async (data, { rejectWithValue }) => {
    try {
      const response = await api.sendMoney(data);
      return response.data;
    } catch (err) {
      // axios interceptor rejects with response.data (FastAPI returns { detail: "..." })
      const msg = err?.detail || err?.message || JSON.stringify(err) || 'Transfer failed';
      return rejectWithValue(msg);
    }
  }
);

export const fundWallet = createAsyncThunk(
  'transactions/fund',
  async (data, { rejectWithValue }) => {
    try {
      
      const response = await api.fundWallet(data);
      return response.data;
    } catch (err) {
      return rejectWithValue(err.message || 'Funding failed');
    }
  }
);



const transactionSlice = createSlice({
  name: 'transactions',
  initialState: {
    list:       [],
    isLoading:  false,
    isSending:  false,
    isFunding:  false,
    error:      null,
    lastTx:     null,
  },
  reducers: {
    clearLastTx: (state) => { state.lastTx = null; },
    clearError:  (state) => { state.error  = null; },
  },
  extraReducers: (builder) => {
    builder
      
      .addCase(fetchTransactions.pending, (state) => { state.isLoading = true; })
      .addCase(fetchTransactions.fulfilled, (state, action) => {
        state.isLoading = false;
        state.list = action.payload;
      })
      .addCase(fetchTransactions.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload;
      })
      
      
      .addCase(sendMoney.pending, (state) => { state.isSending = true; state.error = null; })
      .addCase(sendMoney.fulfilled, (state, action) => {
        state.isSending = false;
        state.lastTx = action.payload;
        state.list.unshift(action.payload); 
      })
      .addCase(sendMoney.rejected, (state, action) => {
        state.isSending = false;
        state.error = action.payload;
      })
      
      
      .addCase(fundWallet.pending, (state) => { state.isFunding = true; state.error = null; })
      .addCase(fundWallet.fulfilled, (state, action) => {
        state.isFunding = false;
        state.lastTx = action.payload;
        state.list.unshift(action.payload);
      })
      .addCase(fundWallet.rejected, (state, action) => {
        state.isFunding = false;
        state.error = action.payload;
      });
  },
});

export const { clearLastTx, clearError } = transactionSlice.actions;
export default transactionSlice.reducer;
