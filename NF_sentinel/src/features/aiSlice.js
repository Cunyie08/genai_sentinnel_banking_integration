import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { api } from '../api/axiosConfig';

export const sendMessage = createAsyncThunk(
  'ai/sendMessage',
  async (text, { rejectWithValue }) => {
    try {
      const response = await api.sendMessage({ message: text });
      return response.data;
    } catch (err) { return rejectWithValue(err.message); }
  }
);

const aiSlice = createSlice({
  name: 'ai',
  initialState: {
    chatHistory: [],
    adminTickets: [],
    isLoading: false,
  },
  reducers: {
    addChatMessage: (state, action) => { 
      state.chatHistory.push(action.payload); 
    },
    createTicket: (state, action) => { 
      state.adminTickets.unshift(action.payload); 
    },
    initChatGreeting: (state, action) => {
      if (state.chatHistory.length === 0) {
        const userName = action.payload || 'there';
        state.chatHistory = [
          {
            id: 1,
            sender: 'ai',
            type: 'options',
            text: `Hello ${userName}! How can I help you with your account today? You can ask about:`,
            options: ['Transaction Discrepancy', 'Card Issues & Limits', 'Report Fraudulent Activity'],
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          }
        ];
      }
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendMessage.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(sendMessage.fulfilled, (state, action) => {
        state.isLoading = false;
        state.chatHistory.push(action.payload);
      })
      .addCase(sendMessage.rejected, (state, action) => {
        state.isLoading = false;
        state.chatHistory.push({
          id: Date.now(),
          sender: 'ai',
          type: 'text',
          text: 'Sorry, I could not process your request. Please try again in a moment.',
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        });
      });
  }
});

export const { addChatMessage, createTicket, initChatGreeting, submitComplaint } = aiSlice.actions;
export default aiSlice.reducer;