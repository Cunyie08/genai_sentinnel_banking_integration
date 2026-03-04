# 🏦 Sentinel Bank — Project Completion Guide

> **Status:** Auth flow complete · Dashboard & protected pages remaining  
> **Stack:** FastAPI + PostgreSQL (Backend) · React 19 + Tailwind v4 + Zustand (Frontend)

---

## 📋 Table of Contents

1. [Project Structure](#project-structure)
2. [Current State — What's Done](#current-state--whats-done)
3. [Frontend Pages To Build](#frontend-pages-to-build)
4. [Full Backend API Reference](#full-backend-api-reference)
5. [Frontend Architecture Rules](#frontend-architecture-rules)
6. [Security Checklist](#security-checklist)
7. [Axios & Auth Setup](#axios--auth-setup)
8. [Zustand Store — How to Extend](#zustand-store--how-to-extend)
9. [Protected Routes (PrivateRoute)](#protected-routes-privateroute)
10. [Step-by-Step Completion Plan](#step-by-step-completion-plan)

---

## Project Structure

```
Sentinnel_bank_project/
├── Backend/
│   ├── app.py              # Main FastAPI app — all routers mounted here
│   ├── api.py              # Auth endpoints (/auth/*)
│   ├── services.py         # Quick services (airtime, data, bills)
│   ├── cards.py            # Card management
│   ├── notifications.py    # In-app notifications
│   ├── admin.py            # Admin panel endpoints
│   ├── audit.py            # Audit logs
│   ├── settings_routes.py  # User settings
│   ├── models.py           # SQLAlchemy ORM models
│   ├── schemas.py          # Pydantic request/response schemas
│   ├── auth.py             # JWT helpers (create_access_token, verify etc.)
│   ├── middleware.py       # get_current_user dependency
│   └── database.py         # DB engine & session
│
└── Frontend/src/
    ├── App.jsx             # Router
    ├── App.css             # Tailwind v4 + theme tokens
    ├── main.jsx            # Entry point (imports App.css)
    ├── api/
    │   └── axiosInstance.js   # Axios with JWT interceptor
    ├── store/
    │   └── useStore.js        # Zustand global state
    └── pages/
        ├── Onboarding.jsx  ✅ Done
        ├── Signup.jsx      ✅ Done
        ├── Login.jsx       ✅ Done
        ├── OTPVerify.jsx   ✅ Done
        ├── Dashboard.jsx   ❌ To Build
        ├── TransactionHistory.jsx  ❌ To Build
        ├── Transfer.jsx    ❌ To Build
        ├── Cards.jsx       ❌ To Build
        ├── Services.jsx    ❌ To Build
        ├── Profile.jsx     ❌ To Build
        ├── Notifications.jsx ❌ To Build
        ├── Settings.jsx    ❌ To Build
        └── ForgotPassword.jsx ❌ To Build
```

---

## Current State — What's Done

| Page       | Route         | Backend Connected | Notes                            |
| ---------- | ------------- | :---------------: | -------------------------------- |
| Onboarding | `/onboarding` |        ✅         | `POST /customers`                |
| Signup     | `/signup`     |        ✅         | `POST /auth/register` → OTP      |
| OTP Verify | `/verify-otp` |        ✅         | `POST /auth/verify-otp` + resend |
| Login      | `/login`      |        ✅         | `POST /auth/token` → JWT saved   |

---

## Frontend Pages To Build

### 1. `Dashboard.jsx` — `/dashboard`

**What it shows:**

- User full name, account number, current balance
- Recent 5 transactions
- Quick actions: Transfer, Airtime, Data, Bills
- AI product recommendation popup (if applicable)

**API calls on mount:**

```js
// 1. Get user profile + account details
GET /users/me
→ { email, role, customer_details: { first_name, last_name }, account_details: [{ account_number, balance }] }

// 2. Get AI popup recommendations (non-blocking)
GET /trajectory/popup_recommendations
→ { cards: [{ title, subtitle, cta, gradient }] }
```

**Zustand actions needed:**

```js
fetchUser(); // hits GET /users/me, stores user + accounts
```

---

### 2. `TransactionHistory.jsx` — `/history`

**What it shows:** Paginated list of transactions with filters (date, type, amount).

**API:**

```js
GET / services / transactions; // check app.py for exact path
```

> ⚠️ Check `app.py` for the transactions list endpoint — it may be under `/accounts/{account_id}/transactions`.

---

### 3. `Transfer.jsx` — `/transfer`

**What it shows:** Form to transfer money to another account.

**API:**

```js
// Internal (within Sentinel)
POST /services/internal-transfer
{ from_account_number, to_account_number, amount, narration }

// External (debit ledger + fraud check)
POST /make_transaction
{ account_number, channel, device_id, counterparty_bank, narration,
  transaction_type: "debit", amount, currency, merchant_name }
```

**Security:** Never expose raw account number in URL. Always validate `amount > 0` client-side before sending.

---

### 4. `Cards.jsx` — `/cards`

**What it shows:** User's virtual/physical cards, freeze/activate toggle, set daily limit.

**API:**

```js
GET    /cards/                          // List all cards
POST   /cards/request                   // { account_id, card_type: "Debit"|"Credit" }
GET    /cards/:cardId/details
PATCH  /cards/:cardId/freeze
PATCH  /cards/:cardId/activate
POST   /cards/:cardId/set-limit         // { daily_limit: number }
```

---

### 5. `Services.jsx` — `/services`

**What it shows:** Tabbed view for Airtime, Data, Bill payment.

**API:**

```js
// Airtime
GET / services / airtime / providers;
POST / services / airtime / purchase; // { account_id, provider, phone_number, amount }

// Data
GET / services / data / providers;
POST / services / data / purchase; // { account_id, provider, phone_number, data_plan, amount }

// Bills
GET / services / bills / categories;
GET / services / bills / providers;
POST / services / bills / pay; // { account_id, provider, category, bill_account_number, amount }
```

---

### 6. `Profile.jsx` — `/profile`

**API:**

```js
GET / users / me;
PATCH / users / update - profile; // { first_name, last_name, phone_number, telco_provider }
PATCH / auth / change - password; // { current_password, new_password }
```

---

### 7. `Notifications.jsx` — `/notifications`

**API:**

```js
GET    /notifications/
PATCH  /notifications/:id/read
DELETE /notifications/:id
```

---

### 8. `Settings.jsx` — `/settings`

**API:**

```js
GET / users / settings;
PATCH / users / update - preferences; // { theme, language, notify_transactions, notify_promotions }
```

---

### 9. `ForgotPassword.jsx` — `/forgot-password`

**Flow:**

1. User enters email → `POST /auth/forgot-password` → email sent with reset link
2. Link opens `/auth/reset-password?token=...` (handled by backend, returns HTML)

**API:**

```js
POST / auth / forgot - password; // { email }
POST / auth / reset - password; // { token, new_password }
```

---

## Full Backend API Reference

### 🔐 Authentication (`/auth/*`)

| Method | Endpoint                | Auth | Body                                       |
| ------ | ----------------------- | ---- | ------------------------------------------ |
| POST   | `/auth/register`        | ❌   | `{ email, password }`                      |
| POST   | `/auth/token`           | ❌   | Form: `username`, `password` (url-encoded) |
| POST   | `/auth/verify-otp`      | ❌   | `{ email, otp_code, purpose }`             |
| POST   | `/auth/resend-otp`      | ❌   | `{ email }`                                |
| POST   | `/auth/forgot-password` | ❌   | `{ email }`                                |
| POST   | `/auth/reset-password`  | ❌   | `{ token, new_password }`                  |
| PATCH  | `/auth/change-password` | ✅   | `{ current_password, new_password }`       |
| POST   | `/auth/refresh`         | ✅   | —                                          |
| POST   | `/auth/logout`          | ✅   | —                                          |

> ⚠️ **`/auth/token` uses `application/x-www-form-urlencoded`**, NOT JSON!

```js
// Correct way to call login:
const params = new URLSearchParams();
params.append("username", email);
params.append("password", password);
await axiosInstance.post("/auth/token", params, {
  headers: { "Content-Type": "application/x-www-form-urlencoded" },
});
```

---

### 👤 User Profile

| Method | Endpoint                    | Auth | Description                    |
| ------ | --------------------------- | ---- | ------------------------------ |
| GET    | `/users/me`                 | ✅   | Full profile + accounts        |
| PATCH  | `/users/update-profile`     | ✅   | Update name / phone            |
| GET    | `/users/settings`           | ✅   | Get preferences                |
| PATCH  | `/users/update-preferences` | ✅   | Theme, language, notifications |

---

### 🏛️ Customers & Accounts

| Method | Endpoint                      | Auth | Description                    |
| ------ | ----------------------------- | ---- | ------------------------------ |
| POST   | `/customers`                  | ❌   | Create customer + bank account |
| POST   | `/make_transaction`           | ✅   | Debit/credit with fraud check  |
| POST   | `/services/internal-transfer` | ✅   | Internal transfer              |

---

### 💳 Cards (`/cards/*`)

| Method | Endpoint               | Auth | Description        |
| ------ | ---------------------- | ---- | ------------------ |
| GET    | `/cards/`              | ✅   | List all cards     |
| POST   | `/cards/request`       | ✅   | Request new card   |
| GET    | `/cards/:id/details`   | ✅   | Single card        |
| PATCH  | `/cards/:id/freeze`    | ✅   | Freeze card        |
| PATCH  | `/cards/:id/activate`  | ✅   | Activate card      |
| POST   | `/cards/:id/set-limit` | ✅   | Update daily limit |

---

### 📱 Quick Services (`/services/*`)

| Method | Endpoint                      | Description            |
| ------ | ----------------------------- | ---------------------- |
| GET    | `/services/airtime/providers` | List airtime providers |
| POST   | `/services/airtime/purchase`  | Buy airtime            |
| GET    | `/services/data/providers`    | List data providers    |
| POST   | `/services/data/purchase`     | Buy data               |
| GET    | `/services/bills/categories`  | Bill categories        |
| GET    | `/services/bills/providers`   | Bill providers         |
| POST   | `/services/bills/pay`         | Pay a bill             |

---

### 🔔 Notifications (`/notifications/*`)

| Method | Endpoint                  | Description       |
| ------ | ------------------------- | ----------------- |
| GET    | `/notifications/`         | All notifications |
| PATCH  | `/notifications/:id/read` | Mark as read      |
| DELETE | `/notifications/:id`      | Delete            |

---

### 🤖 AI Agents

| Method | Endpoint                            | Description                     |
| ------ | ----------------------------------- | ------------------------------- |
| GET    | `/trajectory/popup_recommendations` | AI card product recommendations |
| POST   | `/ai/chat`                          | AI banking chat assistant       |

---

## Frontend Architecture Rules

### 1. One axios instance — always

All API calls go through `src/api/axiosInstance.js`. Never use plain `fetch()` or a new `axios.create()` anywhere else.

### 2. Zustand store slices pattern

Organise the store by domain in **one file** (or split into `authSlice.js`, `accountSlice.js`):

```js
// store/useStore.js — grow this as needed
export const useStore = create((set, get) => ({
  // Auth
  user: null,
  accounts: [],
  isLoading: false,
  error: null,

  // Actions
  fetchUser: async () => {
    /* GET /users/me */
  },
  logout: () => {
    localStorage.removeItem("access_token");
    set({ user: null, accounts: [] });
  },

  // Onboarding (already exists)
  createCustomer: async (formData) => {
    /* POST /customers */
  },
}));
```

### 3. API error handling pattern — always use this

```js
try {
  const res = await axiosInstance.post("/some/endpoint", payload);
  // use res.data
} catch (err) {
  const msg =
    err.response?.data?.detail || // FastAPI error
    err.response?.data?.message ||
    err.message ||
    "Something went wrong";
  setError(msg);
}
```

### 4. Loading states on every form

Every submit button must:

- Show `disabled` + spinner text while `isLoading === true`
- Never allow double submit

### 5. Component structure per page

```
pages/
  Dashboard.jsx        ← page-level component (fetches data, handles state)
components/
  AccountCard.jsx      ← reusable display piece
  TransactionItem.jsx
  QuickActionButton.jsx
```

---

## Security Checklist

### ✅ Already Implemented

- JWT attached via Axios request interceptor (`axiosInstance.js`)
- Passwords hashed with bcrypt (`auth.py`)
- OTP email verification before account activation
- Account ownership verified server-side on every transaction

### 🔴 Must Implement Before Launch

#### 1. Protected Routes (see next section)

Every page behind `/dashboard`, `/transfer` etc. must check for a valid token.

#### 2. Token Expiry Handling

Add a **response interceptor** to `axiosInstance.js`:

```js
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  },
);
```

#### 3. Never log tokens or passwords

```js
// ❌ BAD
console.log("token:", localStorage.getItem("access_token"));

// ✅ Just don't log sensitive data at all
```

#### 4. Sensitive inputs — autocomplete off

```jsx
<input type="password" autoComplete="new-password" />
```

#### 5. Amount validation — always positive

```js
if (amount <= 0 || isNaN(amount)) {
  setError("Please enter a valid amount.");
  return;
}
```

#### 6. No sensitive data in URLs

```js
// ❌ BAD — account number in URL
navigate(`/transfer?from=${accountNumber}`);

// ✅ GOOD — use state or store
navigate("/transfer", { state: { fromAccount: account } });
// or just read from Zustand store
```

#### 7. Environment variables — never hardcode URLs

```
# .env (Frontend)
VITE_API_URL=https://your-backend.onrender.com
```

```js
// axiosInstance.js — already doing this correctly ✅
baseURL: import.meta.env.VITE_API_URL || "http://localhost:8080";
```

---

## Axios & Auth Setup

Current `axiosInstance.js` is correct. Add the **401 response interceptor** for token expiry:

```js
// src/api/axiosInstance.js (complete version)
import axios from "axios";

const axiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8080",
  timeout: 60000,
  headers: { "Content-Type": "application/json" },
});

// Attach JWT on every request
axiosInstance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  },
  (error) => Promise.reject(error),
);

// Auto-redirect on expired token
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  },
);

export default axiosInstance;
```

---

## Zustand Store — How to Extend

```js
// Example: Add fetchUser to useStore.js
fetchUser: async () => {
  set({ isLoading: true, error: null });
  try {
    const res = await axiosInstance.get('/users/me');
    set({
      user: res.data,
      accounts: res.data.account_details,
      isLoading: false,
    });
  } catch (err) {
    const msg = err.response?.data?.detail || 'Failed to load profile';
    set({ error: msg, isLoading: false });
    throw err;
  }
},

logout: () => {
  localStorage.removeItem('access_token');
  set({ user: null, accounts: [], error: null });
},
```

---

## Protected Routes (PrivateRoute)

Create `src/components/PrivateRoute.jsx`:

```jsx
// src/components/PrivateRoute.jsx
import { Navigate } from "react-router-dom";

const PrivateRoute = ({ children }) => {
  const token = localStorage.getItem("access_token");
  return token ? children : <Navigate to="/login" replace />;
};

export default PrivateRoute;
```

Then wrap all protected pages in `App.jsx`:

```jsx
// App.jsx
import PrivateRoute from "./components/PrivateRoute";
import Dashboard from "./pages/Dashboard";
import Transfer from "./pages/Transfer";
// ... other imports

function App() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/onboarding" element={<Onboarding />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/verify-otp" element={<OTPVerify />} />
      <Route path="/login" element={<Login />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />

      {/* Protected */}
      <Route
        path="/dashboard"
        element={
          <PrivateRoute>
            <Dashboard />
          </PrivateRoute>
        }
      />
      <Route
        path="/transfer"
        element={
          <PrivateRoute>
            <Transfer />
          </PrivateRoute>
        }
      />
      <Route
        path="/cards"
        element={
          <PrivateRoute>
            <Cards />
          </PrivateRoute>
        }
      />
      <Route
        path="/services"
        element={
          <PrivateRoute>
            <Services />
          </PrivateRoute>
        }
      />
      <Route
        path="/history"
        element={
          <PrivateRoute>
            <TransactionHistory />
          </PrivateRoute>
        }
      />
      <Route
        path="/profile"
        element={
          <PrivateRoute>
            <Profile />
          </PrivateRoute>
        }
      />
      <Route
        path="/notifications"
        element={
          <PrivateRoute>
            <Notifications />
          </PrivateRoute>
        }
      />
      <Route
        path="/settings"
        element={
          <PrivateRoute>
            <Settings />
          </PrivateRoute>
        }
      />

      {/* Default */}
      <Route path="/" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}
```

---

## Step-by-Step Completion Plan

### Phase 1 — Core Infrastructure (Do These First)

- [ ] Add 401 response interceptor to `axiosInstance.js`
- [ ] Add `PrivateRoute.jsx` component
- [ ] Add `fetchUser`, `logout` actions to `useStore.js`
- [ ] Update `App.jsx` with all routes + PrivateRoute wrappers

### Phase 2 — Dashboard (Most Important)

- [ ] `Dashboard.jsx` — calls `GET /users/me` on mount
- [ ] Show account balance, account number, customer name
- [ ] Recent transactions list (last 5)
- [ ] Quick action buttons → navigate to relevant pages
- [ ] AI popup from `GET /trajectory/popup_recommendations`

### Phase 3 — Transactions & Transfers

- [ ] `TransactionHistory.jsx` — filterable list
- [ ] `Transfer.jsx` — form for internal + external transfers
- [ ] Fraud detection response handling (show blocked/approved status)

### Phase 4 — Cards & Services

- [ ] `Cards.jsx` — list cards, freeze/activate, set limit
- [ ] `Services.jsx` — tabs for Airtime, Data, Bill payment

### Phase 5 — Account & Settings

- [ ] `Profile.jsx` — view + edit profile, change password
- [ ] `Notifications.jsx` — list + mark as read + delete
- [ ] `Settings.jsx` — theme, language, notification prefs
- [ ] `ForgotPassword.jsx` — email entry form

### Phase 6 — Polish & Security

- [ ] Loading skeletons on Dashboard data fetch
- [ ] Toast notifications instead of `alert()` everywhere
- [ ] Form validation library (consider `react-hook-form`)
- [ ] All pages mobile-responsive tested on 375px width
- [ ] Remove all `console.log` statements before production
- [ ] Test token expiry → auto-redirect to login

---

## Common Mistakes To Avoid

| ❌ Wrong                                    | ✅ Right                                 |
| ------------------------------------------- | ---------------------------------------- |
| `fetch('/api/users/me')`                    | `axiosInstance.get('/users/me')`         |
| Posting to `/auth/token` with JSON          | Use `URLSearchParams` (form-encoded)     |
| Showing raw `err` in alert                  | Show `err.response?.data?.detail`        |
| Storing token in sessionStorage             | `localStorage` (already correct)         |
| Calling API in every re-render              | Call in `useEffect` with empty deps `[]` |
| Hardcoding `localhost:8080`                 | Use `VITE_API_URL` env variable          |
| Navigating to dashboard without token check | Always use `PrivateRoute`                |

---

_Last updated: 2026-03-04 | Sentinel Bank Frontend Completion Guide_
