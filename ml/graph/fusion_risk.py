"""
Sentinel — Coordinated Payment Abuse Intelligence
Module: Fusion Risk Engine (fusion_risk.py)

Purpose:
Combines single-transaction Machine Learning probabilities (Random Forest) with
graph structural topology signals and observable behavioral metrics into an explainable,
multi-dimensional fusion risk score (0.0 to 1.0).

Core Design Philosophy:
----------------------
GRAPH CONNECTION != FRAUD.

Real-world payment networks contain many legitimate relationships (families, corporate Wi-Fi,
popular merchants). Shared infrastructure alone is treated as a WEAK signal unless supported
by multiple independent pieces of evidence:
1. ML Signal (40% Weight): Single-transaction RF model anomaly probability.
2. Graph Structural Risk (35% Weight): Infrastructure concentration (Device, Card, IP) and Merchant targeting.
3. Behavioral Risk (25% Weight): Velocity spikes, account age anomalies, and payment failure rates.

Benign Network Suppressor:
If connected infrastructure exhibits mature account ages, low velocity, low decline rates,
and diverse merchant targeting, a Benign Suppressor factor actively reduces graph risk to
prevent false positives on legitimate shared infrastructure.

De-duplication / Anti-Double-Counting:
To prevent double counting correlated features (e.g. users_per_ip vs ip_sharing_ratio),
signals are normalized into unified density dimensions before weighting.
"""

import math
from typing import Dict, Any, List, Tuple


# ==============================================================================
# TRANSPARENT FUSION WEIGHTS & THRESHOLDS (Configurable)
# ==============================================================================
WEIGHT_ML = 0.40           # Random Forest transaction model probability
WEIGHT_GRAPH = 0.35        # Graph structural infrastructure & merchant concentration
WEIGHT_BEHAVIORAL = 0.25   # Behavioral velocity, account age, and decline rate

FUSION_RISK_THRESHOLD = 0.45  # Combined risk score >= 0.45 triggers Investigation Alert


