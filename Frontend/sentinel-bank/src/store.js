// import { configureStore } from '@reduxjs/toolkit';
// import authReducer from './features/authSlice';
// import uiReducer from './features/uiSlice';
// import aiReducer from './features/aiSlice';
// import servicesReducer from './features/servicesSlice';
// import transactionReducer from './features/transactionSlice';

// export const store = configureStore({
//   reducer: {
//     auth: authReducer,
//     ui: uiReducer,
//     ai: aiReducer,
//     services: servicesReducer,
//     transactions: transactionReducer,
//   },
// });



import { configureStore } from '@reduxjs/toolkit';
import authReducer from './features/authSlice';
import uiReducer from './features/uiSlice';
import aiReducer from './features/aiSlice';
import servicesReducer from './features/servicesSlice';
import transactionReducer from './features/transactionSlice';
import accountReducer from './features/accountSlice'; // <--- ADD THIS IMPORT

export const store = configureStore({
  reducer: {
    auth: authReducer,
    ui: uiReducer,
    ai: aiReducer,
    services: servicesReducer,
    transactions: transactionReducer,
    account: accountReducer, // <--- ADD THIS LINE
  },
});