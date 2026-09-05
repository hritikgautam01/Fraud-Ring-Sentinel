"""
Sentinel — Coordinated Payment Abuse Intelligence
Synthetic Transaction Dataset Generator V5 (Independent Blind Test)

Purpose:
Generates a completely fresh, independent test dataset (transactions_v5_independent.csv)
to perform a final blind generalization benchmark.

Key Characteristics of V5:
--------------------------
1. Seed: 55555 (Completely fresh random sequence).
2. Neutral Anonymized IDs: Numeric identifiers (e.g. U_847291, DEV_193847, IP_583920, CARD_729104, MERCH_384920).
   NO recognizable prefixes (like U_FRAUD, D_FARM_HUB, C_STOLEN_POOL).
3. Distribution Shift:
   - Legitimate amounts: $5 - $800, with 10% luxury purchases ($1,200 - $3,500).
   - Legitimate account age: 40% < 30 days old (onboarding wave).
   - Fraud amounts: $15 - $250 (stealth low amounts).
   - Fraud account age: 50% mature accounts (30 - 200 days old).
4. Mixed Infrastructure Networks:
   - Cafe Wi-Fi (IP_583903) shared by legitimate cafe customers AND a stealth fraud user.
   - Fraud rings spread across multiple merchants instead of single targets.
5. Explicit Family Network (Son -> Stationery -> Father -> Jeweller path).
"""

import csv
import datetime
import os
import random

RANDOM_SEED = 55555
TOTAL_TRANSACTIONS = 10000

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "ml", "data", "raw")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "transactions_v5_independent.csv")


