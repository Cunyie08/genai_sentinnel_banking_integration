import uuid
import random
import numpy as np
import pandas as pd
from faker import Faker
from datetime import datetime, timedelta
from collections import defaultdict

fake = Faker()
CURRENT_YEAR = 2026
NUM_CUSTOMERS = 3000
TARGET_SOLO_CUSTOMERS = 1000

PRODUCT_CLASSES = [
    "Student Loan",
    "Car Loan",
    "Investment Plan",
    "Trust Fund",
    "Personal Loan"
]

# ==========================================================
# UNIQUE TRACKERS
# ==========================================================

used_customer_ids    = set()
used_emails          = set()
used_phones          = set()
used_bvns            = set()
used_nins            = set()
used_account_numbers = set()
used_usernames       = set()

# ==========================================================
# TELECOM PROVIDERS
# ==========================================================

TELCO_PREFIXES = {
    "MTN":    ["0803","0806","0703","0706","0813","0810","0903","0906"],
    "Airtel": ["0802","0808","0708","0812","0902","0907"],
    "Glo":    ["0805","0807","0705","0815","0905"],
    "9mobile":["0809","0817","0818","0909","0908"]
}

STATES = [
    "Abia","Adamawa","Akwa Ibom","Anambra","Bauchi","Bayelsa",
    "Benue","Borno","Cross River","Delta","Ebonyi","Edo",
    "Ekiti","Enugu","Gombe","Imo","Jigawa","Kaduna",
    "Kano","Katsina","Kebbi","Kogi","Kwara","Lagos",
    "Nasarawa","Niger","Ogun","Ondo","Osun","Oyo",
    "Plateau","Rivers","Sokoto","Taraba","Yobe","Zamfara"
]

MALE_NAMES = [
    "Ade","Chris","Abdullahi","Oludayo","Mubarak","Uche",
    "Emeka","Michael","Taofeek","Sunday","Seyi",
    "Reuben","Olatunji","Solomon","Kehinde","Victor"
]
FEMALE_NAMES = [
    "Zainab","Naheemat","Aisha","Aminat","Glory",
    "Joy","Anna","Mary","Esther","Blossom",
    "Perpetual","Aaliyah","Funke","Funmilola",
    "Titilope","Halimah","Mariam"
]
LAST_NAMES = [
    "Ekwugum","Oluwole","Adebiyi","Onyekachi","Badrudeen",
    "Willie","David","Ekpo","Friday","Hassan","Ajayi",
    "Tijani","Bello","Lawal","Williams","Garba",
    "Abubakar","Umar","Yusuf","Musa","Adeleke",
    "Salako","Alimi","Smith","Adebayo","Ajala",
    "Ogunleye","Ogunkoya","Sanni","Shabi",
    "Oladele","Uthman"
]

# ==========================================================
# HELPERS
# ==========================================================

def generate_email(first, last):
    domains = random.choices(
        ["gmail.com","yahoo.com","outlook.com","protonmail.com","10minutemail.com"],
        weights=[70,25,3,1,1]
    )[0]
    while True:
        suffix = str(random.randint(10,999)) if random.random() < 0.35 else ""
        email  = f"{first.lower()}.{last.lower()}{suffix}@{domains}"
        if email not in used_emails:
            used_emails.add(email)
            return email

def generate_phone():
    while True:
        telco  = random.choice(list(TELCO_PREFIXES.keys()))
        prefix = random.choice(TELCO_PREFIXES[telco])
        number = "+234" + prefix[1:] + ''.join(str(random.randint(0,9)) for _ in range(7))
        if number not in used_phones:
            used_phones.add(number)
            return number, telco

def generate_unique_number(pool, digits=11):
    while True:
        num = str(random.randint(10**(digits-1), 10**digits-1))
        if num not in pool:
            pool.add(num)
            return num

def generate_account_number():
    while True:
        acc = str(random.randint(10**9, 10**10-1))
        if acc not in used_account_numbers:
            used_account_numbers.add(acc)
            return acc

def generate_reference():
    return "TXN" + str(random.randint(10**11, 10**12-1))

