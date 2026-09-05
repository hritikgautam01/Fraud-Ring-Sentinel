"""
Sentinel — Coordinated Payment Abuse Intelligence
Module: V5 Independent Blind Test Evaluation Suite (evaluate_v5_independent.py)

Purpose:
Performs the final, blind-style generalization benchmark on transactions_v5_independent.csv.

STRICT RULE COMPLIANCE:
-----------------------
- FROZEN MODEL: Loads ml/models/frozen_rf_model.joblib (Trained on V3). ZERO retraining on V5.
- FROZEN GRAPH DETECTOR: Static threshold = 35.0. ZERO threshold tuning.
- FROZEN FUSION WEIGHTS: 0.40 ML, 0.35 Graph, 0.25 Behavioral, Alert Threshold = 0.45.
- ZERO CODE OR PARAMETER MODIFICATIONS.
"""

import os
import sys
import joblib
import pandas as pd
import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
GRAPH_DIR = os.path.join(PROJECT_ROOT, "ml", "graph")
sys.path.append(GRAPH_DIR)

from build_graph import build_heterogeneous_graph
from detect_rings import extract_candidate_clusters
from ring_risk import calculate_ring_risk
from fusion_risk import compute_fusion_risk, FUSION_RISK_THRESHOLD


def main():
    v5_csv_path = os.path.join(PROJECT_ROOT, "ml", "data", "raw", "transactions_v5_independent.csv")
    rf_model_path = os.path.join(PROJECT_ROOT, "ml", "models", "frozen_rf_model.joblib")

    if not os.path.exists(v5_csv_path):
        raise FileNotFoundError(f"V5 dataset not found at: {v5_csv_path}")
    if not os.path.exists(rf_model_path):
        raise FileNotFoundError(f"Frozen RF model not found at: {rf_model_path}")

    v5_df = pd.read_csv(v5_csv_path)
    frozen_rf = joblib.load(rf_model_path)

    ml_features = [
        "amount", "account_age_days", "transactions_last_hour",
        "transactions_last_day", "failed_transactions",
        "unique_devices", "unique_cards"
    ]

    print("=" * 85)
    print("SENTINEL V5 INDEPENDENT BLIND BENCHMARK RUNNER")
    print("=" * 85)
    print(f"Loaded Fresh Independent V5 Dataset: {len(v5_df):,} records.")
    print(f"Loaded Frozen Random Forest Model (Trained on V3): {rf_model_path}\n")

    # --------------------------------------------------------------------------
    # 1. EVALUATE FROZEN RANDOM FOREST MODEL (NO RETRAINING)
    # --------------------------------------------------------------------------
    v5_df["rf_proba"] = frozen_rf.predict_proba(v5_df[ml_features])[:, 1]
    v5_df["rf_pred"] = (v5_df["rf_proba"] >= 0.50).astype(int)

    # --------------------------------------------------------------------------
    # 2. EVALUATE FROZEN GRAPH DETECTOR (STATIC THRESHOLD = 35.0)
    # --------------------------------------------------------------------------
    graph = build_heterogeneous_graph(v5_df)
    candidate_clusters = extract_candidate_clusters(graph)

    txn_to_cluster = {}
    graph_flagged_txn_ids = set()
    suspicious_rings = []

    for cand in candidate_clusters:
        risk_res = calculate_ring_risk(cand)
        if risk_res["is_suspicious_ring"]:
            suspicious_rings.append(risk_res)
            graph_flagged_txn_ids.update(risk_res["details"]["transactions"])
        
        for t_id in cand["transaction_nodes"]:
            clean_t_id = t_id.replace("TRANSACTION:", "")
            txn_to_cluster[clean_t_id] = cand

    v5_df["graph_pred"] = v5_df["transaction_id"].astype(str).isin(graph_flagged_txn_ids).astype(int)

    # --------------------------------------------------------------------------
    # 3. EVALUATE FROZEN FUSION SYSTEM (FROZEN WEIGHTS 0.40/0.35/0.25, THRESHOLD 0.45)
    # --------------------------------------------------------------------------
    fusion_preds = []
    for idx, row in v5_df.iterrows():
        t_id = str(row["transaction_id"])
        ml_prob = float(row["rf_proba"])
        cand_stats = txn_to_cluster.get(t_id, {
            "user_count": 1, "device_count": 1, "ip_count": 1, "card_count": 1,
            "merchant_concentration": 0.0, "top_merchant_id": "N/A",
            "avg_account_age": float(row["account_age_days"]),
            "avg_failed_tx": float(row["failed_transactions"]),
            "avg_tx_hour": float(row["transactions_last_hour"])
        })
        
        f_res = compute_fusion_risk(row.to_dict(), ml_prob, cand_stats)
        fusion_preds.append(1 if f_res["is_flagged_fraud"] else 0)

    v5_df["fusion_pred"] = fusion_preds

    # --------------------------------------------------------------------------
    # METRICS CALCULATION
    # --------------------------------------------------------------------------
    y_true = v5_df["is_fraud"]
    coord_scenarios = ["DEVICE_FARM", "CARD_CYCLING", "ACCOUNT_BURST", "DISTRIBUTED_ABUSE"]

    def get_full_metrics(pred_col):
        preds = v5_df[pred_col]
        prec = precision_score(y_true, preds, zero_division=0) * 100
        rec = recall_score(y_true, preds, zero_division=0) * 100
        f1 = f1_score(y_true, preds, zero_division=0) * 100
        tn, fp, fn, tp = confusion_matrix(y_true, preds).ravel()

        indiv_df = v5_df[v5_df["fraud_scenario"] == "INDIVIDUAL_FRAUD"]
        indiv_rate = (sum(indiv_df[pred_col] == 1) / max(1, len(indiv_df))) * 100

        coord_df = v5_df[v5_df["fraud_scenario"].isin(coord_scenarios)]
        coord_rate = (sum(coord_df[pred_col] == 1) / max(1, len(coord_df))) * 100

        sc_rates = {}
        for sc in coord_scenarios:
            sc_df = v5_df[v5_df["fraud_scenario"] == sc]
            sc_rates[sc] = (sum(sc_df[pred_col] == 1) / max(1, len(sc_df))) * 100

        return {
            "prec": prec, "rec": rec, "f1": f1, "tp": tp, "fp": fp, "fn": fn,
            "indiv_rate": indiv_rate, "coord_rate": coord_rate, "scenarios": sc_rates
        }

    m_rf = get_full_metrics("rf_pred")
    m_gr = get_full_metrics("graph_pred")
    m_fu = get_full_metrics("fusion_pred")

    # --------------------------------------------------------------------------
    # COMPARISON TABLE: V3 vs V5
    # --------------------------------------------------------------------------
    # V3 metrics from earlier benchmark: RF (99.75% F1), Graph (33.67% F1), Fusion (100.00% F1)
    rf_f1_str = f"{m_rf['f1']:.2f}%"
    rf_diff_str = f"{m_rf['f1'] - 99.75:+.2f}%"
    gr_f1_str = f"{m_gr['f1']:.2f}%"
    gr_diff_str = f"{m_gr['f1'] - 33.67:+.2f}%"
    fu_f1_str = f"{m_fu['f1']:.2f}%"
    fu_diff_str = f"{m_fu['f1'] - 100.00:+.2f}%"

    print("=" * 85)
    print("V3 RESULT vs V5 INDEPENDENT RESULT COMPARISON")
    print("=" * 85)
    print(f"{'System':<25s} | {'V3 F1-Score':<15s} | {'V5 F1-Score':<15s} | {'Change':<15s}")
    print("-" * 75)
    print(f"{'Random Forest (ML)':<25s} | {'99.75%':<15s} | {rf_f1_str:<15s} | {rf_diff_str:<15s}")
    print(f"{'Graph Detector Alone':<25s} | {'33.67%':<15s} | {gr_f1_str:<15s} | {gr_diff_str:<15s}")
    print(f"{'Fusion System':<25s} | {'100.00%':<15s} | {fu_f1_str:<15s} | {fu_diff_str:<15s}")

    print("\n" + "=" * 85)
    print("V5 DETAILED SYSTEM RESULTS (10,000 TRANSACTIONS)")
    print("=" * 85)
    print(f"{'System':<25s} | {'Precision':<10s} | {'Recall':<10s} | {'F1-Score':<10s} | {'TP':<6s} | {'FP':<6s} | {'FN':<6s}")
    print("-" * 80)
    print(f"{'Random Forest (ML)':<25s} | {m_rf['prec']:9.2f}% | {m_rf['rec']:9.2f}% | {m_rf['f1']:9.2f}% | {m_rf['tp']:6d} | {m_rf['fp']:6d} | {m_rf['fn']:6d}")
    print(f"{'Graph Detector Alone':<25s} | {m_gr['prec']:9.2f}% | {m_gr['rec']:9.2f}% | {m_gr['f1']:9.2f}% | {m_gr['tp']:6d} | {m_gr['fp']:6d} | {m_gr['fn']:6d}")
    print(f"{'Fusion System':<25s} | {m_fu['prec']:9.2f}% | {m_fu['rec']:9.2f}% | {m_fu['f1']:9.2f}% | {m_fu['tp']:6d} | {m_fu['fp']:6d} | {m_fu['fn']:6d}")

    print("\n" + "=" * 85)
    print("INDIVIDUAL vs COORDINATED FRAUD (V5 DATASET)")
    print("=" * 85)
    print(f"{'System':<25s} | {'Individual Detection Rate':<25s} | {'Coordinated Detection Rate':<25s}")
    print("-" * 80)
    print(f"{'Random Forest (ML)':<25s} | {m_rf['indiv_rate']:23.2f}% | {m_rf['coord_rate']:23.2f}%")
    print(f"{'Graph Detector Alone':<25s} | {m_gr['indiv_rate']:23.2f}% | {m_gr['coord_rate']:23.2f}%")
    print(f"{'Fusion System':<25s} | {m_fu['indiv_rate']:23.2f}% | {m_fu['coord_rate']:23.2f}%")

    print("\n" + "=" * 85)
    print("COORDINATED FRAUD SCENARIO DETECTIONS (V5 DATASET)")
    print("=" * 85)
    print(f"{'Scenario':<25s} | {'Random Forest (ML)':<20s} | {'Graph Detector':<18s} | {'Fusion System':<15s}")
    print("-" * 85)
    for sc in coord_scenarios:
        print(f"{sc:<25s} | {m_rf['scenarios'][sc]:18.2f}% | {m_gr['scenarios'][sc]:16.2f}% | {m_fu['scenarios'][sc]:13.2f}%")

    # --------------------------------------------------------------------------
    # BENIGN NETWORK STRESS TEST TABLE
    # --------------------------------------------------------------------------
    print("\n" + "=" * 85)
    print("BENIGN NETWORK STRESS TEST TABLE (V5 DATASET)")
    print("=" * 85)
    benign_scenarios_v5 = [
        "FAMILY_NETWORK", "OFFICE_NETWORK", "HOSTEL_NETWORK",
        "PUBLIC_WIFI_NETWORK", "LEGITIMATE_BUSINESS_NETWORK"
    ]
    print(f"{'Scenario':<30s} | {'Txns':<7s} | {'Flagged Txns':<13s} | {'False Positive Rate':<18s}")
    print("-" * 75)
    for b_sc in benign_scenarios_v5:
        b_df = v5_df[v5_df["fraud_scenario"] == b_sc]
        tot = len(b_df)
        flagged = sum(b_df["fusion_pred"] == 1)
        fpr = (flagged / max(1, tot)) * 100
        print(f"{b_sc:<30s} | {tot:<7d} | {flagged:<13d} | {fpr:16.2f}%")

    # --------------------------------------------------------------------------
    # MODEL SHORTCUT TEST (FEATURE DISTRIBUTION SHIFT ANALYSIS)
    # --------------------------------------------------------------------------
    print("\n" + "=" * 85)
    print("MODEL SHORTCUT TEST: FEATURE IMPORTANCE vs DISTRIBUTION SHIFT")
    print("=" * 85)
    v3_df = pd.read_csv(os.path.join(PROJECT_ROOT, "ml", "data", "raw", "transactions_v3.csv"))
    
    importances = frozen_rf.feature_importances_
    for feat, imp in sorted(zip(ml_features, importances), key=lambda x: x[1], reverse=True):
        v3_legit_mean = v3_df[v3_df["is_fraud"] == 0][feat].mean()
        v5_legit_mean = v5_df[v5_df["is_fraud"] == 0][feat].mean()
        v3_fraud_mean = v3_df[v3_df["is_fraud"] == 1][feat].mean()
        v5_fraud_mean = v5_df[v5_df["is_fraud"] == 1][feat].mean()
        
        print(f"Feature: {feat:22s} | Importance: {imp*100:5.2f}%")
        print(f"  • Legit Mean  : V3={v3_legit_mean:8.2f} -> V5={v5_legit_mean:8.2f}")
        print(f"  • Fraud Mean  : V3={v3_fraud_mean:8.2f} -> V5={v5_fraud_mean:8.2f}")
    print("=" * 85 + "\n")


if __name__ == "__main__":
    main()
