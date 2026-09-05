"""
Sentinel — Coordinated Payment Abuse Intelligence
Synthetic Transaction Dataset Generator V3 (Adversarial Benign Networks & Partial Overlap)

Purpose:
Generates dataset transactions_v3.csv containing realistic legitimate connected networks
(Family, Hostel, Office, Public Wi-Fi, B2B Business networks) and partial infrastructure
overlap to stress-test false positive protection.

Core Requirement:
GRAPH CONNECTION != FRAUD.

Specific Benign Networks Included:
1. FAMILY_NETWORK: Includes Son (U_FAMILY_SON_01) buying ₹500 at Stationery merchant (M_STATIONERY_01),
   Stationery merchant transacting with Father (U_FAMILY_FATHER_01), Father operating Jeweller merchant (M_JEWELLERY_01).
   Path: Son -> Stationery Merchant -> Father -> Jeweller Merchant. (Graph connected, LEGITIMATE!).
2. HOSTEL_NETWORK: 50 students sharing hostel Wi-Fi IPs & study hall PCs.
3. OFFICE_NETWORK: 80 corporate employees sharing corporate proxy IP.
4. PUBLIC_WIFI_NETWORK: Public cafe Wi-Fi with high customer traffic & partial fraud overlap.
5. LEGITIMATE_BUSINESS_NETWORK: B2B suppliers, merchants, and repeat customers.
6. LEGITIMATE_REGULAR: Standard individual shoppers.

Fraud Scenarios Retained (10% Total):
- INDIVIDUAL_FRAUD (500)
- DEVICE_FARM (125)
- CARD_CYCLING (125)
- ACCOUNT_BURST (125)
- DISTRIBUTED_ABUSE (125)
"""

import csv
import datetime
import os
import random

# ==============================================================================
# CONFIGURATION & PARAMETERS
# ==============================================================================
RANDOM_SEED = 42
TOTAL_TRANSACTIONS = 10000

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "ml", "data", "raw")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "transactions_v3.csv")