def generate_device(channel):
    if channel == "mobile_app":
        return "DEV-" + uuid.uuid4().hex[:12].upper()
    return None

def generate_username(first: str, last: str) -> str:
    """
    Generate a unique username in the format: firstname.lastname
    or firstname.lastnameNN if the base is already taken.
    e.g. ade.ekwugum  or  ade.ekwugum42
    """
    base = f"{first.lower()}.{last.lower()}"
    if base not in used_usernames:
        used_usernames.add(base)
        return base
    for _ in range(1000):
        candidate = f"{base}{random.randint(10, 99)}"
        if candidate not in used_usernames:
            used_usernames.add(candidate)
            return candidate
    # Extreme fallback
    candidate = f"{base}{uuid.uuid4().hex[:4]}"
    used_usernames.add(candidate)
    return candidate

def generate_password(first: str, last: str) -> str:
    """
    Generate a memorable demo password.
    Format: Firstname + first 3 letters of lastname (capitalised) + 4-digit number + !
    e.g.  Ade + Ekw + 4821 + !  →  AdeEkw4821!

    NOTE: Store as plain text here for demo only.
    Hash with bcrypt before storing in a production database.
    """
    pin    = str(random.randint(1000, 9999))
    return f"{first.capitalize()}{last[:3].capitalize()}{pin}!"


CHANNELS = ["mobile_app","ussd","atm","pos","web","branch","nibss_transfer"]
BANKS = [
    "GTBank","Access Bank","Zenith Bank","UBA","First Bank",
    "Fidelity Bank","Union Bank","Sterling Bank","Wema Bank",
    "Opay","Kuda","PalmPay","Providus Bank","Lotus Bank",
    "Premium Trust Bank","Polaris Bank","Stanbic IBTC",
]
STATUS_WEIGHTS = {
    "successful":85, "failed":5, "reversed":3,
    "pending":2, "timeout":2, "queued":2, "processing":1
}
FAILURE_REASONS = [
    "none","insufficient_fund","network_error","system_failure",
    "system_timeout","invalid_account_number",
    "daily_transaction_limit_exceeded",
    "compliance_restriction","suspected_fraud","issuer_unavailable"
]

def generate_status():
    return random.choices(list(STATUS_WEIGHTS.keys()), weights=list(STATUS_WEIGHTS.values()))[0]

def generate_failure(status):
    if status in ["failed","timeout"]:
        return random.choice(FAILURE_REASONS[1:])
    return "none"

def generate_weighted_timestamp(start_date, end_date):
    """
    80% daytime (06:00-22:00), 20% night (22:00-06:00).
    Ensures Sentinel timing_risk (hour 0-5, amount >= ₦100k) fires correctly.
    """
    # Normalize both to datetime so subtraction always works
    if hasattr(start_date, "hour") is False:
        start_date = datetime(start_date.year, start_date.month, start_date.day)
    if hasattr(end_date, "hour") is False:
        end_date = datetime(end_date.year, end_date.month, end_date.day)
    delta_days = max(1, (end_date - start_date).days)
    day_offset = timedelta(days=random.randint(0, delta_days - 1))
    base_date  = start_date + day_offset

    if random.random() < 0.80:
        hour = random.randint(6, 21)
    else:
        hour = random.choice(list(range(22, 24)) + list(range(0, 6)))

    return datetime(base_date.year, base_date.month, base_date.day,
                    hour, random.randint(0,59), random.randint(0,59))


# ==========================================================
# CUSTOMER GENERATION  (includes username + password)
# ==========================================================

customers    = []
solo_counter = 0

