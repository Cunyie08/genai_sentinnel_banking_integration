"""
Project: AI-Driven Banking Middleware (Capstone)
Organization: The Sentinels / AI Fellowship NCC
Role: AI Engineer 2 - Week 1 Deliverable (UPDATED - v3)
Document: Full-Scale Grounding Policy Engine (Production Version)

CHANGELOG v3:
  - PRODUCT_CLASSES expanded from 3 to 5: added Student Loan, Trust Fund
  - PRODUCT_THRESHOLDS and CAR_LOAN_SIGNAL_WEIGHTS removed
  - LOAN_SIGNAL_SCORE_RANGES added: per-product (floor, ceiling) ranges
    aligned to data_generator.py random.uniform() ranges exactly
  - PRS-001 document fully rewritten to reflect score-range model,
    balanced product assignment, and all 5 product eligibility policies
  - Field rename: car_loan_signal_score -> Loan_signal_score (capital L)
  - salary_detected / uber_tracker / monthly_inflow reclassified as
    behavioral context signals, not eligibility gates

Author: AI Engineer 2 (Security & Knowledge Specialist)
Date: February 2026
"""

import json
import uuid
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path


# =============================================================================
# SHARED CONSTANTS — imported by rag_querys.py for zero-drift alignment
# =============================================================================

# Merchant category risk weights (FRM-002, Section 1)
MERCHANT_RISK: Dict[str, int] = {
    "fintech":     25,
    "transport":   15,
    "education":   15,
    "healthcare":  15,
    "telecoms":     5,
    "supermarket":  0,
    "restaurants":  0,
    "fuel":         0,
    "utilities":    0,
}

# Fraud trace flag risk weights (FRM-001, Section 1)
FLAG_WEIGHTS: Dict[str, int] = {
    "mobile_channel_risk": 15,
    "high_amount_spike":   25,
    "multiple_failures":   20,
    "normal_pattern":       0,
}

# SLA hours per department (POL-CCH-001, Section 2)
EXPECTED_SLA: Dict[str, int] = {
    "TSU": 48,
    "COC": 48,
    "FRM": 24,
    "DCS": 72,
    "AOD": 72,
    "CLS": 96,
}

# Full department names keyed by department_code
DEPT_NAMES: Dict[str, str] = {
    "TSU": "Transaction Services Unit",
    "COC": "Card Operations Center",
    "FRM": "Fraud Risk Management",
    "DCS": "Digital Channels Support",
    "AOD": "Account Operations Department",
    "CLS": "Credit & Loan Services",
}

# Risk score thresholds (FRM-001, Section 2.2)
RISK_THRESHOLDS = {
    "LOW":      (0,  30),
    "MEDIUM":   (31, 60),
    "HIGH":     (61, 85),
    "CRITICAL": (86, 100),
}

# Product classes — must match data_generator.py PRODUCT_CLASSES exactly.
# 3000 customers, 600 per product, assigned in balanced shuffle order.
PRODUCT_CLASSES: List[str] = [
    "Student Loan",
    "Car Loan",
    "Investment Plan",
    "Trust Fund",
    "Personal Loan",
]

# Loan_signal_score ranges per product — (floor, ceiling).
# These match the random.uniform() ranges in data_generator.py exactly.
# Floor = minimum score for APPROVED eligibility.
# Ceiling = upper bound used during data generation.
# The field in transactions.csv is "Loan_signal_score" (capital L).
LOAN_SIGNAL_SCORE_RANGES: Dict[str, tuple] = {
    "Student Loan":    (0.80, 0.98),
    "Car Loan":        (0.75, 0.95),
    "Investment Plan": (0.70, 0.90),
    "Personal Loan":   (0.70, 0.92),
    "Trust Fund":      (0.65, 0.85),
}