def generate_v3_transactions():
    random.seed(RANDOM_SEED)
    start_time = datetime.datetime(2026, 9, 1, 8, 0, 0)

    rows = []
    txn_counter = 1

    # --------------------------------------------------------------------------
    # 1. SPECIAL BENIGN NETWORK: FAMILY_NETWORK (300 txns)
    # Includes explicit Son -> Stationery Merchant -> Father -> Jeweller Merchant path
    # --------------------------------------------------------------------------
    son_user = "U_FAMILY_SON_01"
    father_user = "U_FAMILY_FATHER_01"
    mother_user = "U_FAMILY_MOTHER_01"
    daughter_user = "U_FAMILY_DAUGHTER_01"
    
    stationery_merchant = "M_STATIONERY_01"
    jewellery_merchant = "M_JEWELLERY_01"

    family_home_ip = "IP_FAMILY_HOME_01"
    family_home_device = "D_FAMILY_TABLET_01"

    # Family transactions
    for _ in range(300):
        t_delta = datetime.timedelta(seconds=random.randint(0, 86400 * 5))
        current_ts = (start_time + t_delta).strftime("%Y-%m-%dT%H:%M:%SZ")

        roll = random.random()
        if roll < 0.30:
            # Son buying stationery for ₹500 ($6.00 equivalent)
            u_id = son_user
            m_id = stationery_merchant
            amt = 500.00
            dev_id = family_home_device
            ip_id = family_home_ip
            card_id = "C_FAMILY_SON_01"
            acc_age = 180
        elif roll < 0.55:
            # Stationery merchant conducting business with Father
            u_id = "U_STATIONERY_OWNER_01"
            m_id = jewellery_merchant
            amt = 15000.00
            dev_id = "D_STATIONERY_POS_01"
            ip_id = "IP_STATIONERY_BIZ_01"
            card_id = "C_STATIONERY_BIZ_01"
            acc_age = 450
        elif roll < 0.80:
            # Father making business payment at Jeweller
            u_id = father_user
            m_id = jewellery_merchant
            amt = 50000.00
            dev_id = "D_FATHER_PHONE_01"
            ip_id = family_home_ip
            card_id = "C_FATHER_BIZ_01"
            acc_age = 800
        else:
            # Mother/Daughter normal purchases
            u_id = random.choice([mother_user, daughter_user])
            m_id = f"M_{random.randint(1, 100):03d}"
            amt = round(random.uniform(20.0, 150.0), 2)
            dev_id = family_home_device
            ip_id = family_home_ip
            card_id = "C_FAMILY_HOME_01"
            acc_age = 350

        rows.append({
            "transaction_id": f"TXN_V3_{txn_counter:06d}",
            "timestamp": current_ts,
            "user_id": u_id,
            "amount": amt,
            "account_age_days": acc_age,
            "device_id": dev_id,
            "ip_id": ip_id,
            "card_id": card_id,
            "merchant_id": m_id,
            "transactions_last_hour": random.choice([0, 1, 2]),
            "transactions_last_day": random.randint(1, 4),
            "failed_transactions": 0,
            "unique_devices": 1,
            "unique_cards": 1,
            "is_fraud": 0,
            "fraud_scenario": "FAMILY_NETWORK"
        })
        txn_counter += 1

    # --------------------------------------------------------------------------
    # 2. BENIGN NETWORK: HOSTEL_NETWORK (600 txns)
    # 50 students sharing hostel Wi-Fi IPs & study hall PCs
    # --------------------------------------------------------------------------
    hostel_users = [f"U_HOSTEL_{i:03d}" for i in range(1, 51)]
    hostel_ips = ["IP_HOSTEL_WIFI_01", "IP_HOSTEL_WIFI_02", "IP_HOSTEL_WIFI_03"]
    hostel_devices = ["D_HOSTEL_STUDY_01", "D_HOSTEL_STUDY_02"]

    for _ in range(600):
        t_delta = datetime.timedelta(seconds=random.randint(0, 86400 * 5))
        current_ts = (start_time + t_delta).strftime("%Y-%m-%dT%H:%M:%SZ")

        u_id = random.choice(hostel_users)
        ip_id = random.choice(hostel_ips)
        dev_id = random.choice(hostel_devices) if random.random() < 0.20 else f"D_STUDENT_{random.randint(1, 50):03d}"
        card_id = f"C_STUDENT_{random.randint(1, 50):03d}"
        m_id = f"M_{random.randint(1, 120):03d}"

        rows.append({
            "transaction_id": f"TXN_V3_{txn_counter:06d}",
            "timestamp": current_ts,
            "user_id": u_id,
            "amount": round(random.uniform(5.0, 120.0), 2),
            "account_age_days": random.randint(10, 300),
            "device_id": dev_id,
            "ip_id": ip_id,
            "card_id": card_id,
            "merchant_id": m_id,
            "transactions_last_hour": random.choices([0, 1, 2, 3], weights=[0.70, 0.20, 0.07, 0.03])[0],
            "transactions_last_day": random.randint(1, 5),
            "failed_transactions": random.choice([0, 0, 0, 1]),
            "unique_devices": random.choice([1, 1, 2]),
            "unique_cards": 1,
            "is_fraud": 0,
            "fraud_scenario": "HOSTEL_NETWORK"
        })
        txn_counter += 1

    # --------------------------------------------------------------------------
    # 3. BENIGN NETWORK: OFFICE_NETWORK (800 txns)
    # 80 corporate employees sharing corporate proxy IP
    # --------------------------------------------------------------------------
    office_users = [f"U_OFFICE_{i:03d}" for i in range(1, 81)]
    office_ip = "IP_OFFICE_CORP_01"

    for _ in range(800):
        t_delta = datetime.timedelta(seconds=random.randint(0, 86400 * 5))
        current_ts = (start_time + t_delta).strftime("%Y-%m-%dT%H:%M:%SZ")

        u_id = random.choice(office_users)
        dev_id = f"D_EMP_{random.randint(1, 80):03d}"
        card_id = f"C_EMP_{random.randint(1, 80):03d}"
        m_id = f"M_{random.randint(1, 150):03d}"

        rows.append({
            "transaction_id": f"TXN_V3_{txn_counter:06d}",
            "timestamp": current_ts,
            "user_id": u_id,
            "amount": round(random.uniform(15.0, 350.0), 2),
            "account_age_days": random.randint(60, 900),
            "device_id": dev_id,
            "ip_id": office_ip,
            "card_id": card_id,
            "merchant_id": m_id,
            "transactions_last_hour": random.choice([0, 1, 2]),
            "transactions_last_day": random.randint(1, 6),
            "failed_transactions": random.choice([0, 0, 1]),
            "unique_devices": 1,
            "unique_cards": 1,
            "is_fraud": 0,
            "fraud_scenario": "OFFICE_NETWORK"
        })
        txn_counter += 1

    # --------------------------------------------------------------------------
    # 4. BENIGN NETWORK: PUBLIC_WIFI_NETWORK (500 txns)
    # Public cafe Wi-Fi with high customer traffic & partial fraud overlap
    # --------------------------------------------------------------------------
    public_users = [f"U_CAFE_{i:03d}" for i in range(1, 61)]
    public_ip = "IP_PUBLIC_CAFE_01"

    for _ in range(500):
        t_delta = datetime.timedelta(seconds=random.randint(0, 86400 * 5))
        current_ts = (start_time + t_delta).strftime("%Y-%m-%dT%H:%M:%SZ")

        u_id = random.choice(public_users)
        dev_id = f"D_CAFE_CUST_{random.randint(1, 60):03d}"
        card_id = f"C_CAFE_CUST_{random.randint(1, 60):03d}"
        m_id = f"M_{random.randint(1, 150):03d}"

        rows.append({
            "transaction_id": f"TXN_V3_{txn_counter:06d}",
            "timestamp": current_ts,
            "user_id": u_id,
            "amount": round(random.uniform(8.0, 180.0), 2),
            "account_age_days": random.randint(20, 500),
            "device_id": dev_id,
            "ip_id": public_ip,
            "card_id": card_id,
            "merchant_id": m_id,
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
    # 5. BENIGN NETWORK: LEGITIMATE_BUSINESS_NETWORK (800 txns)
    # B2B suppliers, merchants, and repeat customers
    # --------------------------------------------------------------------------
    biz_users = [f"U_BIZ_CLIENT_{i:03d}" for i in range(1, 41)]
    supplier_merchants = [f"M_SUPPLIER_{i:02d}" for i in range(1, 6)]

    for _ in range(800):
        t_delta = datetime.timedelta(seconds=random.randint(0, 86400 * 5))
        current_ts = (start_time + t_delta).strftime("%Y-%m-%dT%H:%M:%SZ")

        u_id = random.choice(biz_users)
        m_id = random.choice(supplier_merchants)
        dev_id = f"D_BIZ_{random.randint(1, 40):03d}"
        ip_id = f"IP_BIZ_{random.randint(1, 40):03d}"
        card_id = f"C_BIZ_{random.randint(1, 40):03d}"

        rows.append({
            "transaction_id": f"TXN_V3_{txn_counter:06d}",
            "timestamp": current_ts,
            "user_id": u_id,
            "amount": round(random.uniform(500.0, 5000.0), 2),
            "account_age_days": random.randint(100, 1200),
            "device_id": dev_id,
            "ip_id": ip_id,
            "card_id": card_id,
            "merchant_id": m_id,
            "transactions_last_hour": random.choice([0, 1, 2]),
            "transactions_last_day": random.randint(2, 8),
            "failed_transactions": 0,
            "unique_devices": 1,
            "unique_cards": 1,
            "is_fraud": 0,
            "fraud_scenario": "LEGITIMATE_BUSINESS_NETWORK"
        })
        txn_counter += 1

    # --------------------------------------------------------------------------
    # 6. LEGITIMATE REGULAR SHOPPERS (6,000 txns)
    # Standard everyday shoppers
    # --------------------------------------------------------------------------
    reg_users = [f"U_REG_{i:04d}" for i in range(1, 2001)]
    reg_devices = [f"D_REG_{i:04d}" for i in range(1, 1500)]
    reg_ips = [f"IP_REG_{i:04d}" for i in range(1, 1500)]
    reg_cards = [f"C_REG_{i:04d}" for i in range(1, 2000)]
    reg_merchants = [f"M_{i:03d}" for i in range(1, 150)]

    for _ in range(6000):
        t_delta = datetime.timedelta(seconds=random.randint(0, 86400 * 5))
        current_ts = (start_time + t_delta).strftime("%Y-%m-%dT%H:%M:%SZ")

        u_id = random.choice(reg_users)
        dev_id = random.choice(reg_devices)
        ip_id = random.choice(reg_ips)
        card_id = random.choice(reg_cards)
        m_id = random.choice(reg_merchants)

        # Partial Overlap: 5% of regular legitimate users buy from target merchant M_TARGET_HIGHVAL_99
        if random.random() < 0.05:
            m_id = "M_TARGET_HIGHVAL_99"

        # 5% of regular legitimate users use cafe public Wi-Fi IP_PUBLIC_CAFE_01
        if random.random() < 0.05:
            ip_id = "IP_PUBLIC_CAFE_01"

        rows.append({
            "transaction_id": f"TXN_V3_{txn_counter:06d}",
            "timestamp": current_ts,
            "user_id": u_id,
            "amount": round(random.uniform(10.0, 250.0), 2),
            "account_age_days": random.randint(30, 900),
            "device_id": dev_id,
            "ip_id": ip_id,
            "card_id": card_id,
            "merchant_id": m_id,
            "transactions_last_hour": random.choices([0, 1, 2], weights=[0.85, 0.12, 0.03])[0],
            "transactions_last_day": random.randint(1, 5),
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
    
    # A. INDIVIDUAL FRAUD (500)
    indiv_users = [f"U_INDIV_V3_{i:03d}" for i in range(1, 151)]
    for _ in range(500):
        t_delta = datetime.timedelta(seconds=random.randint(0, 86400 * 5))
        current_ts = (start_time + t_delta).strftime("%Y-%m-%dT%H:%M:%SZ")

        u_id = random.choice(indiv_users)
        dev_id = f"D_INDIV_V3_{random.randint(1, 200):03d}"
        
        # Partial Overlap: 10% of individual fraud uses public cafe Wi-Fi IP_PUBLIC_CAFE_01
        ip_id = "IP_PUBLIC_CAFE_01" if random.random() < 0.10 else f"IP_INDIV_V3_{random.randint(1, 200):03d}"
        card_id = f"C_INDIV_V3_{random.randint(1, 200):03d}"
        m_id = f"M_{random.randint(1, 150):03d}"

        rows.append({
            "transaction_id": f"TXN_V3_{txn_counter:06d}",
            "timestamp": current_ts,
            "user_id": u_id,
            "amount": round(random.uniform(350.0, 2200.0), 2),
            "account_age_days": random.randint(1, 15),
            "device_id": dev_id,
            "ip_id": ip_id,
            "card_id": card_id,
            "merchant_id": m_id,
            "transactions_last_hour": random.randint(4, 12),
            "transactions_last_day": random.randint(10, 30),
            "failed_transactions": random.randint(2, 6),
            "unique_devices": random.randint(2, 5),
            "unique_cards": random.randint(2, 5),
            "is_fraud": 1,
            "fraud_scenario": "INDIVIDUAL_FRAUD"
        })
        txn_counter += 1

    # B. DEVICE_FARM (125)
    farm_users = [f"U_FARM_{i:03d}" for i in range(1, 31)]
    farm_devices = ["D_FARM_HUB_01", "D_FARM_HUB_02"]
    farm_ips = ["IP_FARM_PROXY_01"]

    for _ in range(125):
        t_delta = datetime.timedelta(seconds=random.randint(0, 86400 * 5))
        current_ts = (start_time + t_delta).strftime("%Y-%m-%dT%H:%M:%SZ")

        rows.append({
            "transaction_id": f"TXN_V3_{txn_counter:06d}",
            "timestamp": current_ts,
            "user_id": random.choice(farm_users),
            "amount": round(random.uniform(40.0, 300.0), 2),
            "account_age_days": random.randint(2, 20),
            "device_id": random.choice(farm_devices),
            "ip_id": random.choice(farm_ips),
            "card_id": f"C_FARM_{random.randint(1, 40):03d}",
            "merchant_id": f"M_{random.randint(1, 150):03d}",
            "transactions_last_hour": random.randint(4, 10),
            "transactions_last_day": random.randint(12, 35),
            "failed_transactions": random.choice([1, 2, 3]),
            "unique_devices": 1,
            "unique_cards": random.randint(1, 3),
            "is_fraud": 1,
            "fraud_scenario": "DEVICE_FARM"
        })
        txn_counter += 1

    # C. CARD_CYCLING (125)
    cycle_users = [f"U_CYCLE_{i:03d}" for i in range(1, 26)]
    stolen_cards = [f"C_STOLEN_POOL_{i:02d}" for i in range(1, 6)]

    for _ in range(125):
        t_delta = datetime.timedelta(seconds=random.randint(0, 86400 * 5))
        current_ts = (start_time + t_delta).strftime("%Y-%m-%dT%H:%M:%SZ")

        rows.append({
            "transaction_id": f"TXN_V3_{txn_counter:06d}",
            "timestamp": current_ts,
            "user_id": random.choice(cycle_users),
            "amount": round(random.uniform(60.0, 400.0), 2),
            "account_age_days": random.randint(10, 90),
            "device_id": f"D_CYCLE_{random.randint(1, 25):03d}",
            "ip_id": f"IP_CYCLE_{random.randint(1, 25):03d}",
            "card_id": random.choice(stolen_cards),
            "merchant_id": f"M_{random.randint(1, 150):03d}",
            "transactions_last_hour": random.randint(3, 8),
            "transactions_last_day": random.randint(8, 22),
            "failed_transactions": random.randint(2, 5),
            "unique_devices": random.randint(1, 3),
            "unique_cards": random.randint(3, 7),
            "is_fraud": 1,
            "fraud_scenario": "CARD_CYCLING"
        })
        txn_counter += 1

    # D. ACCOUNT_BURST (125)
    burst_users = [f"U_BURST_{i:03d}" for i in range(1, 21)]
    burst_ips = ["IP_BURST_SUBNET_01", "IP_BURST_SUBNET_02"]

    for _ in range(125):
        t_delta = datetime.timedelta(seconds=random.randint(0, 86400 * 5))
        current_ts = (start_time + t_delta).strftime("%Y-%m-%dT%H:%M:%SZ")

        rows.append({
            "transaction_id": f"TXN_V3_{txn_counter:06d}",
            "timestamp": current_ts,
            "user_id": random.choice(burst_users),
            "amount": round(random.uniform(150.0, 650.0), 2),
            "account_age_days": random.choice([0, 1, 2]),
            "device_id": f"D_BURST_{random.randint(1, 20):03d}",
            "ip_id": random.choice(burst_ips),
            "card_id": f"C_BURST_{random.randint(1, 30):03d}",
            "merchant_id": f"M_{random.randint(1, 150):03d}",
            "transactions_last_hour": random.randint(6, 15),
            "transactions_last_day": random.randint(10, 25),
            "failed_transactions": random.choice([0, 1, 2]),
            "unique_devices": 1,
            "unique_cards": 1,
            "is_fraud": 1,
            "fraud_scenario": "ACCOUNT_BURST"
        })
        txn_counter += 1

    # E. DISTRIBUTED_ABUSE (125)
    dist_users = [f"U_DIST_{i:03d}" for i in range(1, 31)]
    dist_ips = [f"IP_DIST_PROXY_{i:02d}" for i in range(1, 5)]

    for _ in range(125):
        t_delta = datetime.timedelta(seconds=random.randint(0, 86400 * 5))
        current_ts = (start_time + t_delta).strftime("%Y-%m-%dT%H:%M:%SZ")

        rows.append({
            "transaction_id": f"TXN_V3_{txn_counter:06d}",
            "timestamp": current_ts,
            "user_id": random.choice(dist_users),
            "amount": round(random.uniform(20.0, 110.0), 2),
            "account_age_days": random.randint(15, 90),
            "device_id": f"D_DIST_{random.randint(1, 30):03d}",
            "ip_id": random.choice(dist_ips),
            "card_id": f"C_DIST_{random.randint(1, 35):03d}",
            "merchant_id": "M_TARGET_HIGHVAL_99",
            "transactions_last_hour": random.randint(2, 4),
            "transactions_last_day": random.randint(4, 12),
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
    print(f"Generating Dataset V3 (Adversarial Benign Networks) with seed {RANDOM_SEED}...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    rows = generate_v3_transactions()

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

    print(f"Dataset V3 successfully generated and saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
