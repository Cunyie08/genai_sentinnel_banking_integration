import { createSlice } from '@reduxjs/toolkit';

const aiSlice = createSlice({
  name: 'ai',
  initialState: {
    // EXACT CONVERSATION FROM SCREENSHOT
    chatHistory: [
      { 
        id: 1, 
        sender: 'ai', 
        type: 'options', 
        text: 'Hello Lukman! How can I help you with your account today? You can ask about:', 
        options: ['Transaction Discrepancy', 'Card Issues & Limits', 'Report Fraudulent Activity'],
        time: '12:59 PM'
      },
      {
        id: 2,
        sender: 'user',
        type: 'text',
        text: 'I noticed a double charge of ₦15,000 for my utility bill payment this morning. Can you check this for me?',
        time: '1:00 PM • Read'
      },
      {
        id: 3,
        sender: 'ai',
        type: 'escalation',
        title: 'ACTION REQUIRED',
        text: "I've identified two identical transactions to PHCN Utility at 08:45 AM. I can escalate this to our Billing Operations Sector for immediate reversal.",
        routeTo: 'Escalate Now',
        time: '1:01 PM'
      }
    ],
    adminTickets: [],
  },
  reducers: {
    addChatMessage: (state, action) => { state.chatHistory.push(action.payload); },
    createTicket: (state, action) => { state.adminTickets.unshift(action.payload); },
  }
});

export const { addChatMessage, createTicket } = aiSlice.actions;
export default aiSlice.reducer;