class BankingPolicyGenerator:
    """
    Enterprise-grade generator for comprehensive banking policies.

    Generates six core policy documents that serve as the ground truth
    for the RAG-based AI middleware system:

    1. Complaint Handling Policy (POL-CCH-001)       -> Dispatcher Agent
    2. Fraud Detection Guidelines (FRM-001)           -> Sentinel Agent
    3. Transaction Processing Policies (TSU-POL-002) -> All Agents
    4. Customer Service FAQ (FAQ-001)                 -> Customer-Facing
    5. Merchant Risk Profiles (FRM-002)               -> Sentinel Agent
    6. Product Recommendation Policy (PRS-001)        -> Trajectory Agent

    Usage:
        generator = BankingPolicyGenerator(bank_name="Sentinel Bank Nigeria")
        generator.save_all_policies(Path("./knowledge_base"))
    """

    def __init__(self, bank_name: str = "Sentinel Bank Nigeria"):
        self.bank_name = bank_name
        self.generation_time = datetime.now().isoformat()
        self.display_date = datetime.now().strftime('%B %Y')

        self.system_meta = {
            "project": "AI-Driven Banking Middleware",
            "organization": "The Sentinels / AI Fellowship NCC",
            "jurisdiction": "Nigeria",
            "version": "2026.Q1.v3-COMPLETE",
            "data_classification": "Synthetic/Proprietary"
        }

    def _package_for_rag(self, doc_id: str, title: str, category: str,
                         version: str, text: str) -> Dict[str, Any]:
        return {
            "document_id": doc_id,
            "title": title,
            "category": category,
            "version": version,
            "metadata": {
                **self.system_meta,
                "title": title,
                "category": category,
                "version": version,
                "uuid": str(uuid.uuid4()),
                "last_modified": self.generation_time
            },
            "content": text.strip(),
            "last_updated": self.generation_time
        }

    # =========================================================================
    # DOCUMENT 1: COMPLAINT HANDLING POLICY (POL-CCH-001) — UNCHANGED
    # =========================================================================

    def generate_complaint_handling_policy(self) -> Dict:
        policy_content = f"""
=========================================================================
{self.bank_name} - CUSTOMER COMPLAINT HANDLING & ROUTING POLICY
=========================================================================

Document ID     : POL-CCH-001
Version         : 2.1
Effective Date  : January 2025
Classification  : Internal Use Only -- AI Agent Operational Reference
Review Cycle    : Quarterly

=========================================================================
SECTION 1: PURPOSE & SCOPE
=========================================================================

This policy establishes standardized, deterministic procedures for
receiving, classifying, routing, and resolving customer complaints
across all service channels at {self.bank_name}.

Primary Consumers of This Policy:
  - Dispatcher Agent: Uses routing rules in Section 2 to assign every
    inbound complaint to the correct department on first contact.
  - Sentinel Agent: Uses fraud_related field and FRM routing rules to
    escalate fraud-linked complaints immediately.
  - Human supervisors: Use escalation matrix in Section 4 for overrides.

Key Objectives:
  1. Route complaints to the correct department with >95% accuracy
     on first contact, eliminating manual re-routing overhead.
  2. Enforce SLA compliance by department (exact hours in Section 2).
  3. Provide deterministic escalation paths for every complaint tier.
  4. Enable full auditability -- every routing decision must cite a
     policy section and department code from this document.

Complaint Intake Channels (complaint_channel field values):
  - call_center   : Phone call to customer care hotline
  - mobile_app    : Complaint submitted inside the Sentinel mobile app
  - email         : Complaint submitted via email
  - branch        : In-person complaint at any Sentinel Bank branch
  - social_media  : Twitter, Facebook, Instagram, LinkedIn DMs


=========================================================================
SECTION 2: COMPLAINT CATEGORIES & DEPARTMENT ROUTING
=========================================================================

ROUTING DECISION LOGIC FOR DISPATCHER AGENT
---------------------------------------------
The Dispatcher Agent MUST evaluate fields in this exact priority order:

  STEP 1: If fraud_related == 1 OR is_fraud_score == 1
          -> Route to FRM (Priority: Critical). STOP.

  STEP 2: If transaction channel (channel field) is "atm" or "pos"
          AND transaction_status is NOT "successful"
          -> Route to COC (Priority: High). STOP.

  STEP 3: If transaction_status is "failed", "timeout", or "reversed"
          AND channel is "nibss_transfer", "mobile_app", "web", or "ussd"
          -> Route to TSU (Priority: High). STOP.

  STEP 4: If complaint text references app, login, USSD, crash, error
          -> Route to DCS (Priority: Medium).

  STEP 5: If complaint text references statement, balance, charges,
          account closure, BVN
          -> Route to AOD (Priority: Medium or Low).

  STEP 6: If complaint text references loan, credit, repayment,
          disbursement, overdraft
          -> Route to CLS (Priority: Medium).

  DEFAULT: Route to TSU (Priority: Medium).


--------------------------------------------------------------------------
2.1  TRANSACTION SERVICES UNIT (TSU)
--------------------------------------------------------------------------
Department Code   : TSU
Department Name   : Transaction Services Unit
SLA (Hours)       : 48 hours  <- sla_hours_limit = 48 in dataset
Team Size         : 12 specialists + 2 managers

HANDLES:
  - Transfer debited from sender but credit not received by beneficiary
  - Duplicate debit transactions (same amount charged twice)
  - Incorrect transaction amounts
  - Failed interbank NIP/NIBSS transfers (status = "failed" or "timeout")
  - Reversed transactions that customer disputes (status = "reversed")
  - Missing inbound credit
  - Transaction narration or reference number discrepancies

CHANNELS THAT PRIMARILY GENERATE TSU COMPLAINTS:
  nibss_transfer, mobile_app, ussd, web, branch

PRIORITY ASSIGNMENT RULES FOR TSU:
  - High   : Amount > 100,000 OR status = "failed"/"timeout"/"reversed"
  - Medium : Amount <= 100,000 AND status = "successful" (dispute only)
  - Low    : Narration/reference query, no financial impact

SLA TARGETS:
  - Acknowledgement    : Within 2 hours
  - Resolution         : Within 48 hours (business hours)
  - Reversal (if due)  : Within 24 hours of confirmation
  - Interbank disputes : Up to 14 days (NIBSS coordination required)

COMPLAINT TEXT KEYWORDS THAT TRIGGER TSU ROUTING:
  "transfer", "debit", "not received", "wrong amount",
  "reversal", "failed transaction", "duplicate charge",
  "credited", "debited twice", "NIBSS", "interbank"

EXAMPLES:
  Correct : "I transferred N100,000 to GTBank but recipient has not received it."
  Correct : "My account was debited twice for the same payment."
  Incorrect: "My card was declined at POS." -> Route to COC, not TSU.


--------------------------------------------------------------------------
2.2  CARD OPERATIONS CENTER (COC)
--------------------------------------------------------------------------
Department Code   : COC
Department Name   : Card Operations Center
SLA (Hours)       : 48 hours  <- sla_hours_limit = 48 in dataset
Team Size         : 8 specialists + 1 manager

HANDLES:
  - Card declined at POS terminal or ATM
  - Card retained/swallowed by ATM machine
  - Unauthorized card transactions
  - Lost or stolen card blocking requests
  - PIN reset requests and PIN lock issues
  - Card activation failures
  - Chip or magnetic stripe malfunction
  - Contactless payment failures
  - Card replacement requests

CHANNELS THAT PRIMARILY GENERATE COC COMPLAINTS:
  atm, pos

PRIORITY ASSIGNMENT RULES FOR COC:
  - Critical : Fraud amount > N100,000 AND is_fraud_score = 1
  - High     : ATM card swallowed, POS failure with debit confirmed
  - Medium   : PIN reset, card replacement request
  - Low      : Card information query

SLA TARGETS:
  - Emergency card blocking   : Immediate (within 5 minutes)
  - Card replacement          : 3-5 business days
  - Dispute investigation     : 7-14 days
  - PIN reset                 : Same day (within 4 hours)

COMPLAINT TEXT KEYWORDS THAT TRIGGER COC ROUTING:
  "card", "PIN", "swallowed", "declined", "POS", "chip",
  "contactless", "ATM", "blocked card", "card stolen"


--------------------------------------------------------------------------
2.3  FRAUD RISK MANAGEMENT (FRM)
--------------------------------------------------------------------------
Department Code   : FRM
Department Name   : Fraud Risk Management
SLA (Hours)       : 24 hours  <- sla_hours_limit = 24 in dataset
Team Size         : 6 specialists + 1 senior manager
Operating Hours   : 24/7 including public holidays

HANDLES:
  - All transactions where is_fraud_score = 1
  - All complaints where fraud_related = 1
  - Suspected unauthorized account access
  - Account takeover suspicion
  - SIM swap fraud concerns
  - Social engineering scam reports

ROUTING TRIGGER (DETERMINISTIC):
  IF fraud_related == 1 OR is_fraud_score == 1 -> ALWAYS FRM, ALWAYS Critical.
  This overrides ALL other routing rules. No exceptions.

SLA TARGETS:
  - Account freeze          : Immediate (within 2 minutes)
  - Investigation start     : Within 1 hour
  - Preliminary assessment  : Within 24 hours <- matches sla_hours_limit
  - Full investigation      : 14-21 days

COMPLAINT TEXT KEYWORDS THAT TRIGGER FRM ROUTING:
  "fraud", "hacked", "unauthorized", "scam", "phishing",
  "suspicious", "someone used my account", "I did not authorize",
  "compromised"

CRITICAL OPERATIONAL NOTE:
  NEVER route fraud cases to DCS or TSU even if the fraud occurred on
  a digital channel. NEVER delay a fraud complaint for documentation.


--------------------------------------------------------------------------
2.4  DIGITAL CHANNELS SUPPORT (DCS)
--------------------------------------------------------------------------
Department Code   : DCS
Department Name   : Digital Channels Support
SLA (Hours)       : 72 hours  <- sla_hours_limit = 72 in dataset
Team Size         : 10 specialists + 2 managers

HANDLES:
  - Mobile app login failures
  - Internet banking access problems
  - USSD service errors
  - App crashes, hangs, or freezes
  - Biometric authentication failures
  - OTP delivery failures linked to app/platform

CHANNELS THAT PRIMARILY GENERATE DCS COMPLAINTS:
  mobile_app, ussd, web

SLA TARGETS:
  - Level 1 troubleshooting  : Immediate
  - Technical escalation     : Within 4 hours
  - Resolution               : 24-72 hours <- matches sla_hours_limit

COMPLAINT TEXT KEYWORDS THAT TRIGGER DCS ROUTING:
  "app", "login", "password", "internet banking", "USSD",
  "crash", "freeze", "error message", "biometric", "fingerprint",
  "mobile app", "not loading"


--------------------------------------------------------------------------
2.5  ACCOUNT OPERATIONS DEPARTMENT (AOD)
--------------------------------------------------------------------------
Department Code   : AOD
Department Name   : Account Operations Department
SLA (Hours)       : 72 hours  <- sla_hours_limit = 72 in dataset
Team Size         : 15 specialists + 3 managers

HANDLES:
  - Account statement requests
  - Account balance discrepancy inquiries
  - Account closure requests
  - Service charge disputes
  - BVN and NIN linking or update issues
  - Dormant account reactivation
  - Account freeze (non-fraud related)

SLA TARGETS:
  - Statement generation      : Within 24 hours
  - Account modification      : 2-3 business days
  - Account closure           : 5-7 business days
  - BVN/NIN updates           : 24-48 hours

COMPLAINT TEXT KEYWORDS THAT TRIGGER AOD ROUTING:
  "statement", "balance", "close account", "charges",
  "upgrade", "update details", "BVN", "NIN", "dormant",
  "maintenance fee", "account freeze"


--------------------------------------------------------------------------
2.6  CREDIT & LOAN SERVICES (CLS)
--------------------------------------------------------------------------
Department Code   : CLS
Department Name   : Credit & Loan Services
SLA (Hours)       : 96 hours  <- sla_hours_limit = 96 in dataset
Team Size         : 6 specialists + 1 manager

HANDLES:
  - Loan disbursement delays or failures
  - Interest calculation disputes
  - Repayment schedule issues or missed auto-debit
  - Credit limit increase requests
  - Loan restructuring requests
  - Early repayment and settlement queries
  - Loan documentation problems
  - All five loan/investment product types:
    Student Loan, Car Loan, Investment Plan, Trust Fund, Personal Loan

SLA TARGETS:
  - Query response             : Within 48 hours
  - Disbursement issue         : 3-5 business days
  - Credit review              : 7-14 days
  - Restructuring decision     : 14-21 days

COMPLAINT TEXT KEYWORDS THAT TRIGGER CLS ROUTING:
  "loan", "credit", "disbursement", "interest", "repayment",
  "overdraft", "restructure", "settlement", "installment",
  "student loan", "car loan", "trust fund", "investment plan"


=========================================================================
SECTION 3: COMPLAINT PRIORITY CLASSIFICATION
=========================================================================

  Critical : fraud_related = 1 OR is_fraud_score = 1 (always)
             Response: IMMEDIATE (within 5 minutes)

  High     : ATM card retention, failed high-value transaction
             Response: Within 2 hours

  Medium   : Standard transaction dispute, app technical issue
             Response: Within 4 hours

  Low      : General inquiries, product information requests
             Response: Within 24 hours


=========================================================================
SECTION 4: ESCALATION MATRIX
=========================================================================

  Level 1 : CSR or AI Agent (70% FCR target)
  Level 2 : Specialist (sla_breach_flag = 1 or complexity)
  Level 3 : Department Manager (7 days unresolved or legal threat)
  Level 4 : Executive Committee (<1% of complaints)


=========================================================================
SECTION 5: PROHIBITED ACTIONS
=========================================================================

1. NEVER route fraud_related=1 complaints to any department other than FRM.
2. NEVER delay account freeze when fraud is suspected.
3. NEVER promise resolution within less than the SLA hours in Section 2.
4. NEVER share customer PII via unencrypted channels.
5. NEVER close a ticket without customer confirmation of resolution.
6. NEVER route based on intake channel -- route based on issue type only.


=========================================================================
SECTION 6: DOCUMENTATION REQUIREMENTS
=========================================================================

  complaint_id          : System-generated (format: CMP-XXXXXX)
  customer_id           : Account or customer UUID
  linked_transaction_id : UUID from transactions table (if applicable)
  department_code       : TSU | COC | FRM | DCS | AOD | CLS
  priority_level        : Critical | High | Medium | Low
  sentiment             : angry | neutral | calm
  complaint_channel     : call_center | mobile_app | email | branch | social_media
  sla_hours_limit       : Exact SLA hours from Section 2 per department
  sla_breach_flag       : 1 if resolution_time_hours > sla_hours_limit; else 0
  fraud_related         : 1 if is_fraud_score = 1; else 0
  complaint_status      : open | resolved | escalated


=========================================================================
DOCUMENT CONTROL
=========================================================================

Policy Owner    : Head of Customer Experience
Approver        : Chief Operations Officer (COO)
Review Cycle    : Quarterly
Last Updated    : {self.display_date}
Contact         : customer.experience@sentinelbank.ng | Ext. 5000


=========================================================================
END OF DOCUMENT POL-CCH-001
=========================================================================
"""
        return self._package_for_rag(
            "POL-CCH-001",
            "Customer Complaint Handling Policy",
            "policy",
            "2.1",
            policy_content
        )

    # =========================================================================
    # DOCUMENT 2: FRAUD DETECTION GUIDELINES (FRM-001) — UNCHANGED
    # =========================================================================

    def generate_fraud_detection_guidelines(self) -> Dict:
        guidelines = f"""
=========================================================================
{self.bank_name} - FRAUD DETECTION & PREVENTION GUIDELINES
=========================================================================

Document Code       : FRM-001
Classification      : CONFIDENTIAL -- AI Agent Operational Reference
Version             : 4.0
Effective Date      : January 2026
Review Frequency    : Monthly

Document Owner      : Chief Risk Officer (CRO)
Emergency Contact   : fraud-desk@sentinelbank.ng (Active 24/7)


=========================================================================
SECTION 1: FRAUD EXPLAINABILITY TRACE FLAGS
=========================================================================

The fraud_explainability_trace field in transactions.csv contains a
comma-separated list of flags. The field contains "normal_pattern" when
no fraud is detected. The Sentinel Agent MUST parse this field and map
each flag to its risk weight using this section.

--------------------------------------------------------------------------
FLAG: mobile_channel_risk
--------------------------------------------------------------------------
Risk Weight       : +15 points
Trigger Condition : Transaction channel = "mobile_app"
                    AND is_fraud_score = 1
Definition        : Transaction initiated via mobile application on a
                    device that may not be the customer's primary registered
                    device, or the session exhibits behavioral anomalies.


--------------------------------------------------------------------------
FLAG: high_amount_spike
--------------------------------------------------------------------------
Risk Weight       : +25 points
Trigger Condition : Transaction amount > (account current_balance x 0.6)
                    AND is_fraud_score = 1
Definition        : The transaction represents more than 60% of the
                    account balance -- characteristic of account draining.


--------------------------------------------------------------------------
FLAG: multiple_failures
--------------------------------------------------------------------------
Risk Weight       : +20 points
Trigger Condition : transaction_status = "failed"
                    AND is_fraud_score = 1
Definition        : Failed transaction with abnormal retry behavior,
                    consistent with brute-force or card-testing attacks.


--------------------------------------------------------------------------
FLAG: normal_pattern
--------------------------------------------------------------------------
Risk Weight       : 0 points
Trigger Condition : No fraud flags detected (is_fraud_score = 0)
Action            : Process transaction normally. Issue standard SMS alert.


=========================================================================
SECTION 2: RISK SCORE CALCULATION & ACTION THRESHOLDS
=========================================================================

CALCULATION METHOD:
  risk_score = SUM of all active flag weights (from Section 1 + FRM-002)
  risk_score is CAPPED at 100.

EXAMPLE:
  mobile_channel_risk:  +15
  high_amount_spike:    +25
  merchant (fintech):   +25  [from FRM-002]
  Total:                 65 -> HIGH

--------------------------------------------------------------------------
RISK LEVEL: LOW  (Score 0-30)
--------------------------------------------------------------------------
Action          : PROCESS IMMEDIATELY -- no challenge or friction.
Notification    : SMS + App push after transaction completes.

--------------------------------------------------------------------------
RISK LEVEL: MEDIUM  (Score 31-60)
--------------------------------------------------------------------------
Action          : STEP-UP AUTHENTICATION via OTP.
                  Hold transaction in "Pending" state for 5 minutes.
                  Auto-decline if OTP not entered within 5 minutes.

--------------------------------------------------------------------------
RISK LEVEL: HIGH  (Score 61-85)
--------------------------------------------------------------------------
Action          : MANDATORY PUSH-TO-APP BIOMETRIC CHALLENGE.
                  Place transaction in "Pending - Security Check".
                  Customer must tap APPROVE or REJECT in app.
                  5-minute timeout -> auto-decline if no response.
requires_challenge : True
should_block       : False

--------------------------------------------------------------------------
RISK LEVEL: CRITICAL  (Score 86-100)
--------------------------------------------------------------------------
Action          : BLOCK TRANSACTION IMMEDIATELY.
                  Freeze account -- ALL channels disabled.
                  Block all cards linked to account.
                  Disable mobile app, internet banking, USSD.
                  Generate URGENT FRM alert.
                  Send security alert to registered EMAIL only.
requires_challenge : False
should_block       : True


=========================================================================
SECTION 3: PUSH-TO-APP AUTHORIZATION PROTOCOL
=========================================================================

WHY PUSH-TO-APP REPLACES SMS OTP:
  - SIM swap attacks intercept SMS -- push-to-app is device-bound.
  - Biometric binding means only the real customer can approve.
  - Full transaction details shown in app before approval.

COMPLETE PUSH-TO-APP SEQUENCE:
  1. Transaction placed in "Pending - Security Verification" (max 300 seconds)
  2. Encrypted push notification sent to registered device
  3. App displays: Beneficiary name, bank, amount, fees, risk reason,
     reference number
  4. Customer taps APPROVE (requires biometric) or REJECT
  5. REJECT -> transaction cancelled, FRM alert generated
  6. TIMEOUT (5 minutes) -> transaction auto-declined


=========================================================================
SECTION 4: COMMON FRAUD SCENARIOS IN NIGERIA (2026)
=========================================================================

4.1 SIM SWAP FRAUD
  Attack: Fraudster swaps SIM to receive banking OTPs.
  Detection: SIM swap in last 48 hours -> 48-hour transfer freeze.
  Mitigation: Push-to-app replaces SMS OTP as primary challenge.

4.2 ACCOUNT TAKEOVER (ATO)
  Flags: mobile_channel_risk + high_amount_spike
  Attack: Fraudster obtains login credentials via phishing,
          changes profile, withdraws maximum amount.
  Detection: 24-hour cooling-off period after profile changes.

4.3 PHISHING & SOCIAL ENGINEERING
  Attack: Fraudster impersonates bank official to obtain OTP/PIN.
  Detection: In-app warning during high-risk transfers:
    "SENTINEL BANK WILL NEVER ASK FOR YOUR PIN VIA PHONE."

4.4 FINTECH & CRYPTO FRAUD
  Merchant Category: fintech (high-risk per FRM-002)
  Detection: Combine merchant risk with mobile_channel_risk or
             high_amount_spike for composite score.


=========================================================================
SECTION 5: FRAUD RESPONSE PROTOCOLS
=========================================================================

IMMEDIATE (within 2 minutes of Critical detection):
  - Freeze account, block cards, disable all channels
  - Send security alert to registered EMAIL only
  - Generate urgent FRM alert

WITHIN 1 HOUR:
  - FRM specialist assigned
  - Preliminary investigation: transaction logs, device IDs

WITHIN 24 HOURS (SLA target for FRM):
  - Full forensic analysis
  - NIBSS coordination if funds transferred out
  - Contact destination bank to freeze beneficiary account
  - Police report filed (amounts > N1,000,000)

RESOLUTION (14-21 days):
  - Full investigation report, permanent credit/debit adjustments
  - Account reactivation with new credentials


=========================================================================
DOCUMENT CONTROL
=========================================================================

Owner           : Chief Risk Officer (CRO)
Review Freq     : Monthly
Last Updated    : {self.display_date}
Emergency       : fraud-desk@sentinelbank.ng | +234-1-FRAUD-24 (24/7)


=========================================================================
END OF DOCUMENT FRM-001
=========================================================================
"""
        return self._package_for_rag(
            "FRM-001",
            "Fraud Detection & Prevention Guidelines",
            "security",
            "4.0",
            guidelines
        )

    # =========================================================================
    # DOCUMENT 3: TRANSACTION PROCESSING POLICIES (TSU-POL-002) — UNCHANGED
    # =========================================================================

    def generate_transaction_policies(self) -> Dict:
        policies = f"""
=========================================================================
{self.bank_name} - TRANSACTION PROCESSING & LIMITS POLICY
=========================================================================

Document ID     : TSU-POL-002
Version         : 4.0
Effective Date  : January 2026
Classification  : Internal Use Only -- AI Agent Operational Reference

Policy Custodian : Head of Transaction Services
Last Review      : {self.display_date}


=========================================================================
SECTION 1: TRANSACTION STATUS DEFINITIONS
=========================================================================

STATUS: successful
  Definition    : Transaction completed without error.
  failure_reason: "none"
  Agent Action  : No action. Send standard confirmation alert.

STATUS: failed
  Definition    : Transaction could not be completed. Debit not applied
                  or will be auto-reversed within 24 hours.
  failure_reason: insufficient_fund | network_error | system_failure |
                  system_timeout | invalid_account_number |
                  daily_transaction_limit_exceeded | compliance_restriction |
                  suspected_fraud | issuer_unavailable
  Agent Action  : Route to TSU. Priority = High if amount > N100,000.

STATUS: reversed
  Definition    : Transaction processed but subsequently reversed.
  Agent Action  : Route to TSU if customer disputes the reversal.

STATUS: pending
  Definition    : Submitted but not yet processed.
  Agent Action  : Monitor. Escalate to TSU if pending > 30 minutes.

STATUS: timeout
  Definition    : Not completed within network timeout window.
  failure_reason: "system_timeout"
  Agent Action  : Route to TSU. Priority = High.

STATUS: queued
  Definition    : Received and queued for batch processing.
  Agent Action  : No immediate action.

STATUS: processing
  Definition    : Actively being processed by payment switch.
  Agent Action  : No action. Monitor for final status.


=========================================================================
SECTION 2: KYC TIERING & TRANSACTION LIMITS
=========================================================================

TIER 1 -- BASIC KYC
  Account Types     : savings (newly onboarded, limited KYC)
  Requirements      : Name + Phone number only
  Daily Tx Limit    : N50,000
  Max Balance       : N300,000
  Monthly Limit     : N200,000
  Channels Allowed  : ussd, branch, nibss_transfer (low value only)
  Restrictions      : NO international transactions, NO cards, NO loans

TIER 2 -- INTERMEDIATE KYC
  Account Types     : savings + solo (ages 16-30)
  Requirements      : Tier 1 + BVN + NIN
  Daily Tx Limit    : N200,000
  Max Balance       : N500,000
  Monthly Limit     : N2,000,000
  Channels Allowed  : mobile_app, ussd, atm, pos, web, branch,
                      nibss_transfer
  Note              : Student Loan available at Tier 2 (solo accounts)

TIER 3 -- FULL KYC
  Account Types     : current (full banking, business-grade)
  Requirements      : Tier 2 + Address verification + valid photo ID
                      + utility bill (< 3 months old)
  Daily Tx Limit    : N5,000,000
  Max Balance       : Unlimited
  Channels Allowed  : ALL channels including international SWIFT
  Benefits          : Full product suite including Investment Plan and
                      Trust Fund, loans up to N50,000,000


=========================================================================
SECTION 3: STATUTORY LEVIES (MANDATORY -- CANNOT BE WAIVED)
=========================================================================

Electronic Money Transfer Levy (EMTL)
  Rate         : Flat N50.00
  Applied to   : Inbound (CREDIT) transactions >= N10,000

National Cybersecurity Levy
  Rate         : 0.5% of transaction value
  Applied to   : Outbound (DEBIT) electronic transfers

Value Added Tax (VAT)
  Rate         : 7.5% applied to BANK FEES only (not principal)


=========================================================================
SECTION 4: CHANNEL-SPECIFIC TRANSACTION RULES
=========================================================================

CHANNEL: mobile_app
  Daily Limit       : Up to Tier limit
  OTP Required      : For amounts > N50,000 (Tier 2 and above)
  Push Challenge    : For amounts > N200,000 OR fraud flag present

CHANNEL: ussd
  Daily Limit       : N50,000 (Tier 1 cap)
  Fee               : N6.98 per USSD session

CHANNEL: atm
  Daily Withdrawal Limit  : N100,000 (standard) | N200,000 (premium)
  Per-Transaction Max     : N40,000 per withdrawal (most ATMs)
  Dispense Error          : Auto-reversal within 24 hours after reconciliation

CHANNEL: pos
  Daily Limit          : N500,000 (all cards combined)
  Contactless Limit    : N15,000 per tap; PIN required for >= N5,000

CHANNEL: nibss_transfer
  Processing Time      : 2-5 minutes (normal), up to 2 hours (peak)
  Peak Periods         : Month-end (25th-30th), Friday evenings
  failure_reason codes : network_error, system_timeout, issuer_unavailable,
                         invalid_account_number


=========================================================================
SECTION 5: REVERSAL POLICIES
=========================================================================

AUTOMATIC REVERSALS (no customer action required):
  Internal Transfer Failure  : Within 24 hours
  NIP/Interbank Failure      : 48-72 hours (NIBSS coordination)
  ATM Dispense Error         : Within 24 hours after reconciliation

MANUAL REVERSAL REQUESTS (customer must initiate via TSU):
  Eligible: Wrong account, duplicate transaction, amount error
  Timeline: 2-14 days depending on beneficiary response

REVERSAL NOT POSSIBLE:
  - Beneficiary has already withdrawn the funds
  - Value consummated (airtime loaded, bills paid)
  - Request made > 60 days after transaction


=========================================================================
SECTION 6: FAILURE REASON CODES
=========================================================================

failure_reason           -> Meaning & Action
-------------------------------------------------------------------------
none                     -> No failure. Transaction successful.
insufficient_fund        -> Balance insufficient. Advise customer to top up.
network_error            -> NIBSS connectivity issue. Auto-reversal expected.
system_failure           -> Core banking error. Escalate to TSU immediately.
system_timeout           -> Transaction timed out. Treat as failed. Route TSU.
invalid_account_number   -> Beneficiary account does not exist. No debit.
daily_tx_limit_exceeded  -> Customer hit KYC tier daily limit. Advise upgrade.
compliance_restriction   -> AML/regulatory block. Route AOD or FRM.
suspected_fraud          -> Fraud engine blocked. Route FRM always.
issuer_unavailable       -> Destination bank unreachable. Auto-reversal 24h.


=========================================================================
SECTION 7: SERVICE CHARGE SCHEDULE
=========================================================================

Interbank NIP Transfers:
  Amount <= N5,000         : N10.00
  Amount N5,001-N50,000   : N25.00
  Amount > N50,000         : N50.00

Internal Transfers (Intra-Sentinel)  : FREE
SMS Transaction Alerts               : N4.00 per alert (CBN mandatory)
USSD Banking Sessions                : N6.98 per session
ATM (own bank, 4th onwards)          : N65.00
ATM (other banks)                    : N65.00
Account Maintenance (savings)        : N50/month (waived if balance >= N100,000)
Account Maintenance (current)        : N300/month
Card Replacement                     : N1,500


=========================================================================
DOCUMENT CONTROL
=========================================================================

Policy Owner   : Head of Transaction Services
Last Updated   : {self.display_date}
Contact        : transactionservices@sentinelbank.ng | Ext. 4000


=========================================================================
END OF DOCUMENT TSU-POL-002
=========================================================================
"""
        return self._package_for_rag(
            "TSU-POL-002",
            "Transaction Processing Policies",
            "operations",
            "4.0",
            policies
        )

    # =========================================================================
    # DOCUMENT 4: CUSTOMER SERVICE FAQ (FAQ-001) — UNCHANGED
    # =========================================================================

    def generate_faq_document(self) -> Dict:
        faq = f"""
=========================================================================
{self.bank_name} - CUSTOMER SERVICE FAQ
=========================================================================

Document ID     : FAQ-001
Version         : 2.0
Last Updated    : {self.display_date}
Classification  : Public -- Customer-Facing & Agent Reference


=========================================================================
SECTION 1: TRANSFER & PAYMENT ISSUES
=========================================================================

Q1: My transfer was debited but the receiver did not get the money.
A: This usually indicates a NIBSS network delay or failed interbank
   transaction (transaction_status = "failed" or "timeout").
   Step 1: Wait 2 hours -- most delays self-resolve via auto-reversal.
   Step 2: Check your transaction history in the app for the reference.
   Step 3: If unresolved after 2 hours, contact us with your reference.
   Common failure reasons: network_error, system_timeout, issuer_unavailable.

Q2: I sent money to the wrong account. Can it be reversed?
A: Reversal is NOT automatic for wrong-account transfers.
   Step 1: Contact the recipient directly and request voluntary refund.
   Step 2: Contact TSU with evidence (screenshot of intended vs. actual).
   Step 3: TSU will formally request recall from the beneficiary bank.
   Recovery takes 2-14 days. Not possible if recipient has withdrawn funds.

Q3: What are my daily transfer limits?
A:  Tier 1 (basic savings, phone + name)  : N50,000/day
    Tier 2 (savings/solo, BVN + NIN)      : N200,000/day
    Tier 3 (current account, full KYC)    : N5,000,000/day
    If exceeded: failure_reason = "daily_transaction_limit_exceeded".


=========================================================================
SECTION 2: CARD ISSUES
=========================================================================

Q4: Why was my card declined even though I have sufficient balance?
A: Common reasons:
   1. International transactions disabled (enable in app).
   2. Daily limit exceeded (POS: N500,000, ATM: N100,000 standard).
   3. Incorrect PIN (3 wrong attempts = auto-lock for 24 hours).
   4. Security hold (fraud engine applied risk block).

Q5: The ATM did not dispense cash but my account was debited.
A: ATM dispense error on channel = "atm".
   Report within 24 hours with ATM location, time, and amount.
   Auto-reversal within 24-48 hours after terminal reconciliation.


=========================================================================
SECTION 3: MOBILE APP & DIGITAL BANKING
=========================================================================

Q6: I cannot log into the mobile app.
A: Troubleshoot in order:
   Wrong password -> use "Forgot Password".
   Outdated app -> update via Play Store / App Store.
   Network issue -> toggle airplane mode, clear app cache.
   Account locked -> 3 wrong attempts locks for 30 minutes.
   Still unable -> route complaint to DCS.

Q7: I am not receiving OTPs.
A: 1. Verify registered phone number is correct.
   2. Check SMS spam folder (sender: "SENTINEL" or "SBNK").
   3. Restart phone.
   4. Request email OTP as alternative if available.
   5. Visit branch to update registered phone if incorrect.


=========================================================================
SECTION 4: FRAUD & SECURITY
=========================================================================

Q8: Someone is claiming to be from Sentinel Bank and asking for my PIN.
A: THIS IS A SCAM. Sentinel Bank will NEVER ask for your PIN, password,
   OTP, or credentials via phone, email, or SMS.
   If you shared credentials:
   Step 1: Change password immediately in app.
   Step 2: Block your card via app: Cards -> Block Card.
   Step 3: Call our OFFICIAL number: 0700-SENTINEL.
   Step 4: Email: fraud-desk@sentinelbank.ng.


=========================================================================
SECTION 5: ACCOUNT SERVICES
=========================================================================

Q9: How do I request a bank statement?
A:  Mobile App (FREE, last 90 days): Statements -> Download PDF.
    Email (fee: N50/month): statements@sentinelbank.ng. Response: 24 hours.
    USSD (*737*7#): Last 5 transactions only. Free.
    Branch: Any period. Fee: N100/month. Same-day.

Q10: Why am I being charged monthly fees?
A:  Account maintenance (savings)  : N50/month (waived if balance >= N100,000)
    Account maintenance (current)  : N300/month
    SMS transaction alerts         : N4 per alert (CBN mandatory)
    USSD sessions                  : N6.98 per session
    ATM withdrawals (other banks)  : N65 per withdrawal
    Report unexpected charges to AOD with your statement reference.


=========================================================================
SECTION 6: CONTACT INFORMATION
=========================================================================

24/7 Customer Care     : 0700-SENTINEL (0700-736-8463)
Fraud Emergency        : fraud-desk@sentinelbank.ng (24/7 monitoring)
Complaints             : complaints@sentinelbank.ng
Statement Requests     : statements@sentinelbank.ng
Banking Hours          : Mon-Fri 8:00 AM - 4:00 PM
                         Saturday (selected branches): 9:00 AM - 1:00 PM


=========================================================================
END OF DOCUMENT FAQ-001
=========================================================================
"""
        return self._package_for_rag(
            "FAQ-001",
            "Customer Service Frequently Asked Questions",
            "knowledge_base",
            "2.0",
            faq
        )

    # =========================================================================
    # DOCUMENT 5: MERCHANT RISK PROFILES (FRM-002) — UNCHANGED
    # =========================================================================

    def generate_merchant_risk_profiles(self) -> Dict:
        profiles = f"""
=========================================================================
{self.bank_name} - MERCHANT RISK PROFILES
=========================================================================

Document Code       : FRM-002
Classification      : CONFIDENTIAL -- Sentinel Agent Operational Reference
Version             : 1.0
Effective Date      : January 2026
Review Frequency    : Monthly

Document Owner      : Chief Risk Officer (CRO)
Companion Document  : FRM-001 (Fraud Detection & Prevention Guidelines)

USAGE BY SENTINEL AGENT:
  This document provides merchant_category risk weights added to the base
  risk score from FRM-001. Query with merchant_category field from
  transactions.csv, add the returned weight to the total risk score.


=========================================================================
SECTION 1: MERCHANT CATEGORY RISK TIERS
=========================================================================

--------------------------------------------------------------------------
TIER 1 -- HIGH RISK MERCHANT CATEGORIES  (+25 points)
--------------------------------------------------------------------------

CATEGORY: fintech
Risk Weight       : +25 points
Known Merchants   : Paystack, Flutterwave, Interswitch, Remita, Monnify
Risk Rationale    : Fintech payment gateways are the primary channel for
                    moving stolen funds out of compromised accounts.
                    High-value fintech transactions from accounts with no
                    prior fintech history are the strongest single fraud
                    signal in this dataset.
Sentinel Agent Rule:
  IF merchant_category = "fintech" AND is_fraud_score = 1:
    Add +25 points to risk score.
  IF merchant_category = "fintech" AND amount > 200000 AND no prior
     fintech transactions:
    Treat as if multiple_failures flag present (+20 additional).
Note on Salary Signals:
  Regular fintech credits (Paystack, Remita, Flutterwave) where
  amount > N200,000 are interpreted as salary/payroll credits.
  These are BEHAVIORAL CONTEXT signals recorded in salary_detected
  and do NOT trigger fraud flags when the account holder is the
  recipient (credit transactions).

--------------------------------------------------------------------------
TIER 2 -- MEDIUM-HIGH RISK MERCHANT CATEGORIES  (+15 points)
--------------------------------------------------------------------------

CATEGORY: transport
Risk Weight       : +15 points
Known Merchants   : Uber, Bolt, LagRide, ABC Transport, Peace Mass Transit
Risk Rationale    : Transport platforms used as card-testing venues.
                    Multiple transport transactions in a short window
                    is a card-testing indicator.
Note on Uber Tracker:
  Uber/Bolt/LagRide transactions are counted in uber_tracker. This
  counter is a BEHAVIORAL CONTEXT signal stored for explainability.
  Frequent ride-hailing (>= 6 in 90 days) indicates regular commuter
  behaviour, not fraud.

CATEGORY: education
Risk Weight       : +15 points
Known Merchants   : University Tuition, WAEC, JAMB, Private School Fees
Risk Rationale    : Education payments are legitimate but frequently used
                    in social engineering scams.

CATEGORY: healthcare
Risk Weight       : +15 points
Known Merchants   : Teaching Hospital, Private Hospital, Medplus, HealthPlus
Risk Rationale    : Large healthcare payments can be scam cover payments.

--------------------------------------------------------------------------
TIER 3 -- LOW RISK MERCHANT CATEGORIES  (+5 points)
--------------------------------------------------------------------------

CATEGORY: telecoms
Risk Weight       : +5 points
Known Merchants   : MTN, Airtel, Glo, 9mobile
Risk Rationale    : Generally low-risk but can indicate money-laundering
                    via airtime resale at very high volumes.

--------------------------------------------------------------------------
TIER 4 -- ZERO-RISK MERCHANT CATEGORIES  (0 points)
--------------------------------------------------------------------------
These categories are established, everyday spending patterns. No additional
risk weight is added to the fraud score for transactions in these categories.

CATEGORY: supermarket   | Risk Weight: 0 | Merchants: Shoprite, SPAR, Justrite, Ebeano, Market Square
CATEGORY: restaurants   | Risk Weight: 0 | Merchants: Chicken Republic, Kilimanjaro, Mr Biggs, Dominos, Cold Stone, Bukka Hut
CATEGORY: fuel          | Risk Weight: 0 | Merchants: NNPC Mega Station, TotalEnergies, Mobil, Oando, Conoil, MRS
CATEGORY: utilities     | Risk Weight: 0 | Merchants: Ikeja Electric, EKEDC, IBEDC, AEDC, DSTV, GOtv, StarTimes


=========================================================================
SECTION 2: MERCHANT VELOCITY RULES
=========================================================================

First Transaction with New Merchant
  Condition     : No prior transaction with this merchant_name
  Risk Weight   : +10 points

Repeated Transactions to Same Merchant in Short Window
  Condition     : 3+ transactions to same merchant within 60 minutes
  Risk Weight   : +20 points

Large Single Transaction with New Merchant
  Condition     : Amount > N100,000 AND merchant is new to this account
  Risk Weight   : +25 points


=========================================================================
SECTION 3: COMPOSITE RISK SCORE EXAMPLES
=========================================================================

EXAMPLE 1 -- FINTECH HIGH RISK:
  mobile_channel_risk  : +15
  high_amount_spike    : +25
  fintech merchant     : +25
  First fintech txn    : +10
  Total                : 75 -> HIGH -> Mandatory push-to-app challenge

EXAMPLE 2 -- TRANSPORT CARD TESTING:
  multiple_failures    : +20
  transport merchant   : +15
  3 txns in 30 min     : +20
  Total                : 55 -> MEDIUM -> Step-up OTP authentication

EXAMPLE 3 -- SUPERMARKET NORMAL:
  normal_pattern       : 0
  supermarket          : 0
  Regular merchant     : 0
  Total                : 0 -> LOW -> Process without friction


=========================================================================
SECTION 4: MERCHANT CATEGORY TO DEPARTMENT ROUTING
=========================================================================

  Merchant Category  -> Primary Department  -> Escalate if Fraud
  -------------------------------------------------------------------------
  fintech            -> TSU (disputed txn)  -> FRM (if is_fraud_score = 1)
  transport          -> COC (if card used)  -> FRM (if is_fraud_score = 1)
  supermarket        -> COC (if POS issue)  -> TSU (if transfer issue)
  restaurants        -> COC (if POS issue)  -> TSU (if transfer issue)
  fuel               -> COC (if POS issue)  -> TSU (if transfer issue)
  utilities          -> TSU (bill payment)  -> AOD (if charge disputed)
  telecoms           -> TSU (airtime/data)  -> DCS (if USSD channel)
  education          -> TSU (bank transfer) -> FRM (if scam suspected)
  healthcare         -> TSU (bank transfer) -> FRM (if scam suspected)


=========================================================================
DOCUMENT CONTROL
=========================================================================

Owner           : Chief Risk Officer (CRO)
Review Freq     : Monthly
Last Updated    : {self.display_date}
Emergency       : fraud-desk@sentinelbank.ng | +234-1-FRAUD-24 (24/7)


=========================================================================
END OF DOCUMENT FRM-002
=========================================================================
"""
        return self._package_for_rag(
            "FRM-002",
            "Merchant Risk Profiles",
            "security",
            "1.0",
            profiles
        )

    # =========================================================================
    # DOCUMENT 6: PRODUCT RECOMMENDATION POLICY (PRS-001) — v2 REWRITE
    # =========================================================================

    def generate_product_recommendation_policy(self) -> Dict:
        """
        v2 rewrite aligned to data_generator.py v2 (balanced assignment model).

        Key changes from v1:
          - 5 products: Student Loan, Car Loan, Investment Plan,
            Trust Fund, Personal Loan (was 3: Car Loan, Personal Loan,
            Investment Plan).
          - Field renamed: car_loan_signal_score -> Loan_signal_score
            (capital L, generic across all products).
          - Score model changed: Loan_signal_score is PRE-ASSIGNED per
            product within a fixed range; it is not computed at runtime
            from behavioral signals.
          - Assignment model: balanced (600 customers per product,
            3000 total) rather than threshold-based.
          - Behavioral signals (salary_detected, uber_tracker,
            monthly_inflow) retained as CONTEXT for explainability
            but do not gate the recommendation.
          - None is no longer a valid recommended_product value.
        """
        policy = f"""
=========================================================================
{self.bank_name} - PRODUCT RECOMMENDATION POLICY
=========================================================================

Document Code       : PRS-001
Classification      : Internal -- Trajectory Agent Operational Reference
Version             : 2.0
Effective Date      : February 2026
Review Frequency    : Quarterly

Document Owner      : Head of Retail Banking Products
Companion Documents : TSU-POL-002 (Transaction Policies),
                      POL-CCH-001 (Complaint Handling Policy),
                      FRM-002 (Merchant Risk Profiles)


=========================================================================
SECTION 1: OVERVIEW OF CHANGES FROM VERSION 1.0
=========================================================================

This document supersedes PRS-001 v1.0. The following changes are in
effect from February 2026:

1. PRODUCT EXPANSION
   The product suite expanded from 3 to 5 products. Two new products
   were introduced:
     - Student Loan  (for solo_candidate customers, ages 18-25)
     - Trust Fund    (wealth-preservation product for high-inflow
                      and high-balance customers)

2. FIELD RENAME
   The field car_loan_signal_score (a Car Loan-specific computed score)
   has been renamed to Loan_signal_score (capital L). This field is now
   generic and applies to all five products. The field name in
   transactions.csv is "Loan_signal_score".

3. SCORE MODEL CHANGE
   Version 1 computed car_loan_signal_score from three behavioral
   signals at runtime:
     uber_tracker >= 6    -> +0.4
     salary_detected      -> +0.3
     monthly_inflow > 500K -> +0.3
   Version 2 pre-assigns Loan_signal_score from a fixed range
   determined by the customer's assigned product. The score is locked
   at data generation and stored in transactions.csv. It is not
   recomputed by the agent.

4. ASSIGNMENT MODEL CHANGE
   Version 1 used threshold-based assignment (compute signals, check
   thresholds, assign product based on which threshold fires first).
   Version 2 uses balanced random assignment: 3000 customers are
   shuffled and split evenly across 5 products (600 per product).
   The Loan_signal_score range is then set per-product.

5. BEHAVIORAL SIGNALS RECLASSIFIED
   salary_detected, uber_tracker, and monthly_inflow_tracker are still
   computed and stored in transactions.csv. They are now CONTEXT signals
   used for explainability and credit assessment, not eligibility gates.

6. ELIMINATION OF "None" RECOMMENDATION
   All 3000 customers in the dataset receive a product recommendation.
   recommended_product = None no longer appears in transactions.csv.


=========================================================================
SECTION 2: PRODUCT CLASSES AND LOAN_SIGNAL_SCORE RANGES
=========================================================================

The following five products constitute the full product suite. Each
product has a fixed Loan_signal_score range set in data_generator.py.
The floor of each range is the minimum score for APPROVED eligibility.

PRODUCT CLASSES (exact values from data_generator.py PRODUCT_CLASSES):
  "Student Loan"
  "Car Loan"
  "Investment Plan"
  "Trust Fund"
  "Personal Loan"

LOAN_SIGNAL_SCORE_RANGES (exact values from data_generator.py):
  Product          Floor   Ceiling   Description
  -----------------------------------------------------------------------
  Student Loan     0.80    0.98      Highest range -- young borrowers
                                     with strong educational intent signal
  Car Loan         0.75    0.95      High range -- strong transport and
                                     income profile
  Personal Loan    0.70    0.92      Mid range -- stable salary income,
                                     general credit profile
  Investment Plan  0.70    0.90      Mid range -- high inflow, wealth
                                     accumulation behavior
  Trust Fund       0.65    0.85      Lowest range -- entry-level wealth-
                                     preservation product

ELIGIBILITY RULE (applied by Trajectory Agent):
  Loan_signal_score >= floor for the assigned product -> APPROVED
  Loan_signal_score  < floor for the assigned product -> NOT_ELIGIBLE

The floor threshold is the single criterion that determines eligibility
for each product. It replaces the multiple threshold checks in v1.


=========================================================================
SECTION 3: PRODUCT ELIGIBILITY DETAILS
=========================================================================

--------------------------------------------------------------------------
PRODUCT: Student Loan
--------------------------------------------------------------------------
Loan_signal_score Range    : 0.80 -- 0.98
Floor Threshold            : 0.80
Department                 : CLS (Credit & Loan Services)
KYC Tier Required          : Tier 2 minimum (solo account, BVN + NIN)
Target Demographic         : solo_candidate = True in customers.csv
                             Age range 18-25 (solo account band)

TARGET CUSTOMER PROFILE:
  The Student Loan is designed for customers in the solo_candidate
  segment. In the dataset, solo_candidate = True for the first 1000
  customers generated (ages 18-25). Solo accounts are opened alongside
  savings accounts for customers aged 16-30.

  The high Loan_signal_score floor (0.80) reflects the higher
  institutional risk of lending to young borrowers: only customers with
  a strong behavioral fit (regular transactions, consistent inflow,
  active account usage) qualify.

BEHAVIORAL CONTEXT SIGNALS:
  age (18-25)               : Primary indicator of student profile
  salary_detected           : Not required (students may not have salary)
  monthly_inflow            : Low expected (student income is typically
                              irregular or from family transfers)
  uber_tracker              : Not a primary signal for this product

ADDITIONAL POLICY REQUIREMENTS (for Human Credit Officers):
  - Admission letter or student ID from accredited institution required
  - Guarantor required (parent or guardian if age < 21)
  - Maximum loan amount: N2,000,000 (tuition and living expenses)
  - Tenor: Up to 4 years (academic program duration)
  - Repayment: Deferred until 12 months after graduation (grace period)
  - Account type: solo or savings (current not required)

EXAMPLE VALIDATION:
  Customer: age=21, Loan_signal_score=0.88, solo_candidate=True
  Result: APPROVED (0.88 >= 0.80 floor)
  Customer: age=23, Loan_signal_score=0.74, solo_candidate=True
  Result: NOT_ELIGIBLE (0.74 < 0.80 floor)


--------------------------------------------------------------------------
PRODUCT: Car Loan
--------------------------------------------------------------------------
Loan_signal_score Range    : 0.75 -- 0.95
Floor Threshold            : 0.75
Department                 : CLS (Credit & Loan Services)
KYC Tier Required          : Tier 2 minimum

TARGET CUSTOMER PROFILE:
  The Car Loan targets customers with a demonstrated ability to service
  loan repayments and a behavioral profile consistent with vehicle need.
  The high floor (0.75) filters for customers with strong income and
  transport-related spending patterns.

BEHAVIORAL CONTEXT SIGNALS (stored in transactions.csv for explainability):
  uber_tracker      : Frequent ride-hailing (>= 6 in 90 days) signals
                      lack of personal vehicle and latent vehicle demand.
                      This was the primary signal in v1 (+0.4 score add).
                      In v2 it is context only.
  salary_detected   : 2+ fintech credits > N200,000 indicate stable
                      salary income. Context for credit assessment.
  monthly_inflow    : Cumulative credit total. Context for repayment
                      capacity assessment.

ADDITIONAL POLICY REQUIREMENTS (for Human Credit Officers):
  - Minimum account age    : 12 months with Sentinel Bank
  - Minimum age            : 21 years
  - Maximum age at maturity: 60 years
  - Maximum loan amount    : N15,000,000
  - Tenor                  : 12 to 60 months
  - Collateral             : Vehicle being financed (chattel mortgage)

EXAMPLE VALIDATION:
  Customer: Loan_signal_score=0.82, salary_detected=True
  Result: APPROVED (0.82 >= 0.75 floor)
  Customer: Loan_signal_score=0.60, salary_detected=False
  Result: NOT_ELIGIBLE (0.60 < 0.75 floor)


--------------------------------------------------------------------------
PRODUCT: Investment Plan
--------------------------------------------------------------------------
Loan_signal_score Range    : 0.70 -- 0.90
Floor Threshold            : 0.70
Department                 : CLS (Credit & Loan Services)
KYC Tier Required          : Tier 3 preferred (current account)

TARGET CUSTOMER PROFILE:
  The Investment Plan targets customers with high net cash inflow who
  have the financial headroom to invest rather than borrow. In v1,
  monthly_inflow > N2,000,000 was the single eligibility gate. In v2,
  this context is preserved for credit assessment but the primary
  eligibility check is Loan_signal_score >= 0.70.

BEHAVIORAL CONTEXT SIGNALS:
  monthly_inflow > N2,000,000 : Strong indicator of investment capacity.
                                  Preserved as context for relationship
                                  managers. Does not gate eligibility in v2.
  salary_detected             : Consistent income source context.

AVAILABLE INVESTMENT PRODUCTS:
  - Fixed Deposit (30, 60, 90, 180, 365-day tenors)
  - Treasury Bill participation (via Sentinel Bank treasury desk)
  - Mutual Fund (money market, equity, balanced)
  - Dollar Fixed Deposit (domiciliary account required)

ADDITIONAL POLICY REQUIREMENTS (for Relationship Managers):
  - KYC tier           : Tier 3 required for full product access
  - Minimum investment : N500,000 (Fixed Deposit), N100,000 (Mutual Fund)
  - NDIC coverage      : Fixed deposits covered up to N5,000,000

EXAMPLE VALIDATION:
  Customer: Loan_signal_score=0.78, monthly_inflow=2,500,000
  Result: APPROVED (0.78 >= 0.70 floor)
  Customer: Loan_signal_score=0.62, monthly_inflow=3,000,000
  Result: NOT_ELIGIBLE (0.62 < 0.70 floor; inflow is context only)


--------------------------------------------------------------------------
PRODUCT: Trust Fund
--------------------------------------------------------------------------
Loan_signal_score Range    : 0.65 -- 0.85
Floor Threshold            : 0.65
Department                 : CLS (Credit & Loan Services)
KYC Tier Required          : Tier 3 (current account with full KYC)

TARGET CUSTOMER PROFILE:
  The Trust Fund is a wealth-preservation product for customers with
  significant accumulated assets or high monthly inflow. It has the
  lowest floor (0.65) of all five products, reflecting that the
  product is accessible to a broader range of financially stable
  customers who may not yet have the highest loan signal scores.

PURPOSE AND STRUCTURE:
  A Trust Fund at Sentinel Bank is a discretionary managed account
  where funds are invested and managed on behalf of the customer or
  named beneficiaries. It differs from the Investment Plan in that:
  - The beneficiary may differ from the account holder (estate planning)
  - Funds are locked for a defined trust period (minimum 2 years)
  - Professional fund management is provided by the Sentinel Bank
    Treasury and Wealth Management desk
  - Suitable for estate planning, children's education funds, and
    long-term wealth transfer

BEHAVIORAL CONTEXT SIGNALS:
  monthly_inflow >= N1,000,000 : Indicates high-net-worth profile.
                                   Stored as context for wealth managers.
  account_type = "current"     : Strong indicator of Tier 3 customer.
  current_balance > N5,000,000 : Consistent high balance supports
                                   wealth management relationship.

ADDITIONAL POLICY REQUIREMENTS (for Wealth Management Officers):
  - Minimum fund size         : N2,000,000 initial deposit
  - Trust period              : Minimum 2 years, no early withdrawal
  - Beneficiary designation   : Up to 5 named beneficiaries
  - Legal documentation       : Trust deed required (prepared by Sentinel
                                 Bank's legal department)
  - Annual management fee     : 1.5% of fund value per annum
  - Returns                   : Variable (linked to investment performance)

EXAMPLE VALIDATION:
  Customer: Loan_signal_score=0.73, monthly_inflow=1,200,000
  Result: APPROVED (0.73 >= 0.65 floor)
  Customer: Loan_signal_score=0.50, monthly_inflow=500,000
  Result: NOT_ELIGIBLE (0.50 < 0.65 floor)


--------------------------------------------------------------------------
PRODUCT: Personal Loan
--------------------------------------------------------------------------
Loan_signal_score Range    : 0.70 -- 0.92
Floor Threshold            : 0.70
Department                 : CLS (Credit & Loan Services)
KYC Tier Required          : Tier 2 minimum

TARGET CUSTOMER PROFILE:
  The Personal Loan targets customers with stable income and a
  general credit need not covered by a specialized loan product.
  In v1, it was the fallback product for salary-earners whose
  car_loan_signal_score was below 0.7. In v2, it is an independent
  product class with its own customer segment (600 customers).

  The Personal Loan and Investment Plan share the same floor threshold
  (0.70). The distinction between them is the customer's inflow profile:
  Personal Loan customers typically have moderate monthly inflow
  (N300,000-N2,000,000) while Investment Plan customers typically
  exceed N2,000,000. These are context distinctions -- the floor
  threshold (0.70) is the primary eligibility check for both.

BEHAVIORAL CONTEXT SIGNALS:
  salary_detected             : Strong context signal for repayment
                                  capacity. Not an eligibility gate in v2.
  monthly_inflow >= N300,000  : Moderate inflow context. Not a gate.

ADDITIONAL POLICY REQUIREMENTS (for Human Credit Officers):
  - Debt-to-income ratio       : DTI < 40% (outstanding vs income)
  - Minimum age                : 21 years
  - Maximum loan amount        : N5,000,000 (formal CLS assessment)
  - Tenor                      : 6 to 48 months
  - No collateral required     : Up to N1,000,000 (unsecured)
                                 Collateral required above N1,000,000

EXAMPLE VALIDATION:
  Customer: Loan_signal_score=0.71, salary_detected=True, inflow=450,000
  Result: APPROVED (0.71 >= 0.70 floor)
  Customer: Loan_signal_score=0.65, salary_detected=True, inflow=600,000
  Result: NOT_ELIGIBLE (0.65 < 0.70 floor; salary and inflow are context)


=========================================================================
SECTION 4: BEHAVIORAL CONTEXT SIGNALS
=========================================================================

The following signals are computed in data_generator.py and stored in
transactions.csv. They are available to the Trajectory Agent for
generating explanations and supporting credit decisions but do NOT
determine APPROVED or NOT_ELIGIBLE outcomes in the v2 model.

salary_detected:
  Definition    : salary_tracker[customer_id] >= 2.
                  Two or more credit transactions where amount > N200,000
                  AND merchant_category = "fintech" on this account.
  Merchants     : Paystack, Flutterwave, Interswitch, Remita, Monnify
  Context use   : Strong indicator of salaried employment for Personal
                  Loan and Car Loan credit assessment.
  Note          : salary_detected = False does NOT mean no income.
                  Cash deposits and branch credits are not counted.

uber_tracker:
  Definition    : Count of transactions where merchant_name is "Uber",
                  "Bolt", or "LagRide".
  Context use   : Frequent ride-hailing (>= 6 in 90 days) indicates
                  lack of personal vehicle -- relevant context for Car
                  Loan credit officers. Also flagged as a positive
                  transport signal in FRM-002 (reduces transport
                  merchant suspicion for established commuters).

monthly_inflow_tracker:
  Definition    : Cumulative sum of all credit transaction amounts
                  for this customer_id across all accounts.
  Context use   : Used by relationship managers to assess capacity.
                  Bands that remain relevant for context:
                    > N300,000  : Moderate inflow (Personal Loan context)
                    > N500,000  : Strong inflow (Car Loan context)
                    > N2,000,000 : High inflow (Investment Plan context)
                    > N1,000,000 : High-net-worth indicator (Trust Fund)


=========================================================================
SECTION 5: RECOMMENDATION HIERARCHY
=========================================================================

When a customer's behavioral context suggests qualification for multiple
products simultaneously, use this priority order for the Trajectory
Agent's primary recommendation. This hierarchy is for reference when
deploying a LIVE recommendation engine; the v2 dataset uses balanced
pre-assignment and does not apply this hierarchy at generation time.

  PRIORITY 1: Investment Plan  (monthly_inflow context > N2,000,000)
  PRIORITY 2: Trust Fund       (high balance + long-term customer)
  PRIORITY 3: Car Loan         (uber_tracker >= 6 OR strong inflow)
  PRIORITY 4: Personal Loan    (salary_detected + moderate inflow)
  PRIORITY 5: Student Loan     (age 18-25, solo_candidate = True)


=========================================================================
SECTION 6: VALIDATION AGAINST COMPLAINTS DATASET
=========================================================================

Before finalizing any product recommendation, the Trajectory Agent
must check complaints.csv for the customer:

  If active fraud complaints exist
  (fraud_related = 1, complaint_status = "open" or "escalated"):
    -> DO NOT make product recommendations until resolved.
    -> Flag account for FRM review.

  If SLA breach complaints exist (sla_breach_flag = 1):
    -> Note service quality issue in recommendation report.
    -> Route service quality concern to the breaching department.


=========================================================================
SECTION 7: SAMPLE OUTPUT FORMAT FOR TRAJECTORY AGENT
=========================================================================

PRODUCT RECOMMENDATION REPORT
--------------------------------------------------------------------------
Customer        : [Full Name] | ID: [customer_id]
Account Type    : [savings / solo / current]
Age             : [X] years

ELIGIBILITY ASSESSMENT (per PRS-001 v2.0):
  Assigned Product         : [Product Name]
  Loan_signal_score        : [X.XX] (field: transactions.csv "Loan_signal_score")
  Score Range for Product  : [floor] -- [ceiling]
  Recommendation           : [APPROVED / NOT_ELIGIBLE]

BEHAVIORAL CONTEXT (for credit officer reference -- not eligibility gates):
  salary_detected          : [True / False]
  uber_tracker             : [X] ride-hailing transactions
  monthly_inflow           : N[X,XXX,XXX] cumulative

CRITERIA MET:
  [List each criterion met with actual vs. threshold value]

CRITERIA UNMET (if NOT_ELIGIBLE):
  [List each criterion not met with gap to threshold]

COMPLIANCE FLAGS:
  Active Fraud Complaints  : [Yes / No]
  SLA Breaches on Account  : [X] breaches in last 90 days

Policy Reference           : {self.bank_name} PRS-001 v2.0 ({self.display_date})
--------------------------------------------------------------------------


=========================================================================
DOCUMENT CONTROL
=========================================================================

Policy Owner    : Head of Retail Banking Products
Approver        : Chief Retail Banking Officer
Review Cycle    : Quarterly
Version History : v1.0 January 2026 (3 products, threshold model)
                  v2.0 February 2026 (5 products, score-range model)
Last Updated    : {self.display_date}
Contact         : retailproducts@sentinelbank.ng | Ext. 6000


=========================================================================
END OF DOCUMENT PRS-001
=========================================================================
"""
        return self._package_for_rag(
            "PRS-001",
            "Product Recommendation Policy",
            "policy",
            "2.0",
            policy
        )

    # =========================================================================
    # ORCHESTRATION
    # =========================================================================

    def generate_all_documents(self) -> List[Dict]:
        return [
            self.generate_complaint_handling_policy(),
            self.generate_fraud_detection_guidelines(),
            self.generate_transaction_policies(),
            self.generate_faq_document(),
            self.generate_merchant_risk_profiles(),
            self.generate_product_recommendation_policy()
        ]

    def save_all_policies(self, output_dir: Path):
        output_dir = Path(output_dir)
        policies_dir = output_dir / "policies"
        faqs_dir = output_dir / "faqs"

        policies_dir.mkdir(parents=True, exist_ok=True)
        faqs_dir.mkdir(parents=True, exist_ok=True)

        documents = self.generate_all_documents()

        print(f"\nGenerating {len(documents)} policy documents...")
        print("=" * 60)

        for doc in documents:
            if doc['category'] == 'knowledge_base':
                target_folder = faqs_dir
            else:
                target_folder = policies_dir

            filename = f"{doc['document_id']}.txt"
            filepath = target_folder / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(doc['content'])

            size_kb = len(doc['content'].encode('utf-8')) / 1024
            print(f"  {doc['document_id']}.txt  "
                  f"({doc['title'][:40]})  [{size_kb:.1f} KB]")

        print("=" * 60)
        policy_count = len([d for d in documents if d['category'] != 'knowledge_base'])
        faq_count = len([d for d in documents if d['category'] == 'knowledge_base'])
        print(f"\n  Policies saved : {policy_count} files -> {policies_dir}")
        print(f"  FAQs saved     : {faq_count} file  -> {faqs_dir}")
        print(f"\nAll {len(documents)} documents ready for RAG ingestion.")


