"""
Sentinel — Coordinated Payment Abuse Intelligence
Synthetic Transaction Dataset Generator

This script generates a synthetic dataset of 10,000 payment transactions designed 
for training and evaluating AI risk management systems (Track 02: AI Risk Manager).

Dataset Structure:
------------------
The dataset contains three primary population groups:
1. Legitimate Transactions (~90%): Normal user purchasing behavior with realistic parameters.
   Includes benign shared infrastructure (e.g. shared family devices, office IPs) 
   so rule engines don't naively flag every shared IP/device as fraud.
2. Individual Fraud (~5%): Suspicious single-user behavior (high velocity, high amount, card testing).
3. Coordinated Fraud Rings (~5%): Multi-user network attacks across 4 specific scenarios:
   - DEVICE_FARM: Many user accounts operating from a single device farm.
   - CARD_CYCLING: Multiple user accounts cycling through a shared pool of stolen cards.
   - ACCOUNT_BURST: Cluster of brand-new accounts executing high-velocity transactions simultaneously.
   - DISTRIBUTED_ABUSE: Distributed network sharing IPs and targeting a single merchant with small amounts.

Reproducibility:
----------------
A fixed random seed (42) is used so running this script always produces the exact same dataset.
"""

import csv
import os
import random

# ==============================================================================
# CONFIGURATION & PARAMETERS (Easily configurable at the top)
# ==============================================================================

# Fixed seed ensures every run generates the exact same dataset
RANDOM_SEED = 42

# Total transactions to generate
TOTAL_TRANSACTIONS = 10000

# Target percentages for population groups (sum must equal 1.0)
RATIO_LEGITIMATE = 0.90         # 9,000 transactions (90%)
RATIO_INDIVIDUAL_FRAUD = 0.05   #   500 transactions (5%)
RATIO_COORDINATED_FRAUD = 0.05  #   500 transactions (5%)

# Output destination path (dynamically derived relative to script location)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "ml", "data", "raw")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "transactions.csv")


# ==============================================================================
# HELPER DATA GENERATOR
# ==============================================================================

