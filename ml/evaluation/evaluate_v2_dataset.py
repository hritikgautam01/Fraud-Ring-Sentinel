"""
Sentinel — Coordinated Payment Abuse Intelligence
Module: V2 Evaluation Comparison Engine (evaluate_v2_dataset.py)

Purpose:
Compares the single-transaction Random Forest baseline against the Graph Detector
on the realistic transactions_v2.csv dataset (which contains realistic feature overlap).

Metrics Reported:
- Precision, Recall, F1-Score
- False Positives & False Negatives
- Coordinated Fraud Detection Rate (Overall)
- Individual Fraud Detection Rate
- Per-Scenario Detection Rate (DEVICE_FARM, CARD_CYCLING, ACCOUNT_BURST, DISTRIBUTED_ABUSE)
"""

import os
import sys
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
from sklearn.model_selection import train_test_split

# Add graph module directory to path for imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
GRAPH_DIR = os.path.join(PROJECT_ROOT, "ml", "graph")
sys.path.append(GRAPH_DIR)

from build_graph import build_heterogeneous_graph
from detect_rings import extract_candidate_clusters
from ring_risk import calculate_ring_risk


def main():
    v2_csv_path = os.path.join(PROJECT_ROOT, "ml", "data", "raw", "transactions_v2.csv")

    if not os.path.exists(v2_csv_path):
        raise FileNotFoundError(f"V2 dataset not found at: {v2_csv_path}")

    print("=" * 70)
    print("SENTINEL EVALUATION: BASELINE ML vs. GRAPH DETECTOR (DATASET V2)")
    print("=" * 70)
    print(f"Loading V2 dataset from: {v2_csv_path}\n")

    df = pd.read_csv(v2_csv_path)
    total_txns = len(df)
    print(f"Dataset V2 loaded: {total_txns:,} records.")

    # --------------------------------------------------------------------------
    # 1. EVALUATE TRANSACTION-LEVEL ML BASELINE (RANDOM FOREST)
    # --------------------------------------------------------------------------
    features = [
        "amount", "account_age_days", "transactions_last_hour",
        "transactions_last_day", "failed_transactions",
        "unique_devices", "unique_cards"
    ]
    
    X = df[features]
    y = df["is_fraud"]

    # 80/20 train/test split (stratified)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
    rf_model.fit(X_train, y_train)

    # Predictions on test set (2,000 samples)
    rf_preds = rf_model.predict(X_test)
    test_df = df.iloc[X_test.index].copy()
    test_df["rf_pred"] = rf_preds

    # RF Metrics
    rf_prec = precision_score(y_test, rf_preds, zero_division=0)
    rf_rec = recall_score(y_test, rf_preds, zero_division=0)
    rf_f1 = f1_score(y_test, rf_preds, zero_division=0)

    tn_rf, fp_rf, fn_rf, tp_rf = confusion_matrix(y_test, rf_preds).ravel()

    # Per-scenario detection rates for ML Baseline on test set
    scenarios = ["INDIVIDUAL_FRAUD", "DEVICE_FARM", "CARD_CYCLING", "ACCOUNT_BURST", "DISTRIBUTED_ABUSE"]
    rf_scenario_stats = {}

    for sc in scenarios:
        sc_test = test_df[test_df["fraud_scenario"] == sc]
        if len(sc_test) > 0:
            detected = sum(sc_test["rf_pred"] == 1)
            rate = (detected / len(sc_test)) * 100
            rf_scenario_stats[sc] = {"total": len(sc_test), "detected": detected, "rate": rate}
        else:
            rf_scenario_stats[sc] = {"total": 0, "detected": 0, "rate": 0.0}

    coord_scenarios = ["DEVICE_FARM", "CARD_CYCLING", "ACCOUNT_BURST", "DISTRIBUTED_ABUSE"]
    coord_test_rf = test_df[test_df["fraud_scenario"].isin(coord_scenarios)]
    rf_coord_detected = sum(coord_test_rf["rf_pred"] == 1)
    rf_coord_rate = (rf_coord_detected / max(1, len(coord_test_rf))) * 100

    # --------------------------------------------------------------------------
    # 2. EVALUATE GRAPH DETECTOR
    # --------------------------------------------------------------------------
    graph = build_heterogeneous_graph(df)
    candidate_clusters = extract_candidate_clusters(graph)

    suspicious_rings = []
    for cand in candidate_clusters:
        risk_res = calculate_ring_risk(cand)
        if risk_res["is_suspicious_ring"]:
            suspicious_rings.append(risk_res)

    # Collect all transaction IDs flagged as fraud rings by graph detector
    graph_flagged_txn_ids = set()
    for ring in suspicious_rings:
        graph_flagged_txn_ids.update(ring["details"]["transactions"])

    df["graph_pred"] = df["transaction_id"].astype(str).isin(graph_flagged_txn_ids).astype(int)

    # Evaluate Graph detector on the test set slice for direct 1-to-1 comparison
    test_df["graph_pred"] = df.iloc[X_test.index]["graph_pred"].values

    graph_prec = precision_score(y_test, test_df["graph_pred"], zero_division=0)
    graph_rec = recall_score(y_test, test_df["graph_pred"], zero_division=0)
    graph_f1 = f1_score(y_test, test_df["graph_pred"], zero_division=0)

    tn_g, fp_g, fn_g, tp_g = confusion_matrix(y_test, test_df["graph_pred"]).ravel()

    graph_scenario_stats = {}
    for sc in scenarios:
        sc_test = test_df[test_df["fraud_scenario"] == sc]
        if len(sc_test) > 0:
            detected = sum(sc_test["graph_pred"] == 1)
            rate = (detected / len(sc_test)) * 100
            graph_scenario_stats[sc] = {"total": len(sc_test), "detected": detected, "rate": rate}
        else:
            graph_scenario_stats[sc] = {"total": 0, "detected": 0, "rate": 0.0}

    coord_test_g = test_df[test_df["fraud_scenario"].isin(coord_scenarios)]
    graph_coord_detected = sum(coord_test_g["graph_pred"] == 1)
    graph_coord_rate = (graph_coord_detected / max(1, len(coord_test_g))) * 100

    # Also calculate Full Dataset Graph Detection Metrics for Coordinated Fraud
    full_coord_df = df[df["fraud_scenario"].isin(coord_scenarios)]
    full_graph_coord_detected = sum(full_coord_df["graph_pred"] == 1)
    full_graph_coord_rate = (full_graph_coord_detected / max(1, len(full_coord_df))) * 100

    # --------------------------------------------------------------------------
    # 3. PRINT COMPARATIVE EVALUATION REPORT
    # --------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("COMPARATIVE EVALUATION SUMMARY (TEST SET = 2,000 TRANSACTIONS)")
    print("=" * 70)

    print(f"\n{'Metric / Evaluation Dimension':<35s} | {'Transaction ML (RF)':<20s} | {'Graph Detector':<18s}")
    print("-" * 78)
    print(f"{'Precision':<35s} | {rf_prec * 100:18.2f}% | {graph_prec * 100:16.2f}%")
    print(f"{'Recall (Overall Fraud)':<35s} | {rf_rec * 100:18.2f}% | {graph_rec * 100:16.2f}%")
    print(f"{'F1-Score':<35s} | {rf_f1 * 100:18.2f}% | {graph_f1 * 100:16.2f}%")
    print(f"{'False Positives (Legit flagged)':<35s} | {fp_rf:18d}  | {fp_g:16d} ")
    print(f"{'False Negatives (Fraud missed)':<35s} | {fn_rf:18d}  | {fn_g:16d} ")
    print("-" * 78)
    print(f"{'Individual Fraud Detection Rate':<35s} | {rf_scenario_stats['INDIVIDUAL_FRAUD']['rate']:18.2f}% | {graph_scenario_stats['INDIVIDUAL_FRAUD']['rate']:16.2f}%")
    print(f"{'Coordinated Fraud Ring Rate (Overall)':<35s} | {rf_coord_rate:18.2f}% | {graph_coord_rate:16.2f}%")
    
    print("\n" + "-" * 70)
    print("COORDINATED FRAUD SCENARIO BREAKDOWN (TEST SET DETECTIONS)")
    print("-" * 70)
    print(f"{'Scenario':<22s} | {'Test Total':<10s} | {'ML Baseline Rate':<18s} | {'Graph Detector Rate':<18s}")
    print("-" * 75)
    for sc in coord_scenarios:
        tot = rf_scenario_stats[sc]['total']
        ml_r = rf_scenario_stats[sc]['rate']
        gr_r = graph_scenario_stats[sc]['rate']
        print(f"{sc:<22s} | {tot:<10d} | {ml_r:16.2f}% | {gr_r:16.2f}%")

    print("\n" + "-" * 70)
    print("FULL DATASET GRAPH DETECTION METRICS (10,000 TRANSACTIONS)")
    print("-" * 70)
    print(f"Total Coordinated Fraud Transactions in V2: 500")
    print(f"Coordinated Fraud Transactions Flagged by Graph: {full_graph_coord_detected}")
    print(f"Overall Coordinated Ring Detection Rate        : {full_graph_coord_rate:.2f}%")
    
    for sc in coord_scenarios:
        sc_full = df[df["fraud_scenario"] == sc]
        det_full = sum(sc_full["graph_pred"] == 1)
        r_full = (det_full / max(1, len(sc_full))) * 100
        print(f"  • {sc:20s}: {det_full:3d} / {len(sc_full):3d} detected ({r_full:6.2f}%)")

    print("=" * 70)


if __name__ == "__main__":
    main()