# =============================================================================
# DATASET PATHS
# =============================================================================

DATASET_DIR      = Path("app/sentinel bank dataset")
CUSTOMERS_CSV    = DATASET_DIR / "customers.csv"
ACCOUNTS_CSV     = DATASET_DIR / "accounts.csv"
TRANSACTIONS_CSV = DATASET_DIR / "transactions.csv"
COMPLAINTS_CSV   = DATASET_DIR / "complaints.csv"


# =============================================================================
# MAIN EXECUTION BLOCK
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  SENTINEL BANK -- POLICY DOCUMENT GENERATOR v3")
    print("  AI Engineer 2 | Week 1 Knowledge Base Setup")
    print("  Documents: 6 (4 original + FRM-002 + PRS-001 v2)")
    print("=" * 60)

    print("\nVerifying dataset paths...")
    all_found = True
    for csv_path in [CUSTOMERS_CSV, ACCOUNTS_CSV, TRANSACTIONS_CSV, COMPLAINTS_CSV]:
        exists = csv_path.exists()
        status = "Found" if exists else "MISSING"
        print(f"  {status}  {csv_path}")
        if not exists:
            all_found = False

    if not all_found:
        print(
            f"\nOne or more dataset files not found under '{DATASET_DIR}'.\n"
            f"Update the DATASET_DIR constant at the top of this file.\n"
            f"Policy documents will still be generated regardless.\n"
        )

    print()
    current_dir = Path(__file__).parent
    generator = BankingPolicyGenerator(bank_name="Sentinel Bank Nigeria")
    generator.save_all_policies(current_dir)

    print("\nGenerated Documents:")
    print("  policies/POL-CCH-001.txt -- Complaint Handling (Dispatcher)")
    print("  policies/FRM-001.txt     -- Fraud Detection (Sentinel base)")
    print("  policies/TSU-POL-002.txt -- Transaction Policies (All agents)")
    print("  policies/FRM-002.txt     -- Merchant Risk Profiles (Sentinel)")
    print("  policies/PRS-001.txt     -- Product Recommendations v2 (Trajectory)")
    print("  faqs/FAQ-001.txt         -- Customer FAQ")
    print("=" * 60 + "\n")