def generate_transactions():
    """
    Main generator logic to build synthetic transactions.
    Returns a list of dictionaries, where each dictionary represents one CSV row.
    """
    random.seed(RANDOM_SEED)

    # --------------------------------------------------------------------------
    # STEP 1: Calculate exact row counts per category
    # --------------------------------------------------------------------------
    count_legit = int(TOTAL_TRANSACTIONS * RATIO_LEGITIMATE)
    count_indiv_fraud = int(TOTAL_TRANSACTIONS * RATIO_INDIVIDUAL_FRAUD)
    count_coord_fraud = TOTAL_TRANSACTIONS - count_legit - count_indiv_fraud

    # Divide coordinated fraud equally across the 4 scenarios (125 each)
    scenarios = ["DEVICE_FARM", "CARD_CYCLING", "ACCOUNT_BURST", "DISTRIBUTED_ABUSE"]
    count_per_scenario = count_coord_fraud // len(scenarios)
    remainder = count_coord_fraud % len(scenarios)

    scenario_counts = {sc: count_per_scenario for sc in scenarios}
    # Add any remainder to the first scenario to ensure exact total sum
    scenario_counts[scenarios[0]] += remainder

    # --------------------------------------------------------------------------
    # STEP 2: Pre-define Entity ID Pools
    # --------------------------------------------------------------------------
    # Creating dedicated ID pools allows us to introduce intentional overlaps 
    # (e.g. shared IPs/devices for both legitimate and fraud rings).

    # Legitimate pools
    legit_users = [f"U_LEGIT_{i:04d}" for i in range(1, 2501)]
    legit_devices = [f"D_LEGIT_{i:04d}" for i in range(1, 2000)]
    legit_ips = [f"IP_LEGIT_{i:04d}" for i in range(1, 2000)]
    legit_cards = [f"C_LEGIT_{i:04d}" for i in range(1, 3000)]
    merchants = [f"M_{i:03d}" for i in range(1, 151)]

    # Benign Shared Infrastructure (crucial so system learns shared != always fraud)
    # E.g., Family household sharing a tablet, or corporate office behind one IP
    shared_benign_devices = [f"D_SHARED_BENIGN_{i:02d}" for i in range(1, 11)]
    shared_benign_ips = [f"IP_SHARED_BENIGN_{i:02d}" for i in range(1, 11)]

    # Individual Fraud pools
    indiv_fraud_users = [f"U_INDIV_{i:04d}" for i in range(1, 201)]

    # Coordinated Ring Pools (Specific shared infrastructure for each ring)
    # Ring 1: Device Farm (Many users, 1 shared device farm)
    ring_farm_users = [f"U_FARM_{i:03d}" for i in range(1, 31)]
    ring_farm_devices = ["D_FARM_HUB_01", "D_FARM_HUB_02"]
    ring_farm_ips = ["IP_FARM_PROXY_01"]

    # Ring 2: Card Cycling (Many users cycling through a small stolen card pool)
    ring_cycle_users = [f"U_CYCLE_{i:03d}" for i in range(1, 26)]
    ring_cycle_stolen_cards = [f"C_STOLEN_POOL_{i:02d}" for i in range(1, 6)]

    # Ring 3: Account Burst (Cluster created on same day with rapid firing)
    ring_burst_users = [f"U_BURST_{i:03d}" for i in range(1, 21)]
    ring_burst_ips = ["IP_BURST_SUBNET_01", "IP_BURST_SUBNET_02"]

    # Ring 4: Distributed Abuse (Many users across proxy IPs targeting 1 merchant)
    ring_dist_users = [f"U_DIST_{i:03d}" for i in range(1, 31)]
    ring_dist_ips = [f"IP_DIST_PROXY_{i:02d}" for i in range(1, 5)]
    target_merchant = "M_TARGET_HIGHVAL_99"

    rows = []
    txn_counter = 1

    # --------------------------------------------------------------------------
    # STEP 3: Generate Legitimate Transactions (approx 90% = 9,000)
    # --------------------------------------------------------------------------
    # WHY: Legitimate users have low transaction velocity, low failure counts,
    # mature accounts, and stable device/card usage. Occasionally, they share
    # household devices or office Wi-Fi IPs.
    for _ in range(count_legit):
        user_id = random.choice(legit_users)
        
        # 10% chance of using a benign shared device (e.g. home shared computer)
        if random.random() < 0.10:
            device_id = random.choice(shared_benign_devices)
        else:
            device_id = random.choice(legit_devices)

        # 10% chance of using a benign shared IP (e.g. office / public cafe Wi-Fi)
        if random.random() < 0.10:
            ip_id = random.choice(shared_benign_ips)
        else:
            ip_id = random.choice(legit_ips)

        card_id = random.choice(legit_cards)
        merchant_id = random.choice(merchants)

        row = {
            "transaction_id": f"TXN_{txn_counter:06d}",
            "user_id": user_id,
            "amount": round(random.uniform(8.0, 250.0), 2),
            "account_age_days": random.randint(30, 1200),  # Established accounts
            "device_id": device_id,
            "ip_id": ip_id,
            "card_id": card_id,
            "merchant_id": merchant_id,
            "transactions_last_hour": random.choices([0, 1, 2], weights=[0.85, 0.12, 0.03])[0],
            "transactions_last_day": random.randint(1, 5),
            "failed_transactions": random.choices([0, 1], weights=[0.96, 0.04])[0], # Typos are rare
            "unique_devices": random.choice([1, 1, 1, 2]),
            "unique_cards": random.choice([1, 1, 1, 2]),
            "is_fraud": 0,
            "fraud_scenario": "NONE"
        }
        rows.append(row)
        txn_counter += 1

    # --------------------------------------------------------------------------
    # STEP 4: Generate Individual Fraud Transactions (approx 5% = 500)
    # --------------------------------------------------------------------------
    # WHY: Single fraudsters show abnormal behavior at the transaction level:
    # high transaction velocity, brand new account age, high failed attempts
    # due to guessing CVVs/OTPs, and rapid swapping of cards and devices.
    for _ in range(count_indiv_fraud):
        user_id = random.choice(indiv_fraud_users)
        device_id = f"D_INDIV_{random.randint(1, 400):04d}"
        ip_id = f"IP_INDIV_{random.randint(1, 400):04d}"
        card_id = f"C_INDIV_{random.randint(1, 400):04d}"
        merchant_id = random.choice(merchants)

        row = {
            "transaction_id": f"TXN_{txn_counter:06d}",
            "user_id": user_id,
            "amount": round(random.uniform(450.0, 3000.0), 2), # High transaction amount
            "account_age_days": random.randint(0, 7),          # Brand new accounts
            "device_id": device_id,
            "ip_id": ip_id,
            "card_id": card_id,
            "merchant_id": merchant_id,
            "transactions_last_hour": random.randint(6, 18),   # High hourly velocity
            "transactions_last_day": random.randint(15, 50),   # High daily velocity
            "failed_transactions": random.randint(3, 9),       # Card testing failures
            "unique_devices": random.randint(3, 7),           # Swapping multiple devices
            "unique_cards": random.randint(3, 8),             # Swapping multiple cards
            "is_fraud": 1,
            "fraud_scenario": "INDIVIDUAL_FRAUD"
        }
        rows.append(row)
        txn_counter += 1

    # --------------------------------------------------------------------------
    # STEP 5: Generate Coordinated Fraud-Ring Scenarios (approx 5% = 500 total)
    # --------------------------------------------------------------------------

    # Scenario 1: DEVICE_FARM (125 transactions)
    # WHY: A syndicate uses automated emulators or a physical phone farm on 1-2 devices.
    # Dozens of distinct user IDs conduct transactions from the exact same device ID.
    for _ in range(scenario_counts["DEVICE_FARM"]):
        user_id = random.choice(ring_farm_users)
        device_id = random.choice(ring_farm_devices)  # Shared farm device
        ip_id = random.choice(ring_farm_ips)          # Shared proxy IP
        card_id = f"C_FARM_{random.randint(1, 50):03d}"
        merchant_id = random.choice(merchants)

        row = {
            "transaction_id": f"TXN_{txn_counter:06d}",
            "user_id": user_id,
            "amount": round(random.uniform(60.0, 450.0), 2),
            "account_age_days": random.randint(0, 5),
            "device_id": device_id,
            "ip_id": ip_id,
            "card_id": card_id,
            "merchant_id": merchant_id,
            "transactions_last_hour": random.randint(7, 22),
            "transactions_last_day": random.randint(25, 70),
            "failed_transactions": random.randint(2, 7),
            "unique_devices": 1,                       # All activity locked to farm device
            "unique_cards": random.randint(2, 6),
            "is_fraud": 1,
            "fraud_scenario": "DEVICE_FARM"
        }
        rows.append(row)
        txn_counter += 1

    # Scenario 2: CARD_CYCLING (125 transactions)
    # WHY: Multiple user accounts take turns abusing a batch of stolen credit card numbers.
    # Individual accounts look somewhat separate, but analyzing card usage reveals a shared ring.
    for _ in range(scenario_counts["CARD_CYCLING"]):
        user_id = random.choice(ring_cycle_users)
        card_id = random.choice(ring_cycle_stolen_cards)  # Shared pool of stolen cards
        device_id = f"D_CYCLE_{random.randint(1, 30):03d}"
        ip_id = f"IP_CYCLE_{random.randint(1, 30):03d}"
        merchant_id = random.choice(merchants)

        row = {
            "transaction_id": f"TXN_{txn_counter:06d}",
            "user_id": user_id,
            "amount": round(random.uniform(120.0, 850.0), 2),
            "account_age_days": random.randint(1, 12),
            "device_id": device_id,
            "ip_id": ip_id,
            "card_id": card_id,
            "merchant_id": merchant_id,
            "transactions_last_hour": random.randint(4, 14),
            "transactions_last_day": random.randint(12, 40),
            "failed_transactions": random.randint(3, 10), # High declines on stolen cards
            "unique_devices": random.randint(2, 5),
            "unique_cards": random.randint(4, 9),         # High card cycling ratio
            "is_fraud": 1,
            "fraud_scenario": "CARD_CYCLING"
        }
        rows.append(row)
        txn_counter += 1

    # Scenario 3: ACCOUNT_BURST (125 transactions)
    # WHY: A syndicate creates a cluster of synthetic identity accounts on the exact same day.
    # They immediately execute high-velocity transactions to extract value before accounts get blocked.
    for _ in range(scenario_counts["ACCOUNT_BURST"]):
        user_id = random.choice(ring_burst_users)
        device_id = f"D_BURST_{random.randint(1, 20):03d}"
        ip_id = random.choice(ring_burst_ips)
        card_id = f"C_BURST_{random.randint(1, 30):03d}"
        merchant_id = random.choice(merchants)

        row = {
            "transaction_id": f"TXN_{txn_counter:06d}",
            "user_id": user_id,
            "amount": round(random.uniform(300.0, 1500.0), 2),
            "account_age_days": random.choice([0, 1]),   # Created today or yesterday!
            "device_id": device_id,
            "ip_id": ip_id,
            "card_id": card_id,
            "merchant_id": merchant_id,
            "transactions_last_hour": random.randint(10, 25), # Extreme immediate velocity
            "transactions_last_day": random.randint(15, 35),
            "failed_transactions": random.randint(1, 5),
            "unique_devices": random.randint(1, 3),
            "unique_cards": random.randint(1, 3),
            "is_fraud": 1,
            "fraud_scenario": "ACCOUNT_BURST"
        }
        rows.append(row)
        txn_counter += 1

    # Scenario 4: DISTRIBUTED_ABUSE (125 transactions)
    # WHY: Attackers distribute transactions across many accounts and IPs to keep single-user
    # velocity low and transaction amounts small (under typical threshold alerts), while targeting 
    # a single merchant in a coordinated attack.
    for _ in range(scenario_counts["DISTRIBUTED_ABUSE"]):
        user_id = random.choice(ring_dist_users)
        device_id = f"D_DIST_{random.randint(1, 30):03d}"
        ip_id = random.choice(ring_dist_ips)               # Shared proxy subnet
        card_id = f"C_DIST_{random.randint(1, 40):03d}"
        merchant_id = target_merchant                      # Targeted merchant

        row = {
            "transaction_id": f"TXN_{txn_counter:06d}",
            "user_id": user_id,
            "amount": round(random.uniform(15.0, 75.0), 2), # Low amount evades standard cap rules
            "account_age_days": random.randint(2, 25),
            "device_id": device_id,
            "ip_id": ip_id,
            "card_id": card_id,
            "merchant_id": merchant_id,
            "transactions_last_hour": random.randint(3, 8),
            "transactions_last_day": random.randint(6, 18),
            "failed_transactions": random.randint(0, 2),
            "unique_devices": random.randint(1, 2),
            "unique_cards": random.randint(1, 2),
            "is_fraud": 1,
            "fraud_scenario": "DISTRIBUTED_ABUSE"
        }
        rows.append(row)
        txn_counter += 1

    # --------------------------------------------------------------------------
    # STEP 6: Shuffle dataset
    # --------------------------------------------------------------------------
    # Shuffling simulates a realistic time-ordered or batch-logged stream where 
    # legitimate and fraudulent transactions occur interleaved.
    random.shuffle(rows)

    return rows


