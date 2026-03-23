# Sentinel Banking MVP - Key Endpoints Documentation

This document outlines the core backend endpoints required for the frontend MVP implementation.

## 1. Authentication Endpoints

### User Login
* **Endpoint:** `POST /auth/token`
* **Description:** Authenticates a customer and provides a JWT access token.
* **Payload (Form Data):**
  * `username`: Customer's email address
  * `password`: Customer's password
* **Response:**
  Returns an `access_token` and `token_type` (bearer). This token is required for all customer-facing endpoints.

### Admin Login
* **Endpoint:** `POST /admin/login`
* **Description:** Authenticates an administrator and provides a JWT access token.
* **Payload (Form Data):**
  * `username`: Admin email
  * `password`: Admin password
* **Response:**
  Returns an `access_token` and `token_type` (bearer). This token is strictly required for `/admin/*` routes.

---

## 2. User Profile Endpoint

### Get Current User Profile
* **Endpoint:** `GET /users/me`
* **Headers:** `Authorization: Bearer <user_token>`
* **Description:** Retrieves the authenticated user's profile information and all linked bank accounts.
* **Response:**
  Returns a `FullUserResponse` JSON object containing:
  * `customer_id` & `email`
  * `customer_details`: First name, last name, full name, phone number, and KYC status.
  * `account_details`: A list of all bank accounts belonging to the user. Each account includes `account_id`, `account_number`, `account_type`, `current_balance`, and account `status`.

---

## 3. Agent Endpoints (Core MVP)


### Process Card Transaction (Terminal/POS)
* **Endpoint:** `POST /card_transaction`
* **Headers:** `Authorization: Bearer <user_token>`
* **Payload (JSON):**
  * `account_number` (string)
  * `amount` (float)
  * `device_id` (string)
  * `merchant_name` (optional string)
  * `transaction_type` (string: "debit" or "credit")
  * `narration` (optional string)
  * `currency` (string, e.g., "NGN")
* **Description:** 
  Initiates a Point-of-Sale (POS) or card transaction. This endpoint synchronously invokes the **SentinelAgent** but enforces a mandatory card challenge override policy. As a result, the transaction is always placed in a `PENDING_CONFIRMATION` state to force explicit user verification via a popup.

### Search Knowledge Base (FAQs)
* **Endpoint:** `GET /faqs`
* **Query Parameters:**
  * `prompt` (optional string, search keyword)
* **Description:** 
  Searches the internal FAQ knowledge base. If no prompt is provided, returns all available FAQs grouped by category. If a prompt is provided, returns the most relevant FAQ using a similarity score, along with a confidence label.

### Submit Complaint (Dispatcher Agent)
* **Endpoint:** `POST /make_complaint`
* **Headers:** `Authorization: Bearer <user_token>`
* **Payload (JSON):**
  * `account_number` (string)
  * `complaint_channel` (string, e.g., "in-app", "web")
  * `complaint_text` (string)
  * `linked_transaction_id` (optional string)
  * `linked_reference` (optional string)
* **Description:** 
  Saves a new customer complaint and asynchronously invokes the **DispatcherAgent**. The AI analyzes the complaint text, determines customer sentiment, assigns a priority level, and routes the complaint to the most appropriate internal department.

### Initiate Transaction (Sentinel Agent)
* **Endpoint:** `POST /make_transaction`
* **Headers:** `Authorization: Bearer <user_token>`
* **Payload (JSON):**
  * `account_number` (string)
  * `amount` (float)
  * `channel` (string)
  * `device_id` (string)
  * `merchant_name` (optional string)
  * `transaction_type` (string: "debit" or "credit")
  * `narration` (optional string)
  * `currency` (string, e.g., "NGN")
* **Description:** 
  Initiates a bank transaction and synchronously runs the **SentinelAgent** to perform real-time fraud analysis. 
  * If the calculated AI risk score is acceptable, the transaction completes successfully and balances are updated.
  * If the AI flags the transaction as high-risk (>80 risk score), it is placed in a `PENDING_CONFIRMATION` state, requiring the user to explicitly confirm their identity/intent.

### Confirm Pending Transaction
* **Endpoint:** `POST /transactions/confirm`
* **Headers:** `Authorization: Bearer <user_token>`
* **Payload (JSON):**
  * `transaction_id` (string)
  * `password` (string - customer's login password for verification)
* **Description:** 
  Confirms and completes a transaction that was previously flagged as high-risk by the Sentinel Agent. The backend verifies the provided password, deducts the amount from the customer's balance, and marks the transaction as "completed".

### Get Trajectory Recommendations
* **Endpoint:** `GET /trajectory/popup_recommendations`
* **Headers:** `Authorization: Bearer <user_token>`
* **Description:** 
  Invokes the **TrajectoryAgent** to analyze the user's financial profile, transaction history, and balances to return highly personalized product recommendations (e.g., Car Loans, Student Loans, Fixed Deposits). The response payload is specifically structured to supply data for a frontend popup or marquee card.

---

## 4. Admin Routing Endpoints

### View Complaint Routing Decisions
* **Endpoint:** `GET /admin/routing-decisions`
* **Headers:** `Authorization: Bearer <admin_token>`
* **Query Parameters:**
  * `department_name` (optional string, filters results by department)
  * `skip` (integer, default=0)
  * `limit` (integer, default=50)
* **Description:** 
  Allows administrators to view a chronological log of all AI dispatcher routing decisions. The response includes the rationale behind the AI's choices, the assigned department, priority level, and customer sentiment for each complaint.