def compute_fusion_risk(
    txn_row: Dict[str, Any],
    ml_probability: float,
    graph_cluster_stats: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Computes a multi-signal fusion risk score for a single transaction.
    
    Args:
        txn_row (Dict[str, Any]): Transaction feature dictionary.
        ml_probability (float): Predicted probability from Random Forest (0.0 to 1.0).
        graph_cluster_stats (Dict[str, Any]): Infrastructure cluster stats from detect_rings.py.
        
    Returns:
        Dict[str, Any]: Multi-signal fusion risk result dictionary with evidence strings.
    """
    evidence = []

    # --------------------------------------------------------------------------
    # 1. ML SIGNAL (40% Weight)
    # --------------------------------------------------------------------------
    ml_risk = float(ml_probability)
    if ml_risk >= 0.50:
        evidence.append(f"Transaction ML model anomaly score: {ml_risk * 100:.1f}%")

    # --------------------------------------------------------------------------
    # 2. GRAPH STRUCTURAL RISK (35% Weight)
    # --------------------------------------------------------------------------
    user_count = graph_cluster_stats.get("user_count", 1)
    device_count = graph_cluster_stats.get("device_count", 1)
    ip_count = graph_cluster_stats.get("ip_count", 1)
    card_count = graph_cluster_stats.get("card_count", 1)
    merchant_concentration = graph_cluster_stats.get("merchant_concentration", 0.0)
    top_merchant_id = graph_cluster_stats.get("top_merchant_id", "N/A")

    # De-duplicated Density Dimensions (scaled 0.0 to 1.0)
    # Device Density: ratio of users to devices
    u_per_d = user_count / max(1, device_count)
    device_density = min(1.0, (u_per_d - 1) / 5.0) if u_per_d >= 2 and device_count > 0 else 0.0

    # Card Pooling: ratio of users to cards
    u_per_c = user_count / max(1, card_count)
    card_pooling = min(1.0, (u_per_c - 1) / 3.0) if u_per_c >= 2 and card_count > 0 else 0.0

    # IP Proxy Density: ratio of users to IPs
    u_per_ip = user_count / max(1, ip_count)
    ip_density = min(1.0, (u_per_ip - 1) / 5.0) if u_per_ip >= 3 and ip_count > 0 else 0.0

    # Merchant Concentration (e.g. Distributed Abuse targeting single merchant)
    merchant_target_risk = merchant_concentration if (merchant_concentration >= 0.50 and user_count >= 3) else 0.0

    # Combine sub-structural signals without double-counting
    raw_graph_risk = max(device_density, card_pooling, ip_density) * 0.60 + merchant_target_risk * 0.40

    # Collect structural evidence
    if device_density > 0:
        evidence.append(f"{user_count} users share {device_count} device(s) ({u_per_d:.1f} users/device)")
    if card_pooling > 0:
        evidence.append(f"{user_count} users share {card_count} card(s) ({u_per_c:.1f} users/card)")
    if ip_density > 0:
        evidence.append(f"{user_count} users share {ip_count} IP address(es) ({u_per_ip:.1f} users/IP)")
    if merchant_target_risk > 0:
        evidence.append(f"{merchant_concentration * 100:.1f}% of cluster transactions target merchant {top_merchant_id}")

    # --------------------------------------------------------------------------
    # BENIGN NETWORK SUPPRESSOR (GRAPH CONNECTION != FRAUD)
    # --------------------------------------------------------------------------
    # If the connected cluster shows mature accounts, low velocity, low failure rates,
    # and diverse merchants, suppress graph risk to prevent flagging benign office/family networks.
    avg_account_age = graph_cluster_stats.get("avg_account_age", 100.0)
    avg_failed_tx = graph_cluster_stats.get("avg_failed_tx", 0.0)
    avg_tx_hour = graph_cluster_stats.get("avg_tx_hour", 0.0)

    is_benign_pattern = (
        avg_account_age >= 30.0 and 
        avg_failed_tx <= 0.5 and 
        avg_tx_hour <= 2.0 and 
        merchant_concentration < 0.30
    )

    if is_benign_pattern:
        suppressor_factor = 0.25  # Reduce graph risk by 75% for benign networks
        graph_risk = raw_graph_risk * suppressor_factor
    else:
        graph_risk = raw_graph_risk

    # --------------------------------------------------------------------------
    # 3. BEHAVIORAL RISK (25% Weight)
    # --------------------------------------------------------------------------
    txn_amount = float(txn_row.get("amount", 0.0))
    tx_hour = float(txn_row.get("transactions_last_hour", 0))
    tx_day = float(txn_row.get("transactions_last_day", 0))
    failed_tx = float(txn_row.get("failed_transactions", 0))
    acc_age = float(txn_row.get("account_age_days", 100))

    # Velocity risk
    velocity_risk = min(1.0, (tx_hour / 8.0) * 0.6 + (tx_day / 20.0) * 0.4) if (tx_hour > 2 or tx_day > 6) else 0.0

    # New account risk
    account_age_risk = 1.0 if acc_age <= 5 else (0.5 if acc_age <= 15 else 0.0)

    # Decline rate risk
    decline_risk = min(1.0, failed_tx / 4.0) if failed_tx >= 1 else 0.0

    behavioral_risk = velocity_risk * 0.40 + account_age_risk * 0.35 + decline_risk * 0.25

    if velocity_risk > 0:
        evidence.append(f"Elevated velocity: {int(tx_hour)} txns/hr, {int(tx_day)} txns/day")
    if account_age_risk > 0:
        evidence.append(f"New account age: {int(acc_age)} days")
    if decline_risk > 0:
        evidence.append(f"Recent payment failures: {int(failed_tx)} failed attempt(s)")

    # --------------------------------------------------------------------------
    # 4. COMBINED FUSION RISK SCORE
    # --------------------------------------------------------------------------
    combined_risk = round(
        WEIGHT_ML * ml_risk +
        WEIGHT_GRAPH * graph_risk +
        WEIGHT_BEHAVIORAL * behavioral_risk,
        4
    )

    is_flagged_fraud = combined_risk >= FUSION_RISK_THRESHOLD

    # Determine deterministic action and risk_level
    if is_flagged_fraud:
        action = "INVESTIGATE"
    elif combined_risk >= 0.25:
        action = "MONITOR"
    else:
        action = "ALLOW"

    if combined_risk >= 0.75:
        risk_level = "CRITICAL"
    elif combined_risk >= 0.45:
        risk_level = "HIGH"
    elif combined_risk >= 0.25:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "transaction_id": str(txn_row.get("transaction_id")),
        "user_id": str(txn_row.get("user_id")),
        "ml_probability": round(ml_risk, 4),
        "graph_structural_risk": round(graph_risk, 4),
        "behavioral_risk": round(behavioral_risk, 4),
        "combined_risk": combined_risk,
        "is_flagged_fraud": is_flagged_fraud,
        "threshold_applied": FUSION_RISK_THRESHOLD,
        "is_benign_pattern": is_benign_pattern,
        "action": action,
        "risk_level": risk_level,
        "evidence": evidence if evidence else ["Normal transaction profile across all dimensions"]
    }