for _ in range(NUM_CUSTOMERS):
    while True:
        customer_id = str(uuid.uuid4())
        if customer_id not in used_customer_ids:
            used_customer_ids.add(customer_id)
            break

    if solo_counter < TARGET_SOLO_CUSTOMERS:
        age       = random.randint(18, 25)
        solo_flag = True
        solo_counter += 1
    else:
        age       = random.randint(26, 70)
        solo_flag = False

    gender = random.choice(["male","female"])
    first  = random.choice(MALE_NAMES if gender == "male" else FEMALE_NAMES)
    last   = random.choice(LAST_NAMES)
    dob    = datetime(CURRENT_YEAR - age, random.randint(1,12), random.randint(1,28))

    bvn   = generate_unique_number(used_bvns)
    nin   = generate_unique_number(used_nins)
    phone, telco = generate_phone()
    email    = generate_email(first, last)
    username = generate_username(first, last)
    password = generate_password(first, last)

    customers.append({
        "customer_id":      customer_id,
        "first_name":       first,
        "last_name":        last,
        "full_name":        f"{first} {last}",
        "gender":           gender,
        "age":              age,
        "date_of_birth":    dob.date(),
        "bvn":              bvn,
        "nin":              nin,
        "phone_number":     phone,
        "telco_provider":   telco,
        "email":            email,
        "state_of_origin":  random.choice(STATES),
        "residential_state":random.choice(STATES),
        "banking_branch":   random.choice(STATES),
        "solo_candidate":   solo_flag,
        "onboarding_date":  fake.date_between("-5y", "today"),
        "username":         username,   # ← new
        "password":         password,   # ← new (plain text, hash before prod use)
    })

customers_df = pd.DataFrame(customers)

# ==========================================================
# ACCOUNT GENERATION
# ==========================================================

accounts = []

for _, cust in customers_df.iterrows():
    acc_types = ["savings"]
    if 16 <= cust["age"] <= 30:
        acc_types.append("solo")
    if cust["age"] >= 18:
        acc_types.append("current")

    for acc_type in acc_types:
        if acc_type == "solo":
            balance = random.uniform(10_000, 250_000)
        elif acc_type == "savings":
            balance = random.uniform(30_000, 2_000_000)
        else:
            balance = random.uniform(500_000, 10_000_000)

        accounts.append({
            "account_id":     str(uuid.uuid4()),
            "customer_id":    cust["customer_id"],
            "account_number": generate_account_number(),
            "account_type":   acc_type,
            "currency":       "NGN",
            "current_balance":round(balance, 2),
            "opened_date":    fake.date_between(cust["onboarding_date"], "today"),
        })

accounts_df = pd.DataFrame(accounts)

# ==========================================================
# PROFILE-BASED PRODUCT ASSIGNMENT
# ==========================================================

def assign_product_by_profile(age: int, solo_candidate: bool) -> str:
    if solo_candidate and age <= 25:
        return "Student Loan"
    elif age >= 40:
        return random.choices(
            ["Investment Plan", "Trust Fund", "Car Loan"],
            weights=[40, 35, 25]
        )[0]
    elif age >= 30:
        return random.choices(
            ["Investment Plan", "Car Loan", "Personal Loan"],
            weights=[30, 40, 30]
        )[0]
    elif age >= 21:
        return random.choices(
            ["Car Loan", "Personal Loan", "Investment Plan"],
            weights=[45, 40, 15]
        )[0]
    else:
        return "Personal Loan"

customer_product_map = {}
for _, cust in customers_df.iterrows():
    customer_product_map[cust["customer_id"]] = assign_product_by_profile(
        cust["age"], cust["solo_candidate"]
    )

# ==========================================================
# LOAN_SIGNAL_SCORE — ONCE PER CUSTOMER
# ==========================================================

SCORE_RANGES = {
    "Student Loan":   (0.80, 0.98),
    "Car Loan":       (0.75, 0.95),
    "Investment Plan":(0.70, 0.90),
    "Personal Loan":  (0.70, 0.92),
    "Trust Fund":     (0.65, 0.85),
}

customer_loan_score = {}
for cid, product in customer_product_map.items():
    lo, hi = SCORE_RANGES[product]
    customer_loan_score[cid] = round(random.uniform(lo, hi), 2)

# ==========================================================
# TRANSACTION AMOUNTS SCALED BY PRODUCT TIER
# ==========================================================

