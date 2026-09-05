"""
Sentinel — Coordinated Payment Abuse Intelligence
Synthetic Transaction Dataset Generator V2 (Harder / Realistic Overlap)

Purpose:
Generates a realistic, second-iteration synthetic payment dataset (transactions_v2.csv)
containing intentional overlap between legitimate and fraudulent behavior.

Key Changes in V2:
------------------
1. Legitimate Noise: Legitimate transactions include new accounts, high sales-driven velocity,
   occasional card decline failures, multiple cards/devices, and shared household/office infrastructure.
2. Stealth Fraud: Fraudulent transactions include normal purchase amounts, aged/compromised accounts,
   low transaction velocity, and few card declines.
3. Coordinated Rings in V2:
   - DEVICE_FARM: Uses aged accounts and moderate velocity.
   - CARD_CYCLING: Uses normal transaction amounts and low decline rates.
   - ACCOUNT_BURST: Staggered creation over 0-3 days with moderate velocity.
   - DISTRIBUTED_ABUSE: Low amounts ($25-$120), normal account ages (15-120 days), and 
     normal velocity (1-3 txns/hr) targeting merchant M_TARGET_HIGHVAL_99.

Result:
Single-transaction ML features alone will have significant difficulty distinguishing fraud from legit,
demonstrating the necessity of graph network analysis for discovering coordinated rings.
"""

import csv
import os
import random

# ==============================================================================
# CONFIGURATION & PARAMETERS
# ==============================================================================
RANDOM_SEED = 42
TOTAL_TRANSACTIONS = 10000

RATIO_LEGITIMATE = 0.90         # 9,000 transactions (90%)
RATIO_INDIVIDUAL_FRAUD = 0.05   #   500 transactions (5%)
RATIO_COORDINATED_FRAUD = 0.05  #   500 transactions (5%)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "ml", "data", "raw")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "transactions_v2.csv")