def generate_v5_transactions():
    random.seed(RANDOM_SEED)
    start_time = datetime.datetime(2026, 9, 15, 8, 0, 0)

    rows = []
    txn_counter = 500001

    # Neutral ID Generators
    def gen_user(idx): return f"U_{840000 + idx}"
    def gen_dev(idx): return f"DEV_{190000 + idx}"
    def gen_ip(idx): return f"IP_{580000 + idx}"
    def gen_card(idx): return f"CARD_{720000 + idx}"
    def gen_merch(idx): return f"MERCH_{380000 + idx}"

    # --------------------------------------------------------------------------
    # 1. FAMILY_NETWORK (300 txns) - Son/Father/Stationery/Jeweller Path
    # --------------------------------------------------------------------------
    u_son, u_father = gen_user(1), gen_user(2)
    u_mother, u_stat_owner = gen_user(3), gen_user(4)
    
    m_stationery, m_jeweller = gen_merch(1), gen_merch(2)
    ip_fam_home = gen_ip(1)
    dev_fam_tablet = gen_dev(1)

    for _ in range(300):
        t_delta = datetime.timedelta(seconds=random.randint(0, 86400 * 5))
        current_ts = (start_time + t_delta).strftime("%Y-%m-%dT%H:%M:%SZ")
        roll = random.random()

        if roll < 0.35:
            # Son buying ₹500 ($6.00 equivalent) stationery
            u_id, m_id, amt, card_id = u_son, m_stationery, 500.00, gen_card(1)
        elif roll < 0.60:
            # Stationery owner transacting with Father
            u_id, m_id, amt, card_id = u_stat_owner, m_jeweller, 18000.00, gen_card(2)
        elif roll < 0.85:
            # Father buying from Jeweller
            u_id, m_id, amt, card_id = u_father, m_jeweller, 45000.00, gen_card(3)
        else:
            u_id, m_id, amt, card_id = u_mother, gen_merch(random.randint(10, 50)), 140.00, gen_card(4)

        rows.append({
            "transaction_id": f"TXN_V5_{txn_counter:06d}",
            "timestamp": current_ts,
            "user_id": u_id,
            "amount": amt,
            "account_age_days": 380,
            "device_id": dev_fam_tablet if u_id in [u_son, u_mother] else gen_dev(2),
            "ip_id": ip_fam_home if u_id in [u_son, u_father, u_mother] else gen_ip(2),
            "card_id": card_id,
            "merchant_id": m_id,
            "transactions_last_hour": random.choice([0, 1, 2]),
            "transactions_last_day": random.randint(1, 3),
            "failed_transactions": 0,
            "unique_devices": 1,
            "unique_cards": 1,
            "is_fraud": 0,
            "fraud_scenario": "FAMILY_NETWORK"
        })
        txn_counter += 1

    # --------------------------------------------------------------------------
    # 2. OFFICE_NETWORK (800 txns) - Corporate IP_580003 shared by 80 users
    # --------------------------------------------------------------------------
    office_users = [gen_user(10 + i) for i in range(80)]
    ip_office = gen_ip(3)

    for _ in range(800):
        t_delta = datetime.timedelta(seconds=random.randint(0, 86400 * 5))
        current_ts = (start_time + t_delta).strftime("%Y-%m-%dT%H:%M:%SZ")

        u_idx = random.randint(0, 79)
        rows.append({
            "transaction_id": f"TXN_V5_{txn_counter:06d}",
            "timestamp": current_ts,
            "user_id": office_users[u_idx],
            "amount": round(random.uniform(20.0, 450.0), 2),
            "account_age_days": random.randint(40, 800),
            "device_id": gen_dev(10 + u_idx),
            "ip_id": ip_office,
            "card_id": gen_card(10 + u_idx),
            "merchant_id": gen_merch(random.randint(10, 150)),
            "transactions_last_hour": random.choice([0, 1, 2, 3]),
            "transactions_last_day": random.randint(1, 5),
            "failed_transactions": random.choice([0, 0, 1]),
            "unique_devices": 1,
            "unique_cards": 1,
            "is_fraud": 0,
            "fraud_scenario": "OFFICE_NETWORK"
        })
        txn_counter += 1

    # --------------------------------------------------------------------------
    # 3. HOSTEL_NETWORK (600 txns) - 50 students on IP_580004
    # --------------------------------------------------------------------------
    hostel_users = [gen_user(100 + i) for i in range(50)]
    ip_hostel = gen_ip(4)

    for _ in range(600):
        t_delta = datetime.timedelta(seconds=random.randint(0, 86400 * 5))
        current_ts = (start_time + t_delta).strftime("%Y-%m-%dT%H:%M:%SZ")

        u_idx = random.randint(0, 49)
        rows.append({
            "transaction_id": f"TXN_V5_{txn_counter:06d}",
            "timestamp": current_ts,
            "user_id": hostel_users[u_idx],
            "amount": round(random.uniform(8.0, 110.0), 2),
            "account_age_days": random.randint(15, 250),
            "device_id": gen_dev(100 + u_idx),
            "ip_id": ip_hostel,
            "card_id": gen_card(100 + u_idx),
            "merchant_id": gen_merch(random.randint(10, 150)),
            "transactions_last_hour": random.choice([0, 1, 2]),
            "transactions_last_day": random.randint(1, 4),
            "failed_transactions": random.choice([0, 0, 1]),
            "unique_devices": 1,
            "unique_cards": 1,
            "is_fraud": 0,
            "fraud_scenario": "HOSTEL_NETWORK"
        })
        txn_counter += 1

    # --------------------------------------------------------------------------
    # 4. PUBLIC_CAFE_NETWORK (500 txns) - Mixed Graph Infrastructure!
    # IP_580005 shared by 60 cafe customers AND 1 stealth fraud user!
    # --------------------------------------------------------------------------
    cafe_users = [gen_user(200 + i) for i in range(60)]
    ip_cafe = gen_ip(5)

    for _ in range(500):
        t_delta = datetime.timedelta(seconds=random.randint(0, 86400 * 5))
        current_ts = (start_time + t_delta).strftime("%Y-%m-%dT%H:%M:%SZ")

        u_idx = random.randint(0, 59)
        rows.append({
            "transaction_id": f"TXN_V5_{txn_counter:06d}",
            "timestamp": current_ts,
            "user_id": cafe_users[u_idx],
            "amount": round(random.uniform(10.0, 160.0), 2),
            "account_age_days": random.randint(25, 450),
            "device_id": gen_dev(200 + u_idx),
            "ip_id": ip_cafe,
            "card_id": gen_card(200 + u_idx),
            "merchant_id": gen_merch(random.randint(10, 150)),
            "transactions_last_hour": random.choice([0, 1, 2]),
            "transactions_last_day": random.randint(1, 4),
            "failed_transactions": 0,
            "unique_devices": 1,
            "unique_cards": 1,
            "is_fraud": 0,
            "fraud_scenario": "PUBLIC_WIFI_NETWORK"
        })
        txn_counter += 1

    # --------------------------------------------------------------------------
    # 5. LEGITIMATE_BUSINESS_NETWORK (800 txns) - B2B Payments
    # --------------------------------------------------------------------------
    biz_users = [gen_user(300 + i) for i in range(40)]
    for _ in range(800):
        t_delta = datetime.timedelta(seconds=random.randint(0, 86400 * 5))
        current_ts = (start_time + t_delta).strftime("%Y-%m-%dT%H:%M:%SZ")

        u_idx = random.randint(0, 39)
        rows.append({
            "transaction_id": f"TXN_V5_{txn_counter:06d}",
            "timestamp": current_ts,
            "user_id": biz_users[u_idx],
            "amount": round(random.uniform(600.0, 4500.0), 2),
            "account_age_days": random.randint(90, 1100),
            "device_id": gen_dev(300 + u_idx),
            "ip_id": gen_ip(300 + u_idx),
            "card_id": gen_card(300 + u_idx),
            "merchant_id": gen_merch(random.randint(1, 10)),
            "transactions_last_hour": random.choice([0, 1, 2]),
            "transactions_last_day": random.randint(2, 7),
            "failed_transactions": 0,
            "unique_devices": 1,
            "unique_cards": 1,
            "is_fraud": 0,
            "fraud_scenario": "LEGITIMATE_BUSINESS_NETWORK"
        })
        txn_counter += 1

    # --------------------------------------------------------------------------
    # 6. LEGITIMATE REGULAR SHOPPERS (6,000 txns)
    # Distribution shift: 40% < 30 days old, 10% luxury purchases ($1,200 - $3,500)
    # --------------------------------------------------------------------------
    reg_users = [gen_user(1000 + i) for i in range(2000)]
    for _ in range(6000):
        t_delta = datetime.timedelta(seconds=random.randint(0, 86400 * 5))
        current_ts = (start_time + t_delta).strftime("%Y-%m-%dT%H:%M:%SZ")

        u_idx = random.randint(0, 1999)
        acc_age = random.randint(1, 29) if random.random() < 0.40 else random.randint(30, 900)
        amt = round(random.uniform(1200.0, 3500.0), 2) if random.random() < 0.10 else round(random.uniform(5.0, 800.0), 2)

        rows.append({
            "transaction_id": f"TXN_V5_{txn_counter:06d}",
            "timestamp": current_ts,
            "user_id": reg_users[u_idx],
            "amount": amt,
            "account_age_days": acc_age,
            "device_id": gen_dev(1000 + u_idx),
            "ip_id": gen_ip(1000 + u_idx),
            "card_id": gen_card(1000 + u_idx),
            "merchant_id": gen_merch(random.randint(1, 150)),
            "transactions_last_hour": random.choices([0, 1, 2, 3], weights=[0.75, 0.15, 0.07, 0.03])[0],
            "transactions_last_day": random.randint(1, 6),
            "failed_transactions": random.choice([0, 0, 1]),
            "unique_devices": 1,
            "unique_cards": 1,
            "is_fraud": 0,
            "fraud_scenario": "NONE"
        })
        txn_counter += 1

    # --------------------------------------------------------------------------
    # 7. FRAUD TRANSACTIONS (1,000 Total: 500 Indiv, 500 Coordinated Rings)
    # --------------------------------------------------------------------------

    # A. INDIVIDUAL FRAUD (500) - Stealth: amounts $15 - $250, 50% mature accounts (30-180 days)
    indiv_users = [gen_user(5000 + i) for i in range(150)]
    for _ in range(500):
        t_delta = datetime.timedelta(seconds=random.randint(0, 86400 * 5))
        current_ts = (start_time + t_delta).strftime("%Y-%m-%dT%H:%M:%SZ")

        u_idx = random.randint(0, 149)
        acc_age = random.randint(30, 180) if random.random() < 0.50 else random.randint(1, 15)
        amt = round(random.uniform(15.0, 250.0), 2) if random.random() < 0.50 else round(random.uniform(400.0, 1800.0), 2)

        # 1 stealth fraud user shares public cafe Wi-Fi IP_580005 (mixed graph!)
        ip_id = ip_cafe if random.random() < 0.10 else gen_ip(5000 + u_idx)

        rows.append({
            "transaction_id": f"TXN_V5_{txn_counter:06d}",
            "timestamp": current_ts,
            "user_id": indiv_users[u_idx],
            "amount": amt,
            "account_age_days": acc_age,
            "device_id": gen_dev(5000 + u_idx),
            "ip_id": ip_id,
            "card_id": gen_card(5000 + u_idx),
            "merchant_id": gen_merch(random.randint(1, 150)),
            "transactions_last_hour": random.randint(3, 9),
            "transactions_last_day": random.randint(8, 24),
            "failed_transactions": random.choice([0, 1, 2]),
            "unique_devices": random.randint(2, 4),
            "unique_cards": random.randint(2, 4),
            "is_fraud": 1,
            "fraud_scenario": "INDIVIDUAL_FRAUD"
        })
        txn_counter += 1

    # B. RING_MULTI_MERCHANT (125) - 18 users sharing 2 devices + 1 IP across 12 merchants
    ring1_users = [gen_user(6000 + i) for i in range(18)]
    ring1_devs = [gen_dev(6001), gen_dev(6002)]
    ring1_ip = gen_ip(6001)

    for _ in range(125):
        t_delta = datetime.timedelta(seconds=random.randint(0, 86400 * 5))
        current_ts = (start_time + t_delta).strftime("%Y-%m-%dT%H:%M:%SZ")

        rows.append({
            "transaction_id": f"TXN_V5_{txn_counter:06d}",
            "timestamp": current_ts,
            "user_id": random.choice(ring1_users),
            "amount": round(random.uniform(35.0, 280.0), 2),
            "account_age_days": random.randint(5, 45),
            "device_id": random.choice(ring1_devs),
            "ip_id": ring1_ip,
            "card_id": gen_card(random.randint(6000, 6030)),
            "merchant_id": gen_merch(random.randint(50, 62)),  # Multi-merchant spread!
            "transactions_last_hour": random.randint(3, 7),
            "transactions_last_day": random.randint(10, 25),
            "failed_transactions": random.choice([1, 2]),
            "unique_devices": 1,
            "unique_cards": random.randint(1, 3),
            "is_fraud": 1,
            "fraud_scenario": "DEVICE_FARM"
        })
        txn_counter += 1

    # C. RING_CARD_CYCLING_STEALTH (125) - 15 users cycling 4 stolen cards, 0-1 failures
    ring2_users = [gen_user(6100 + i) for i in range(15)]
    ring2_cards = [gen_card(6101), gen_card(6102), gen_card(6103), gen_card(6104)]

    for _ in range(125):
        t_delta = datetime.timedelta(seconds=random.randint(0, 86400 * 5))
        current_ts = (start_time + t_delta).strftime("%Y-%m-%dT%H:%M:%SZ")

        rows.append({
            "transaction_id": f"TXN_V5_{txn_counter:06d}",
            "timestamp": current_ts,
            "user_id": random.choice(ring2_users),
            "amount": round(random.uniform(50.0, 380.0), 2),
            "account_age_days": random.randint(20, 110),
            "device_id": gen_dev(random.randint(6100, 6115)),
            "ip_id": gen_ip(random.randint(6100, 6115)),
            "card_id": random.choice(ring2_cards),
            "merchant_id": gen_merch(random.randint(1, 150)),
            "transactions_last_hour": random.randint(2, 6),
            "transactions_last_day": random.randint(6, 18),
            "failed_transactions": random.choice([0, 1]),     # Stealth low failure rate!
            "unique_devices": random.randint(1, 3),
            "unique_cards": 4,
            "is_fraud": 1,
            "fraud_scenario": "CARD_CYCLING"
        })
        txn_counter += 1

    # D. RING_BURST_STAGGERED (125) - 22 users created over 0-3 days, moderate velocity
    ring3_users = [gen_user(6200 + i) for i in range(22)]
    ring3_ips = [gen_ip(6201), gen_ip(6202)]

    for _ in range(125):
        t_delta = datetime.timedelta(seconds=random.randint(0, 86400 * 5))
        current_ts = (start_time + t_delta).strftime("%Y-%m-%dT%H:%M:%SZ")

        rows.append({
            "transaction_id": f"TXN_V5_{txn_counter:06d}",
            "timestamp": current_ts,
            "user_id": random.choice(ring3_users),
            "amount": round(random.uniform(120.0, 520.0), 2),
            "account_age_days": random.choice([0, 1, 2, 3]),
            "device_id": gen_dev(random.randint(6200, 6222)),
            "ip_id": random.choice(ring3_ips),
            "card_id": gen_card(random.randint(6200, 6230)),
            "merchant_id": gen_merch(random.randint(1, 150)),
            "transactions_last_hour": random.randint(3, 7),     # Moderate velocity!
            "transactions_last_day": random.randint(8, 18),
            "failed_transactions": random.choice([0, 1]),
            "unique_devices": 1,
            "unique_cards": 1,
            "is_fraud": 1,
            "fraud_scenario": "ACCOUNT_BURST"
        })
        txn_counter += 1

    # E. RING_DISTRIBUTED_MULTI_TARGET (125) - 28 users sharing 3 proxy IPs targeting 2 merchants
    ring4_users = [gen_user(6300 + i) for i in range(28)]
    ring4_ips = [gen_ip(6301), gen_ip(6302), gen_ip(6303)]
    target_merchants_v5 = [gen_merch(88), gen_merch(89)]

    for _ in range(125):
        t_delta = datetime.timedelta(seconds=random.randint(0, 86400 * 5))
        current_ts = (start_time + t_delta).strftime("%Y-%m-%dT%H:%M:%SZ")

        rows.append({
            "transaction_id": f"TXN_V5_{txn_counter:06d}",
            "timestamp": current_ts,
            "user_id": random.choice(ring4_users),
            "amount": round(random.uniform(20.0, 90.0), 2),      # Low stealth amount!
            "account_age_days": random.randint(15, 100),
            "device_id": gen_dev(random.randint(6300, 6328)),
            "ip_id": random.choice(ring4_ips),
            "card_id": gen_card(random.randint(6300, 6335)),
            "merchant_id": random.choice(target_merchants_v5),   # Multi-target merchant!
            "transactions_last_hour": random.randint(1, 3),      # Low velocity!
            "transactions_last_day": random.randint(3, 9),
            "failed_transactions": random.choice([0, 1]),
            "unique_devices": 1,
            "unique_cards": 1,
            "is_fraud": 1,
            "fraud_scenario": "DISTRIBUTED_ABUSE"
        })
        txn_counter += 1

    random.shuffle(rows)
    return rows


def main():
    print(f"Generating Fresh Independent Dataset V5 with seed {RANDOM_SEED}...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    rows = generate_v5_transactions()

    fieldnames = [
        "transaction_id", "timestamp", "user_id", "amount", "account_age_days",
        "device_id", "ip_id", "card_id", "merchant_id",
        "transactions_last_hour", "transactions_last_day", "failed_transactions",
        "unique_devices", "unique_cards", "is_fraud", "fraud_scenario"
    ]

    with open(OUTPUT_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Dataset V5 successfully generated and saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