AMOUNT_PROFILES = {
    "Student Loan":   {"credit": (5_000,   80_000),  "debit": (2_000,   50_000)},
    "Personal Loan":  {"credit": (50_000,  500_000),  "debit": (30_000,  300_000)},
    "Car Loan":       {"credit": (100_000, 800_000),  "debit": (50_000,  400_000)},
    "Investment Plan":{"credit": (200_000, 3_000_000),"debit": (100_000, 1_000_000)},
    "Trust Fund":     {"credit": (500_000, 5_000_000),"debit": (200_000, 2_000_000)},
}

def generate_amount(product: str, txn_type: str) -> float:
    lo, hi = AMOUNT_PROFILES[product][txn_type]
    return round(max(100, np.random.uniform(lo, hi)), 2)

# ==========================================================
# MERCHANTS
# ==========================================================

MERCHANTS = {
    "supermarket": ["Shoprite","SPAR","Justrite","Ebeano","Market Square"],
    "restaurants": ["Chicken Republic","Kilimanjaro","Mr Biggs","Dominos","Cold Stone","Bukka Hut"],
    "fuel":        ["NNPC Mega Station","TotalEnergies","Mobil","Oando","Conoil","MRS"],
    "transport":   ["Uber","Bolt","LagRide","ABC Transport","Peace Mass Transit"],
    "telecoms":    ["MTN","Airtel","Glo","9mobile"],
    "utilities":   ["Ikeja Electric","EKEDC","IBEDC","AEDC","DSTV","GOtv","StarTimes"],
    "fintech":     ["Paystack","Flutterwave","Interswitch","Remita","Monnify"],
    "education":   ["University Tuition","WAEC","JAMB","Private School Fees"],
    "healthcare":  ["Teaching Hospital","Private Hospital","Medplus","HealthPlus"],
    "betting":     ["BetKing","Bet9ja","SportyBet","1xBet","NairaBet"],
}

HIGH_RISK_MERCHANTS = {"betting", "fintech"}

# ==========================================================
# FRAUD FLAG LOGIC
# ==========================================================

high_risk   = set(random.sample(list(customers_df.customer_id), int(0.05 * NUM_CUSTOMERS)))
medium_risk = set(random.sample(
    [c for c in customers_df.customer_id if c not in high_risk],
    int(0.10 * NUM_CUSTOMERS)
))

def generate_fraud_flags(customer_id, channel, amount, balance, status, hour, merchant_cat):
    if customer_id in high_risk:
        fraud_prob = 0.15
    elif customer_id in medium_risk:
        fraud_prob = 0.05
    else:
        fraud_prob = 0.01

    if merchant_cat in HIGH_RISK_MERCHANTS: fraud_prob *= 2
    if 0 <= hour < 5:                       fraud_prob *= 1.5
    if amount > balance * 0.7:              fraud_prob *= 1.5

    is_fraud = random.random() < min(fraud_prob, 0.80)
    if not is_fraud:
        return 0, "normal_pattern"

    flags = []
    if channel == "mobile_app":                          flags.append("mobile_channel_risk")
    if amount > balance * 0.5:                           flags.append("high_amount_spike")
    if 0 <= hour < 5:                                    flags.append("late_night_transaction")
    if status == "failed":                               flags.append("multiple_failures")
    if merchant_cat in HIGH_RISK_MERCHANTS:              flags.append("new_merchant")
    if customer_id in high_risk and random.random() < 0.4: flags.append("velocity_breach")
    if not flags:                                        flags.append("high_amount_spike")

    return 1, ",".join(flags)

# ==========================================================
# PERSONAL TRACKERS
# ==========================================================

salary_tracker         = defaultdict(int)
uber_tracker_map       = defaultdict(int)
monthly_inflow_tracker = defaultdict(float)
monthly_outflow_tracker= defaultdict(float)

# ==========================================================
# TRANSACTION GENERATION
# ==========================================================

transactions = []