def generate_v2_transactions():
    random.seed(RANDOM_SEED)

    count_legit = int(TOTAL_TRANSACTIONS * RATIO_LEGITIMATE)
    count_indiv_fraud = int(TOTAL_TRANSACTIONS * RATIO_INDIVIDUAL_FRAUD)
    count_coord_fraud = TOTAL_TRANSACTIONS - count_legit - count_indiv_fraud

    scenarios = ["DEVICE_FARM", "CARD_CYCLING", "ACCOUNT_BURST", "DISTRIBUTED_ABUSE"]
    count_per_scenario = count_coord_fraud // len(scenarios)
    remainder = count_coord_fraud % len(scenarios)

    scenario_counts = {sc: count_per_scenario for sc in scenarios}
    scenario_counts[scenarios[0]] += remainder

    # Entity Pools
    legit_users = [f"U_LEGIT_{i:04d}" for i in range(1, 2501)]
    legit_devices = [f"D_LEGIT_{i:04d}" for i in range(1, 2000)]
    legit_ips = [f"IP_LEGIT_{i:04d}" for i in range(1, 2000)]
    legit_cards = [f"C_LEGIT_{i:04d}" for i in range(1, 3000)]
    merchants = [f"M_{i:03d}" for i in range(1, 151)]

    # Benign Shared Infrastructure
    shared_benign_devices = [f"D_SHARED_BENIGN_{i:02d}" for i in range(1, 15)]
    shared_benign_ips = [f"IP_SHARED_BENIGN_{i:02d}" for i in range(1, 15)]

    # Individual Fraud pools
    indiv_fraud_users = [f"U_INDIV_{i:04d}" for i in range(1, 201)]

    # Coordinated Ring Pools
    ring_farm_users = [f"U_FARM_{i:03d}" for i in range(1, 31)]
    ring_farm_devices = ["D_FARM_HUB_01", "D_FARM_HUB_02", "D_FARM_HUB_03"]
    ring_farm_ips = ["IP_FARM_PROXY_01", "IP_FARM_PROXY_02"]

    ring_cycle_users = [f"U_CYCLE_{i:03d}" for i in range(1, 26)]
    ring_cycle_stolen_cards = [f"C_STOLEN_POOL_{i:02d}" for i in range(1, 7)]

    ring_burst_users = [f"U_BURST_{i:03d}" for i in range(1, 21)]
    ring_burst_ips = ["IP_BURST_SUBNET_01", "IP_BURST_SUBNET_02"]

    ring_dist_users = [f"U_DIST_{i:03d}" for i in range(1, 31)]
    ring_dist_ips = [f"IP_DIST_PROXY_{i:02d}" for i in range(1, 6)]
    target_merchant = "M_TARGET_HIGHVAL_99"

    rows = []
    txn_counter = 1

    # --------------------------------------------------------------------------
    # STEP 1: Generate Legitimate Transactions with Noise (9,000)
    # --------------------------------------------------------------------------
    for _ in range(count_legit):
        user_id = random.choice(legit_users)
        
        # 15% chance of using shared benign infrastructure
        device_id = random.choice(shared_benign_devices) if random.random() < 0.15 else random.choice(legit_devices)
        ip_id = random.choice(shared_benign_ips) if random.random() < 0.15 else random.choice(legit_ips)
        card_id = random.choice(legit_cards)
        merchant_id = random.choice(merchants)

        # REALISTIC OVERLAP IN LEGITIMATE:
        # 25% of legitimate accounts are relatively new (1-29 days old)
        if random.random() < 0.25:
            account_age = random.randint(1, 29)
        else:
            account_age = random.randint(30, 1000)

        # 15% high-value legitimate purchases ($300-$2000)
        if random.random() < 0.15:
            amount = round(random.uniform(300.0, 2000.0), 2)
        else:
            amount = round(random.uniform(10.0, 250.0), 2)

        # 10% velocity spikes (3-6 txns/hr during sales/deals)
        if random.random() < 0.10:
            tx_hour = random.randint(3, 6)
            tx_day = random.randint(5, 12)
        else:
            tx_hour = random.choices([0, 1, 2], weights=[0.80, 0.15, 0.05])[0]
            tx_day = random.randint(1, 4)

        # 10% occasional card decline / OTP failure (1-3 failures)
        failed_tx = random.randint(1, 3) if random.random() < 0.10 else 0

        rows.append({
            "transaction_id": f"TXN_V2_{txn_counter:06d}",
            "user_id": user_id,
            "amount": amount,
            "account_age_days": account_age,
            "device_id": device_id,
            "ip_id": ip_id,
            "card_id": card_id,
            "merchant_id": merchant_id,
            "transactions_last_hour": tx_hour,
            "transactions_last_day": tx_day,
            "failed_transactions": failed_tx,
            "unique_devices": random.choice([1, 1, 2, 3]),
            "unique_cards": random.choice([1, 1, 2, 3]),
            "is_fraud": 0,
            "fraud_scenario": "NONE"
        })
        txn_counter += 1

    # --------------------------------------------------------------------------
    # STEP 2: Generate Individual Fraud with Stealth Overlap (500)
    # --------------------------------------------------------------------------
    for _ in range(count_indiv_fraud):
        user_id = random.choice(indiv_fraud_users)
        device_id = f"D_INDIV_{random.randint(1, 300):04d}"
        ip_id = f"IP_INDIV_{random.randint(1, 300):04d}"
        card_id = f"C_INDIV_{random.randint(1, 300):04d}"
        merchant_id = random.choice(merchants)

        # 40% of individual fraud use aged/compromised accounts (15-180 days)
        account_age = random.randint(15, 180) if random.random() < 0.40 else random.randint(0, 7)

        # 40% of individual fraud use completely normal amounts ($20-$250)
        amount = round(random.uniform(20.0, 250.0), 2) if random.random() < 0.40 else round(random.uniform(400.0, 2200.0), 2)

        # 40% use stealth/low hourly velocity (1-3 txns/hr)
        tx_hour = random.randint(1, 3) if random.random() < 0.40 else random.randint(4, 12)
        tx_day = random.randint(4, 25)

        # 40% low failed attempts (0-1 failures)
        failed_tx = random.choice([0, 1]) if random.random() < 0.40 else random.randint(2, 6)

        rows.append({
            "transaction_id": f"TXN_V2_{txn_counter:06d}",
            "user_id": user_id,
            "amount": amount,
            "account_age_days": account_age,
            "device_id": device_id,
            "ip_id": ip_id,
            "card_id": card_id,
            "merchant_id": merchant_id,
            "transactions_last_hour": tx_hour,
            "transactions_last_day": tx_day,
            "failed_transactions": failed_tx,
            "unique_devices": random.randint(2, 5),
            "unique_cards": random.randint(2, 5),
            "is_fraud": 1,
            "fraud_scenario": "INDIVIDUAL_FRAUD"
        })
        txn_counter += 1

    # --------------------------------------------------------------------------
    # STEP 3: Coordinated Fraud Rings with Stealth Overlap (500 total)
    # --------------------------------------------------------------------------

    # Scenario 1: DEVICE_FARM (125)
    # Stealth: Moderate velocity (2-5 txns/hr), normal amounts ($30-$250), mix of account ages
    for _ in range(scenario_counts["DEVICE_FARM"]):
        user_id = random.choice(ring_farm_users)
        device_id = random.choice(ring_farm_devices)
        ip_id = random.choice(ring_farm_ips)
        card_id = f"C_FARM_{random.randint(1, 40):03d}"
        merchant_id = random.choice(merchants)

        rows.append({
            "transaction_id": f"TXN_V2_{txn_counter:06d}",
            "user_id": user_id,
            "amount": round(random.uniform(30.0, 250.0), 2),     # Normal amount
            "account_age_days": random.randint(5, 60),           # Mix of ages
            "device_id": device_id,                              # Shared farm device
            "ip_id": ip_id,                                      # Shared farm proxy
            "card_id": card_id,
            "merchant_id": merchant_id,
            "transactions_last_hour": random.randint(2, 5),      # Moderate velocity
            "transactions_last_day": random.randint(8, 22),
            "failed_transactions": random.choice([0, 1, 2]),     # Low failures
            "unique_devices": 1,
            "unique_cards": random.choice([1, 2]),
            "is_fraud": 1,
            "fraud_scenario": "DEVICE_FARM"
        })
        txn_counter += 1

    # Scenario 2: CARD_CYCLING (125)
    # Stealth: Normal transaction amounts ($40-$350), low decline rate (0-2 failures)
    for _ in range(scenario_counts["CARD_CYCLING"]):
        user_id = random.choice(ring_cycle_users)
        card_id = random.choice(ring_cycle_stolen_cards)      # Shared stolen card pool
        device_id = f"D_CYCLE_{random.randint(1, 25):03d}"
        ip_id = f"IP_CYCLE_{random.randint(1, 25):03d}"
        merchant_id = random.choice(merchants)

        rows.append({
            "transaction_id": f"TXN_V2_{txn_counter:06d}",
            "user_id": user_id,
            "amount": round(random.uniform(40.0, 350.0), 2),     # Normal amount
            "account_age_days": random.randint(15, 120),
            "device_id": device_id,
            "ip_id": ip_id,
            "card_id": card_id,
            "merchant_id": merchant_id,
            "transactions_last_hour": random.randint(2, 5),      # Moderate velocity
            "transactions_last_day": random.randint(6, 18),
            "failed_transactions": random.choice([0, 1, 2]),     # Low declines
            "unique_devices": random.randint(1, 3),
            "unique_cards": random.randint(2, 5),
            "is_fraud": 1,
            "fraud_scenario": "CARD_CYCLING"
        })
        txn_counter += 1

    # Scenario 3: ACCOUNT_BURST (125)
    # Stealth: Staggered account creation (0-5 days), moderate velocity (3-7 txns/hr)
    for _ in range(scenario_counts["ACCOUNT_BURST"]):
        user_id = random.choice(ring_burst_users)
        device_id = f"D_BURST_{random.randint(1, 20):03d}"
        ip_id = random.choice(ring_burst_ips)
        card_id = f"C_BURST_{random.randint(1, 30):03d}"
        merchant_id = random.choice(merchants)

        rows.append({
            "transaction_id": f"TXN_V2_{txn_counter:06d}",
            "user_id": user_id,
            "amount": round(random.uniform(80.0, 450.0), 2),      # Normal amount
            "account_age_days": random.randint(0, 5),             # Account age 0-5 days
            "device_id": device_id,
            "ip_id": ip_id,
            "card_id": card_id,
            "merchant_id": merchant_id,
            "transactions_last_hour": random.randint(3, 7),       # Moderate velocity
            "transactions_last_day": random.randint(8, 20),
            "failed_transactions": random.choice([0, 1]),
            "unique_devices": random.randint(1, 2),
            "unique_cards": random.randint(1, 2),
            "is_fraud": 1,
            "fraud_scenario": "ACCOUNT_BURST"
        })
        txn_counter += 1

    # Scenario 4: DISTRIBUTED_ABUSE (125)
    # Stealth: Completely normal amounts ($25-$120), normal account ages (15-120 days),
    # normal velocity (1-3 txns/hr), 0-1 failures, targeting merchant M_TARGET_HIGHVAL_99
    for _ in range(scenario_counts["DISTRIBUTED_ABUSE"]):
        user_id = random.choice(ring_dist_users)
        device_id = f"D_DIST_{random.randint(1, 30):03d}"
        ip_id = random.choice(ring_dist_ips)                    # Shared proxy subnet
        card_id = f"C_DIST_{random.randint(1, 35):03d}"
        merchant_id = target_merchant                           # Targeted merchant

        rows.append({
            "transaction_id": f"TXN_V2_{txn_counter:06d}",
            "user_id": user_id,
            "amount": round(random.uniform(25.0, 120.0), 2),     # Completely normal amounts!
            "account_age_days": random.randint(15, 120),         # Aged accounts!
            "device_id": device_id,
            "ip_id": ip_id,
            "card_id": card_id,
            "merchant_id": merchant_id,
            "transactions_last_hour": random.randint(1, 3),      # Low/normal velocity!
            "transactions_last_day": random.randint(3, 8),
            "failed_transactions": random.choice([0, 1]),        # Clean txns!
            "unique_devices": 1,
            "unique_cards": 1,
            "is_fraud": 1,
            "fraud_scenario": "DISTRIBUTED_ABUSE"
        })
        txn_counter += 1

    random.shuffle(rows)
    return rows


def main():
    print(f"Generating realistic synthetic dataset V2 with seed {RANDOM_SEED}...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    rows = generate_v2_transactions()

    fieldnames = [
        "transaction_id", "user_id", "amount", "account_age_days",
        "device_id", "ip_id", "card_id", "merchant_id",
        "transactions_last_hour", "transactions_last_day", "failed_transactions",
        "unique_devices", "unique_cards", "is_fraud", "fraud_scenario"
    ]

    with open(OUTPUT_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"V2 Dataset successfully generated and saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
