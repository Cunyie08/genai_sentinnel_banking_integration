// // src/features/transactionSlice.js
// import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';

// // ── Mock transaction history ──────────────────────────────────────────────
// const MOCK_TRANSACTIONS = [
//   { id: 't1', type: 'debit',  category: 'airtime',   name: 'MTN Airtime',     amount: 500,     date: '2025-02-24T14:14:00', status: 'success', ref: 'TXN001' },
//   { id: 't2', type: 'credit', category: 'transfer',  name: 'Transfer In',     amount: 50000,   date: '2025-02-24T11:03:00', status: 'success', ref: 'TXN002' },
//   { id: 't3', type: 'debit',  category: 'bills',     name: 'DSTV Bill',       amount: 8500,    date: '2025-02-23T09:00:00', status: 'success', ref: 'TXN003' },
//   { id: 't4', type: 'debit',  category: 'data',      name: 'Data Bundle',     amount: 2000,    date: '2025-02-22T09:00:00', status: 'success', ref: 'TXN004' },
//   { id: 't5', type: 'credit', category: 'salary',    name: 'Salary Credit',   amount: 320000,  date: '2025-02-20T00:01:00', status: 'success', ref: 'TXN005' },
//   { id: 't6', type: 'debit',  category: 'transfer',  name: 'Transfer to Ade', amount: 15000,   date: '2025-02-19T16:30:00', status: 'success', ref: 'TXN006' },
//   { id: 't7', type: 'debit',  category: 'betting',   name: 'Bet9ja Deposit',  amount: 3000,    date: '2025-02-18T20:00:00', status: 'success', ref: 'TXN007' },
//   { id: 't8', type: 'debit',  category: 'bills',     name: 'EKEDC Prepaid',   amount: 5000,    date: '2025-02-17T10:00:00', status: 'success', ref: 'TXN008' },
// ];

// // ── Async thunks ──────────────────────────────────────────────────────────
// export const fetchTransactions = createAsyncThunk(
//   'transactions/fetchAll',
//   async () => {
//     await new Promise(res => setTimeout(res, 800));
//     return MOCK_TRANSACTIONS;
//   }
// );

// export const sendMoney = createAsyncThunk(
//   'transactions/send',
//   async ({ recipient, amount, note }, { rejectWithValue }) => {
//     try {
//       await new Promise(res => setTimeout(res, 1500));
//       if (amount <= 0) throw new Error('Invalid amount');
//       return {
//         id:        't' + Date.now(),
//         type:      'debit',
//         category:  'transfer',
//         name:      'Transfer to ' + recipient,
//         amount:    Number(amount),
//         date:      new Date().toISOString(),
//         status:    'success',
//         ref:       'TXN' + Math.floor(Math.random() * 100000),
//         note,
//       };
//     } catch (err) {
//       return rejectWithValue(err.message);
//     }
//   }
// );

// export const fundWallet = createAsyncThunk(
//   'transactions/fund',
//   async ({ amount, method }, { rejectWithValue }) => {
//     try {
//       await new Promise(res => setTimeout(res, 1200));
//       return {
//         id:       't' + Date.now(),
//         type:     'credit',
//         category: 'fund',
//         name:     'Wallet Funding via ' + method,
//         amount:   Number(amount),
//         date:     new Date().toISOString(),
//         status:   'success',
//         ref:      'TXN' + Math.floor(Math.random() * 100000),
//       };
//     } catch (err) {
//       return rejectWithValue(err.message);
//     }
//   }
// );

// // ── Slice ─────────────────────────────────────────────────────────────────
// const transactionSlice = createSlice({
//   name: 'transactions',
//   initialState: {
//     list:       [],
//     isLoading:  false,
//     isSending:  false,
//     isFunding:  false,
//     error:      null,
//     lastTx:     null,   // most recent completed transaction
//   },
//   reducers: {
//     clearLastTx: (state) => { state.lastTx = null; },
//     clearError:  (state) => { state.error  = null; },
//   },
//   extraReducers: (builder) => {
//     builder
//       // Fetch
//       .addCase(fetchTransactions.pending,   (state) => { state.isLoading = true;  })
//       .addCase(fetchTransactions.fulfilled, (state, action) => {
//         state.isLoading = false;
//         state.list      = action.payload;
//       })
//       .addCase(fetchTransactions.rejected,  (state, action) => {
//         state.isLoading = false;
//         state.error     = action.payload;
//       })
//       // Send
//       .addCase(sendMoney.pending,   (state) => { state.isSending = true; state.error = null; })
//       .addCase(sendMoney.fulfilled, (state, action) => {
//         state.isSending = false;
//         state.lastTx    = action.payload;
//         state.list.unshift(action.payload);
//       })
//       .addCase(sendMoney.rejected,  (state, action) => {
//         state.isSending = false;
//         state.error     = action.payload;
//       })
//       // Fund
//       .addCase(fundWallet.pending,   (state) => { state.isFunding = true; state.error = null; })
//       .addCase(fundWallet.fulfilled, (state, action) => {
//         state.isFunding = false;
//         state.lastTx    = action.payload;
//         state.list.unshift(action.payload);
//       })
//       .addCase(fundWallet.rejected,  (state, action) => {
//         state.isFunding = false;
//         state.error     = action.payload;
//       });
//   },
// });

// export const { clearLastTx, clearError } = transactionSlice.actions;
// export default transactionSlice.reducer;







import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { api } from '../api/axiosConfig';

// ── Async Thunks ──────────────────────────────────────────────────────────

export const fetchTransactions = createAsyncThunk(
  'transactions/fetchAll',
  async (params, { rejectWithValue }) => {
    try {
      const response = await api.getTransactions(params);
      return response.data.transactions;
    } catch (err) {
      return rejectWithValue(err.message || 'Failed to load transactions');
    }
  }
);

export const sendMoney = createAsyncThunk(
  'transactions/send',
  async (data, { rejectWithValue }) => {
    try {
      // data: { recipient, amount, note, ... }
      const response = await api.sendMoney(data);
      return response.data;
    } catch (err) {
      return rejectWithValue(err.message || 'Transfer failed');
    }
  }
);

export const fundWallet = createAsyncThunk(
  'transactions/fund',
  async (data, { rejectWithValue }) => {
    try {
      // data: { amount, method }
      const response = await api.fundWallet(data);
      return response.data;
    } catch (err) {
      return rejectWithValue(err.message || 'Funding failed');
    }
  }
);

// ── Slice ─────────────────────────────────────────────────────────────────

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
      // Fetch History
      .addCase(fetchTransactions.pending, (state) => { state.isLoading = true; })
      .addCase(fetchTransactions.fulfilled, (state, action) => {
        state.isLoading = false;
        state.list = action.payload;
      })
      .addCase(fetchTransactions.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload;
      })
      
      // Send Money
      .addCase(sendMoney.pending, (state) => { state.isSending = true; state.error = null; })
      .addCase(sendMoney.fulfilled, (state, action) => {
        state.isSending = false;
        state.lastTx = action.payload;
        state.list.unshift(action.payload); // Add new tx to top of list
      })
      .addCase(sendMoney.rejected, (state, action) => {
        state.isSending = false;
        state.error = action.payload;
      })
      
      // Fund Wallet
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