for _, acc in accounts_df.iterrows():
    balance     = acc["current_balance"]
    customer_id = acc["customer_id"]
    product     = customer_product_map[customer_id]
    loan_score  = customer_loan_score[customer_id]

    if product in ("Investment Plan", "Trust Fund"):
        num_txns = random.randint(30, 60)
    elif product == "Student Loan":
        num_txns = random.randint(10, 25)
    else:
        num_txns = random.randint(20, 40)

    opened_date = acc["opened_date"]
    if isinstance(opened_date, str):
        opened_date = datetime.strptime(opened_date, "%Y-%m-%d")
    end_date = datetime.now()

    for _ in range(num_txns):
        channel  = random.choice(CHANNELS)
        device   = generate_device(channel)
        txn_type = random.choice(["debit","credit"])
        amount   = generate_amount(product, txn_type)

        merchant_category = random.choice(list(MERCHANTS.keys()))
        merchant_name     = random.choice(MERCHANTS[merchant_category])

        if txn_type == "credit":
            monthly_inflow_tracker[customer_id] += amount
            if amount > 200_000 and merchant_category == "fintech":
                salary_tracker[customer_id] += 1
        else:
            monthly_outflow_tracker[customer_id] += amount

        if merchant_name in ("Uber","Bolt","LagRide"):
            uber_tracker_map[customer_id] += 1

        salary_detected = salary_tracker[customer_id] >= 2

        status = generate_status()
        if txn_type == "debit":
            amount      = min(amount, balance * 0.7)
            new_balance = balance - amount if status not in ("failed","reversed") else balance
        else:
            new_balance = balance + amount if status not in ("failed","reversed") else balance

        ts   = generate_weighted_timestamp(opened_date, end_date)
        hour = ts.hour

        is_fraud, fraud_trace = generate_fraud_flags(
            customer_id, channel, amount, balance, status, hour, merchant_category
        )

        transactions.append({
            "transaction_id":               str(uuid.uuid4()),
            "transaction_reference_number": generate_reference(),
            "account_id":                   acc["account_id"],
            "customer_id":                  customer_id,
            "channel":                      channel,
            "device_id":                    device,
            "counterparty_bank":            random.choice(BANKS),
            "narration":                    fake.sentence(nb_words=6),
            "transaction_type":             txn_type,
            "amount":                       round(amount, 2),
            "currency":                     "NGN",
            "transaction_balance":          round(new_balance, 2),
            "transaction_status":           status,
            "failure_reason":               generate_failure(status),
            "is_fraud_score":               is_fraud,
            "fraud_explainability_trace":   fraud_trace,
            "merchant_category":            merchant_category,
            "merchant_name":                merchant_name,
            "salary_detected":              salary_detected,
            "Loan_signal_score":            loan_score,
            "recommended_product":          product,
            "transaction_timestamp":        ts,
        })

        balance = new_balance

transactions_df = pd.DataFrame(transactions)

# ==========================================================
# DEPARTMENT DEFINITIONS
# ==========================================================

DEPARTMENTS = {
    "TSU": {"name":"Transaction Services Unit",     "sla_hours":48, "agents":["TSU_A1","TSU_A2","TSU_A3","TSU_A4","TSU_A5"]},
    "COC": {"name":"Card Operations Center",        "sla_hours":48, "agents":["COC_A1","COC_A2","COC_A3"]},
    "FRM": {"name":"Fraud Risk Management",         "sla_hours":24, "agents":["FRM_A1","FRM_A2","FRM_A3"]},
    "DCS": {"name":"Digital Channels Support",      "sla_hours":72, "agents":["DCS_A1","DCS_A2","DCS_A3"]},
    "AOD": {"name":"Account Operations Department", "sla_hours":72, "agents":["AOD_A1","AOD_A2","AOD_A3"]},
    "CLS": {"name":"Credit & Loan Services",        "sla_hours":96, "agents":["CLS_A1","CLS_A2"]},
}

SENTIMENTS         = ["angry","neutral","calm"]
COMPLAINT_CHANNELS = ["call_center","mobile_app","email","branch","social_media"]

def map_transaction_to_department(txn):
    if txn["is_fraud_score"] == 1:
        return "FRM", "Critical"
    if txn["channel"] in ("atm","pos"):
        return "COC", "High"
    if txn["transaction_status"] in ("failed","timeout","reversed"):
        dept = random.choices(["TSU","DCS"], weights=[70,30])[0]
        return dept, "High"
    if txn["merchant_category"] == "education" and txn["transaction_type"] == "credit":
        return "CLS", "Medium"
    if txn["transaction_status"] == "pending":
        return "AOD", "Medium"
    return random.choices(["TSU","COC","AOD","CLS"], weights=[50,20,20,10])[0], "Medium"