# ==============================================================================
# MAIN EXECUTION & FILE SAVING
# ==============================================================================

def main():
    """
    Creates output directory, generates dataset rows, writes to CSV,
    and runs self-verification checks.
    """
    print(f"Generating synthetic dataset with seed {RANDOM_SEED}...")
    
    # Ensure directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Generate data rows
    rows = generate_transactions()
    
    # CSV Header Columns (15 columns as specified)
    fieldnames = [
        "transaction_id",
        "user_id",
        "amount",
        "account_age_days",
        "device_id",
        "ip_id",
        "card_id",
        "merchant_id",
        "transactions_last_hour",
        "transactions_last_day",
        "failed_transactions",
        "unique_devices",
        "unique_cards",
        "is_fraud",
        "fraud_scenario"
    ]

    # Write to CSV
    with open(OUTPUT_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        
    print(f"Dataset successfully written to: {OUTPUT_FILE}\n")

    # ==========================================================================
    # VERIFICATION CHECKS
    # ==========================================================================
    print("=" * 60)
    print("RUNNING VERIFICATION CHECKS")
    print("=" * 60)

    # 1. Row Count Check
    total_rows = len(rows)
    print(f"1. Total Rows Generated: {total_rows} (Expected: {TOTAL_TRANSACTIONS})")
    assert total_rows == TOTAL_TRANSACTIONS, "Row count mismatch!"

    # 2. Missing Value Check
    missing_count = 0
    for r in rows:
        for val in r.values():
            if val is None or val == "":
                missing_count += 1
    print(f"2. Missing Values Found: {missing_count} (Expected: 0)")
    assert missing_count == 0, "Dataset contains missing values!"

    # 3. Target values present
    fraud_values = set(r["is_fraud"] for r in rows)
    print(f"3. Unique 'is_fraud' values: {sorted(list(fraud_values))} (Expected: [0, 1])")
    assert fraud_values == {0, 1}, "is_fraud must contain both 0 and 1!"

    # 4. Scenarios Check
    scenarios_found = set(r["fraud_scenario"] for r in rows)
    expected_scenarios = {"NONE", "INDIVIDUAL_FRAUD", "DEVICE_FARM", "CARD_CYCLING", "ACCOUNT_BURST", "DISTRIBUTED_ABUSE"}
    print(f"4. Fraud Scenarios Found: {sorted(list(scenarios_found))}")
    assert expected_scenarios.issubset(scenarios_found), "Missing required fraud scenarios!"

    # 5. Class Distribution & Percentages
    fraud_counts = {0: 0, 1: 0}
    scenario_counts = {}
    for r in rows:
        fraud_counts[r["is_fraud"]] += 1
        sc = r["fraud_scenario"]
        scenario_counts[sc] = scenario_counts.get(sc, 0) + 1

    print("\n--- Class Distribution ---")
    for is_f, cnt in sorted(fraud_counts.items()):
        pct = (cnt / total_rows) * 100
        label = "Legitimate (0)" if is_f == 0 else "Fraud (1)"
        print(f"  {label}: {cnt} rows ({pct:.2f}%)")

    print("\n--- Fraud Scenario Distribution ---")
    for sc, cnt in sorted(scenario_counts.items(), key=lambda x: x[1], reverse=True):
        pct = (cnt / total_rows) * 100
        print(f"  {sc:20s}: {cnt} rows ({pct:.2f}%)")

    # Display First 10 Rows
    print("\n" + "=" * 60)
    print("FIRST 10 ROWS SAMPLE")
    print("=" * 60)
    for idx, row in enumerate(rows[:10], start=1):
        print(f"Row {idx:02d}: {row}")


if __name__ == "__main__":
    main()
