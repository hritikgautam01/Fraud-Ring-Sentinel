"""
Sentinel — Coordinated Payment Abuse Intelligence
Module: Real Pipeline Integration Test (test_pipeline_integration.py)

Purpose:
Executes an end-to-end integration test running a real transaction from dataset v3 through:
  Existing Detection (RF Baseline + Graph Analyzer + Behavioral Analyzer)
  -> Existing Fusion Output (compute_fusion_risk)
  -> Evidence Builder (build_investigation_case)
  -> Data Contract Schema (to_dict)
  -> Evidence Validator (validate_investigation_case)
  -> LLM Investigator (generate_report)
  -> Report Validator (validate_investigation_report)
"""

import json
import os
import pandas as pd
import joblib

try:
    from ml.graph.build_graph import build_heterogeneous_graph
    from ml.graph.detect_rings import extract_candidate_clusters
    from ml.graph.fusion_risk import compute_fusion_risk
    from ml.investigator.evidence_builder import build_investigation_case
    from ml.investigator.validate_evidence import validate_investigation_case
    from ml.investigator.llm_investigator import LLMInvestigator
    from ml.investigator.validate_report import validate_investigation_report
except ImportError:
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    from ml.graph.build_graph import build_heterogeneous_graph
    from ml.graph.detect_rings import extract_candidate_clusters
    from ml.graph.fusion_risk import compute_fusion_risk
    from ml.investigator.evidence_builder import build_investigation_case
    from ml.investigator.validate_evidence import validate_investigation_case
    from ml.investigator.llm_investigator import LLMInvestigator
    from ml.investigator.validate_report import validate_investigation_report


def run_pipeline_test():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    v3_path = os.path.join(project_root, "ml", "data", "raw", "transactions_v3.csv")
    model_path = os.path.join(project_root, "ml", "models", "frozen_rf_model.joblib")

    print("=" * 80)
    print("SENTINEL FULL PIPELINE INTEGRATION TEST (DETECTION -> EVIDENCE -> LLM REPORT)")
    print("=" * 80)

    # 1. Load Real Transaction Row
    print("\n[Step 1] Loading real transaction record from transactions_v3.csv...")
    df = pd.read_csv(v3_path)
    txn_row = df[df["transaction_id"] == "TXN_V3_009900"].iloc[0].to_dict()
    print(f"  • Transaction ID: {txn_row['transaction_id']}")
    print(f"  • User ID: {txn_row['user_id']}")
    print(f"  • Amount: ${txn_row['amount']}")

    # 2. Run Single-Transaction Random Forest Prediction
    print("\n[Step 2] Executing ML Model inference (RandomForestClassifier)...")
    model = joblib.load(model_path)
    features = [
        "amount", "account_age_days", "transactions_last_hour",
        "transactions_last_day", "failed_transactions", "unique_devices", "unique_cards"
    ]
    X = pd.DataFrame([txn_row])[features]
    ml_prob = float(model.predict_proba(X)[0, 1])
    print(f"  • Predicted Anomaly Probability: {ml_prob:.4f}")

    # 3. Build Graph & Extract Cluster Statistics
    print("\n[Step 3] Constructing heterogeneous graph & extracting topology clusters...")
    G = build_heterogeneous_graph(df)
    clusters = extract_candidate_clusters(G)

    user_node = f"USER:{txn_row['user_id']}"
    cluster_stats = next((c for c in clusters if user_node in c["users"]), {})
    print(f"  • Matched Infrastructure Cluster User Count: {cluster_stats.get('user_count', 1)}")

    # 4. Compute Fusion Risk Engine Score
    print("\n[Step 4] Computing Fusion Risk Engine outcome...")
    fusion_res = compute_fusion_risk(txn_row, ml_prob, cluster_stats)
    print(f"  • Combined Risk Score: {fusion_res['combined_risk']}")
    print(f"  • Deterministic Risk Level: {fusion_res['risk_level']}")
    print(f"  • Deterministic Action: {fusion_res['action']}")
    print(f"  • Threshold Applied: {fusion_res['threshold_applied']}")

    # 5. Build Investigation Case via Evidence Builder
    print("\n[Step 5] Normalizing outputs via Evidence Builder pure adapter...")
    case = build_investigation_case(txn_row, ml_prob, cluster_stats, fusion_res)
    case_dict = case.to_dict()

    # 6. Validate Evidence Data Contract Schema
    print("\n[Step 6] Running evidence schema & ground-truth validation...")
    is_ev_valid, ev_errors = validate_investigation_case(case_dict)
    assert is_ev_valid, f"Evidence validation failed: {ev_errors}"
    print("  ✓ PASS: InvestigationCase strictly adheres to data contract schema with ZERO ground-truth leakage!")

    # 7. LLM Investigator Explanation & Report Generation
    print("\n[Step 7] Generating human-readable InvestigationReport via LLM Investigator...")
    investigator = LLMInvestigator()
    report = investigator.generate_report(case)
    report_dict = report.to_dict()

    # 8. Validate Investigation Report
    print("\n[Step 8] Validating InvestigationReport schema and decision authority...")
    is_rep_valid, rep_errors = validate_investigation_report(report_dict, expected_case=case_dict)
    assert is_rep_valid, f"Report validation failed: {rep_errors}"
    print("  ✓ PASS: InvestigationReport matches deterministic decision authority & passes all schema checks!")

    print("\n" + "=" * 80)
    print("FINAL SERIALIZED INVESTIGATION REPORT JSON OUTPUT:")
    print("=" * 80)
    print(json.dumps(report_dict, indent=2))

    return is_rep_valid


if __name__ == "__main__":
    run_pipeline_test()