account_to_customer = dict(zip(accounts_df["account_id"], accounts_df["customer_id"]))

COMPLAINT_TEMPLATES = {
    "TSU": [
        "My transfer of ₦{amount:,.0f} with reference {ref} was debited but the recipient has not received it.",
        "I was charged ₦{amount:,.0f} but the transaction failed. Please investigate reference {ref}.",
        "This transaction with reference {ref} was reversed incorrectly. I need an urgent refund.",
        "I sent ₦{amount:,.0f} to the wrong account number. The reference is {ref}. Please help me reverse it.",
        "My NIBSS transfer of ₦{amount:,.0f} has been pending for over 24 hours. Reference: {ref}.",
        "I made a payment of ₦{amount:,.0f} via {channel} but it shows failed on my end. Reference {ref}.",
    ],
    "COC": [
        "My card transaction of ₦{amount:,.0f} at POS failed but my account was debited. Ref {ref}.",
        "The ATM transaction of ₦{amount:,.0f} did not dispense cash but I was debited. Ref {ref}.",
        "My card was declined even though I have sufficient balance in my account.",
        "My debit card was swallowed by the ATM machine. I need it returned or replaced immediately.",
        "I am unable to use my card for online transactions. It keeps getting declined.",
        "My card PIN has been blocked after three failed attempts. Please help me reset it.",
    ],
    "FRM": [
        "I noticed an unauthorized transaction of ₦{amount:,.0f}. Reference {ref}. I did not authorize this.",
        "My account appears to have been compromised. This transaction {ref} is suspicious.",
        "I believe I am a victim of fraud. Please freeze my account immediately.",
        "Someone made a transfer from my account without my knowledge. Reference {ref}.",
        "I received a phishing SMS and my account was debited ₦{amount:,.0f} without my consent.",
        "My BVN was used to open an account I did not authorize. Please investigate.",
    ],
    "DCS": [
        "I attempted a transaction of ₦{amount:,.0f} but the mobile app failed with an error.",
        "The banking app crashed during transaction {ref}. My money was deducted but not sent.",
        "I cannot complete transactions via USSD. It keeps saying service unavailable.",
        "I am locked out of my mobile banking app and cannot reset my password.",
        "The Sentinel mobile app keeps crashing whenever I try to log in.",
        "My OTP is not being delivered to my registered phone number for online transactions.",
    ],
    "AOD": [
        "There is an issue with my account balance. It does not reflect my last deposit.",
        "I need clarification on charges deducted from my account this month.",
        "My account has been restricted and I cannot perform any transactions.",
        "I want to upgrade my account tier but the process keeps failing online.",
        "My BVN is not linked to my account despite providing it at the branch.",
        "My account has been dormant and I need help reactivating it.",
    ],
    "CLS": [
        "My loan repayment linked to transaction {ref} was not processed correctly.",
        "There is an issue with my loan disbursement. The amount received is incorrect.",
        "I need clarification regarding the interest rate applied to my loan this month.",
        "I applied for a Car Loan two weeks ago and have not received any update.",
        "My loan account statement does not reflect my last three repayments.",
        "I was told I qualify for a Personal Loan but my application keeps getting rejected.",
    ],
}

def generate_complaint_text(txn, dept_code, sentiment):
    ref      = txn["transaction_reference_number"]
    amount   = float(txn["amount"])
    channel  = txn["channel"].replace("_", " ")
    template = random.choice(COMPLAINT_TEMPLATES.get(dept_code, COMPLAINT_TEMPLATES["TSU"]))
    text     = template.format(amount=amount, ref=ref, channel=channel)

    if sentiment == "angry":
        text = random.choice(["This is absolutely unacceptable. ","I am very frustrated. ","This is outrageous. "]) \
             + text \
             + random.choice([" I need urgent resolution."," I will escalate to CBN."," This is the third time."])
    elif sentiment == "calm":
        text = random.choice(["Kindly assist. ","Good day, ","Please help me. "]) + text

    return text

