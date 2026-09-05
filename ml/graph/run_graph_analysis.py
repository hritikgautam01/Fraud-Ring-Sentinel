"""
Sentinel — Coordinated Payment Abuse Intelligence
Main Script: Graph Analysis Runner (run_graph_analysis.py)

Purpose:
Orchestrates the graph analysis pipeline:
1. Loads synthetic transaction dataset
2. Builds heterogeneous NetworkX graph
3. Discovers infrastructure-sharing clusters
4. Evaluates ring risk scores & generates evidence
5. Compares detected rings against ground truth scenarios (for evaluation only)
6. Prints a detailed investigation report
7. Saves structured JSON output to ml/graph/output/ring_results.json
"""

import json
import os
import pandas as pd
from build_graph import build_heterogeneous_graph
from detect_rings import extract_candidate_clusters
from ring_risk import calculate_ring_risk, RISK_THRESHOLD

# ==============================================================================
# MAIN GRAPH ANALYSIS RUNNER
# ==============================================================================

def main():
    # --------------------------------------------------------------------------
    # Path Setup
    # --------------------------------------------------------------------------
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
    
    csv_path = os.path.join(project_root, "ml", "data", "raw", "transactions.csv")
    output_dir = os.path.join(script_dir, "output")
    json_output_path = os.path.join(output_dir, "ring_results.json")
    
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 60)
    print("FRAUD RING SENTINEL — GRAPH ANALYSIS ENGINE")
    print("=" * 60)
    
    # --------------------------------------------------------------------------
    # 1. Load Dataset & Build Graph
    # --------------------------------------------------------------------------
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset not found at: {csv_path}")

    df = pd.read_csv(csv_path)
    graph = build_heterogeneous_graph(df)

    # Node summary stats
    node_type_counts = {}
    for _, attrs in graph.nodes(data=True):
        ntype = attrs.get("node_type", "UNKNOWN")
        node_type_counts[ntype] = node_type_counts.get(ntype, 0) + 1

    # --------------------------------------------------------------------------
    # 2. Extract Infrastructure Candidate Clusters & Calculate Ring Risk Scores
    # --------------------------------------------------------------------------
    candidate_clusters = extract_candidate_clusters(graph)
    
    evaluated_rings = []
    suspicious_rings = []
    benign_shared_clusters = []

    ring_counter = 1
    for cand in candidate_clusters:
        risk_result = calculate_ring_risk(cand)
        
        if risk_result["is_suspicious_ring"]:
            risk_result["cluster_id"] = f"RING_{ring_counter:03d}"
            suspicious_rings.append(risk_result)
            ring_counter += 1
        else:
            risk_result["cluster_id"] = f"BENIGN_INFRA_{len(benign_shared_clusters)+1:03d}"
            benign_shared_clusters.append(risk_result)
            
        evaluated_rings.append(risk_result)

    # Sort suspicious rings by risk score descending
    suspicious_rings.sort(key=lambda x: x["risk_score"], reverse=True)

    # --------------------------------------------------------------------------
    # 3. Ground Truth Evaluation (AFTER Detection)
    # --------------------------------------------------------------------------
    # Collect all transaction IDs captured by detected suspicious fraud rings
    detected_fraud_txn_ids = set()
    for ring in suspicious_rings:
        detected_fraud_txn_ids.update(ring["details"]["transactions"])

    # Count ground truth breakdown from original CSV
    gt_scenario_counts = df["fraud_scenario"].value_counts().to_dict()
    
    # Calculate detection metrics for each scenario
    detected_counts_by_scenario = {}
    for sc in ["DEVICE_FARM", "CARD_CYCLING", "ACCOUNT_BURST", "DISTRIBUTED_ABUSE", "INDIVIDUAL_FRAUD", "NONE"]:
        sc_txns = set(df[df["fraud_scenario"] == sc]["transaction_id"].astype(str))
        detected_sc_txns = sc_txns.intersection(detected_fraud_txn_ids)
        detected_counts_by_scenario[sc] = len(detected_sc_txns)

    total_coordinated_gt = sum(gt_scenario_counts.get(sc, 0) for sc in ["DEVICE_FARM", "CARD_CYCLING", "ACCOUNT_BURST", "DISTRIBUTED_ABUSE"])
    total_coordinated_detected = sum(detected_counts_by_scenario.get(sc, 0) for sc in ["DEVICE_FARM", "CARD_CYCLING", "ACCOUNT_BURST", "DISTRIBUTED_ABUSE"])
    
    overall_detection_rate = (total_coordinated_detected / max(1, total_coordinated_gt)) * 100
    false_positives_legit = detected_counts_by_scenario.get("NONE", 0)

    # --------------------------------------------------------------------------
    # 4. Save Structured JSON Output
    # --------------------------------------------------------------------------
    json_payload = {
        "summary": {
            "total_transactions": len(df),
            "total_nodes": graph.number_of_nodes(),
            "total_edges": graph.number_of_edges(),
            "node_breakdown": node_type_counts,
            "total_candidate_clusters": len(candidate_clusters),
            "detected_suspicious_rings_count": len(suspicious_rings),
            "benign_shared_infrastructure_count": len(benign_shared_clusters),
            "risk_score_threshold": RISK_THRESHOLD
        },
        "suspicious_rings": [
            {
                "cluster_id": r["cluster_id"],
                "risk_score": r["risk_score"],
                "likely_pattern": r["likely_pattern"],
                "users": r["users_count"],
                "devices": r["devices_count"],
                "ips": r["ips_count"],
                "cards": r["cards_count"],
                "transactions": r["transactions_count"],
                "merchants": r["merchants_count"],
                "evidence": r["evidence"],
                "ground_truth_scenario_breakdown": r["ground_truth_scenarios"],
                "details": r["details"]
            }
            for r in suspicious_rings
        ],
        "evaluation": {
            "total_coordinated_fraud_transactions": total_coordinated_gt,
            "detected_coordinated_fraud_transactions": total_coordinated_detected,
            "overall_coordinated_detection_rate_pct": round(overall_detection_rate, 2),
            "scenario_breakdown": {
                sc: {
                    "total_in_dataset": gt_scenario_counts.get(sc, 0),
                    "detected_by_graph": detected_counts_by_scenario.get(sc, 0),
                    "detection_rate_pct": round((detected_counts_by_scenario.get(sc, 0) / max(1, gt_scenario_counts.get(sc, 0))) * 100, 2)
                }
                for sc in ["DEVICE_FARM", "CARD_CYCLING", "ACCOUNT_BURST", "DISTRIBUTED_ABUSE"]
            },
            "false_positives_legitimate_transactions": false_positives_legit
        }
    }

    with open(json_output_path, "w", encoding="utf-8") as f:
        json.dump(json_payload, f, indent=2)

    print(f"\nResults successfully exported to JSON: {json_output_path}\n")

    # --------------------------------------------------------------------------
    # 5. Print Formatted Investigation Report
    # --------------------------------------------------------------------------
    print("=" * 60)
    print("FRAUD RING SENTINEL — GRAPH ANALYSIS REPORT")
    print("=" * 60)
    print(f"Total transactions analyzed: {len(df):,}")
    print("\nGraph Nodes Breakdown:")
    print(f"  • Users        : {node_type_counts.get('USER', 0):,}")
    print(f"  • Devices      : {node_type_counts.get('DEVICE', 0):,}")
    print(f"  • IPs          : {node_type_counts.get('IP', 0):,}")
    print(f"  • Cards        : {node_type_counts.get('CARD', 0):,}")
    print(f"  • Merchants    : {node_type_counts.get('MERCHANT', 0):,}")
    print(f"  • Transactions : {node_type_counts.get('TRANSACTION', 0):,}")

    print(f"\nInfrastructure Clusters Extracted: {len(candidate_clusters)}")
    print(f"  • Suspicious Fraud Rings Detected (Risk Score >= {RISK_THRESHOLD}): {len(suspicious_rings)}")
    print(f"  • Benign Shared Infrastructure Filtered (Risk Score < {RISK_THRESHOLD}): {len(benign_shared_clusters)}")

    print("\n" + "-" * 60)
    print("TOP SUSPICIOUS FRAUD CLUSTERS DETECTED")
    print("-" * 60)

    for ring in suspicious_rings:
        print(f"\n{ring['cluster_id']} | Risk Score: {ring['risk_score']} / 100 | Likely Pattern: {ring['likely_pattern']}")
        print(f"  Users: {ring['users_count']} | Devices: {ring['devices_count']} | IPs: {ring['ips_count']} | Cards: {ring['cards_count']} | Txns: {ring['transactions_count']} | Merchants: {ring['merchants_count']}")
        print("  Evidence:")
        for ev in ring['evidence']:
            print(f"    - {ev}")

    print("\n" + "-" * 60)
    print("EVALUATION AGAINST GROUND TRUTH (POST-DETECTION VALIDATION)")
    print("-" * 60)
    print(f"Total Coordinated Fraud Transactions in Dataset: {total_coordinated_gt}")
    print(f"Coordinated Fraud Transactions Detected by Graph: {total_coordinated_detected}")
    print(f"Overall Coordinated Fraud Detection Rate        : {overall_detection_rate:.2f}%\n")

    print("Scenario Detection Rate Breakdown:")
    for sc in ["DEVICE_FARM", "CARD_CYCLING", "ACCOUNT_BURST", "DISTRIBUTED_ABUSE"]:
        total_sc = gt_scenario_counts.get(sc, 0)
        det_sc = detected_counts_by_scenario.get(sc, 0)
        rate_sc = (det_sc / max(1, total_sc)) * 100
        print(f"  • {sc:20s}: {det_sc:3d} / {total_sc:3d} detected ({rate_sc:6.2f}%)")

    print(f"\nFalse Positives (Legitimate transactions flagged in rings): {false_positives_legit}")
    print("=" * 60)


if __name__ == "__main__":
    main()