# ==========================================================
# COMPLAINT GENERATION
# ==========================================================

complaints        = []
complaint_counter = 1

for _, txn in transactions_df.iterrows():
    prob = 0.85 if txn["is_fraud_score"] == 1 else 0.15
    if random.random() > prob:
        continue

    customer_id = account_to_customer.get(txn["account_id"])
    if customer_id not in set(customers_df["customer_id"]):
        continue

    dept_code, priority = map_transaction_to_department(txn)
    dept                = DEPARTMENTS[dept_code]
    sentiment = "angry" if priority == "Critical" else random.choices(SENTIMENTS, weights=[0.3,0.4,0.3])[0]

    complaint_time   = txn["transaction_timestamp"] + timedelta(minutes=random.randint(5,720))
    resolution_hours = random.randint(2, dept["sla_hours"] + 48)
    resolution_time  = complaint_time + timedelta(hours=resolution_hours)

    complaints.append({
        "complaint_id":          f"CMP-{str(complaint_counter).zfill(6)}",
        "customer_id":           customer_id,
        "account_id":            txn["account_id"],
        "linked_transaction_id": txn["transaction_id"],
        "linked_reference":      txn["transaction_reference_number"],
        "department_code":       dept_code,
        "department_name":       dept["name"],
        "priority_level":        priority,
        "sentiment":             sentiment,
        "complaint_channel":     random.choice(COMPLAINT_CHANNELS),
        "assigned_agent_id":     random.choice(dept["agents"]),
        "complaint_timestamp":   complaint_time,
        "resolution_timestamp":  resolution_time,
        "resolution_time_hours": resolution_hours,
        "sla_hours_limit":       dept["sla_hours"],
        "sla_breach_flag":       int(resolution_hours > dept["sla_hours"]),
        "complaint_status":      random.choice(["open","resolved","escalated"]),
        "fraud_related":         int(txn["is_fraud_score"]),
        "complaint_text":        generate_complaint_text(txn, dept_code, sentiment),
    })
    complaint_counter += 1

complaints_df = pd.DataFrame(complaints)
for col in ("complaint_timestamp","resolution_timestamp"):
    complaints_df[col] = pd.to_datetime(complaints_df[col], errors="coerce")

# ==========================================================
# EXPORT
# ==========================================================

customers_df.to_csv("customers.csv",      index=False)
accounts_df.to_csv("accounts.csv",        index=False)
transactions_df.to_csv("transactions.csv", index=False)
complaints_df.to_csv("complaints.csv",    index=False)

# Print a sample of login credentials for the demo
sample = customers_df[["full_name","username","password"]].head(10)

print("\n" + "=" * 60)
print("  SENTINEL BANK — DATA GENERATOR v2.1 COMPLETE")
print("=" * 60)
print(f"  Customers    : {len(customers_df):,}")
print(f"  Accounts     : {len(accounts_df):,}")
print(f"  Transactions : {len(transactions_df):,}")
print(f"  Complaints   : {len(complaints_df):,}")

print("\n  Product distribution:")
for p in PRODUCT_CLASSES:
    c = sum(1 for v in customer_product_map.values() if v == p)
    print(f"    {p:<20}: {c:,} customers")

fraud_count = int(transactions_df["is_fraud_score"].sum())
print(f"\n  Fraud transactions : {fraud_count:,} ({fraud_count/len(transactions_df)*100:.1f}%)")

dept_counts = complaints_df["department_code"].value_counts()
print("\n  Complaint routing:")
for dept, count in dept_counts.items():
    print(f"    {dept} : {count:,}")

print("\n  Sample login credentials (first 10 customers):")
print(f"  {'Name':<25} {'Username':<30} {'Password'}")
print(f"  {'-'*25} {'-'*30} {'-'*20}")
for _, row in sample.iterrows():
    print(f"  {row['full_name']:<25} {row['username']:<30} {row['password']}")

print()
print("  NOTE: Passwords are plain text for demo only.")
print("        Hash with bcrypt before any production use.")
print("=" * 60 + "\n")

