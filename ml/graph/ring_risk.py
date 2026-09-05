"""
Sentinel — Coordinated Payment Abuse Intelligence
Module: Ring Risk Evaluator (ring_risk.py)

Purpose:
Calculates a transparent, deterministic ring risk score (0 to 100) and generates
evidence explanations for candidate infrastructure clusters based on graph topology
and transaction behavior metrics.

Scoring Weights:
Configurable parameters at the top of the file determine the weight of each risk dimension.
"""

from typing import Dict, Any, List

# ==============================================================================
# CONFIGURABLE RISK SCORING WEIGHTS (Must sum to 1.0)
# ==============================================================================
DEFAULT_WEIGHTS = {
    "device_sharing_weight": 0.20,     # High user-to-device ratio (Device Farm indicator)
    "card_sharing_weight": 0.20,       # High user-to-card ratio (Card Cycling indicator)
    "ip_sharing_weight": 0.15,         # High user-to-IP proxy ratio (Distributed Abuse indicator)
    "merchant_target_weight": 0.15,    # High concentration targeting a single merchant (Distributed Abuse indicator)
    "velocity_weight": 0.15,           # High hourly & daily transaction velocity
    "new_account_weight": 0.10,        # High concentration of newly created accounts (Account Burst indicator)
    "failed_txn_weight": 0.05,         # High rate of payment failures / card testing
}

# Minimum risk score threshold (0 - 100) to classify a cluster as a Suspicious Fraud Ring
RISK_THRESHOLD = 35.0


def calculate_ring_risk(cluster: Dict[str, Any], weights: Dict[str, float] = None) -> Dict[str, Any]:
    """
    Computes a deterministic ring risk score (0-100), generates evidence strings,
    and infers the likely fraud pattern.
    
    Args:
        cluster (Dict[str, Any]): Candidate cluster statistics dictionary.
        weights (Dict[str, float], optional): Custom scoring weights.
        
    Returns:
        Dict[str, Any]: Evaluated ring result dictionary.
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS

    user_count = cluster["user_count"]
    device_count = cluster["device_count"]
    ip_count = cluster["ip_count"]
    card_count = cluster["card_count"]
    txn_count = cluster["transaction_count"]
    
    avg_tx_hour = cluster["avg_tx_hour"]
    avg_tx_day = cluster["avg_tx_day"]
    avg_failed_tx = cluster["avg_failed_tx"]
    new_account_ratio = cluster["new_account_ratio"]
    merchant_concentration = cluster["merchant_concentration"]
    top_merchant_id = cluster["top_merchant_id"]

    evidence = []

    # --------------------------------------------------------------------------
    # 1. Device Sharing Sub-score (0.0 to 1.0)
    # --------------------------------------------------------------------------
    u_per_d = user_count / max(1, device_count) if device_count > 0 else 0
    if u_per_d >= 3 and device_count > 0:
        device_sharing_score = min(1.0, (u_per_d - 1) / 5.0)
        evidence.append(f"{user_count} users share {device_count} device(s) ({u_per_d:.1f} users/device)")
    else:
        device_sharing_score = 0.0

    # --------------------------------------------------------------------------
    # 2. Card Sharing Sub-score (0.0 to 1.0)
    # --------------------------------------------------------------------------
    u_per_c = user_count / max(1, card_count) if card_count > 0 else 0
    if u_per_c >= 2 and card_count > 0:
        card_sharing_score = min(1.0, (u_per_c - 1) / 3.0)
        evidence.append(f"{user_count} users share {card_count} card(s) ({u_per_c:.1f} users/card)")
    else:
        card_sharing_score = 0.0

    # --------------------------------------------------------------------------
    # 3. IP Sharing Sub-score (0.0 to 1.0)
    # --------------------------------------------------------------------------
    u_per_ip = user_count / max(1, ip_count) if ip_count > 0 else 0
    if u_per_ip >= 3 and ip_count > 0:
        ip_sharing_score = min(1.0, (u_per_ip - 1) / 5.0)
        evidence.append(f"{user_count} users share {ip_count} IP proxy/proxies ({u_per_ip:.1f} users/IP)")
    else:
        ip_sharing_score = 0.0

    # --------------------------------------------------------------------------
    # 4. Merchant Target Sub-score (0.0 to 1.0)
    # --------------------------------------------------------------------------
    if merchant_concentration >= 0.6 and user_count >= 3:
        merchant_target_score = merchant_concentration
        evidence.append(f"{merchant_concentration * 100:.1f}% of transactions concentrated on target merchant {top_merchant_id}")
    else:
        merchant_target_score = 0.0

    # --------------------------------------------------------------------------
    # 5. Transaction Velocity Sub-score (0.0 to 1.0)
    # --------------------------------------------------------------------------
    if avg_tx_hour > 3.0 or avg_tx_day > 10.0:
        velocity_score = min(1.0, (avg_tx_hour / 10.0) * 0.6 + (avg_tx_day / 25.0) * 0.4)
        evidence.append(f"high transaction velocity (avg {avg_tx_hour:.1f} txns/hr, {avg_tx_day:.1f} txns/day)")
    else:
        velocity_score = 0.0

    # --------------------------------------------------------------------------
    # 6. New Account Sub-score (0.0 to 1.0)
    # --------------------------------------------------------------------------
    if new_account_ratio > 0.3:
        new_account_score = new_account_ratio
        evidence.append(f"{new_account_ratio * 100:.1f}% of accounts are newly created (age <= 5 days)")
    else:
        new_account_score = 0.0

    # --------------------------------------------------------------------------
    # 7. Failed Transactions Sub-score (0.0 to 1.0)
    # --------------------------------------------------------------------------
    if avg_failed_tx >= 1.5:
        failed_txn_score = min(1.0, avg_failed_tx / 4.0)
        evidence.append(f"high payment failure rate (avg {avg_failed_tx:.1f} failed txns/user)")
    else:
        failed_txn_score = 0.0

    # --------------------------------------------------------------------------
    # Combine Sub-scores into Final Ring Risk Score (0 to 100)
    # --------------------------------------------------------------------------
    total_score = (
        device_sharing_score * weights["device_sharing_weight"] +
        card_sharing_score * weights["card_sharing_weight"] +
        ip_sharing_score * weights["ip_sharing_weight"] +
        merchant_target_score * weights["merchant_target_weight"] +
        velocity_score * weights["velocity_weight"] +
        new_account_score * weights["new_account_weight"] +
        failed_txn_score * weights["failed_txn_weight"]
    )
    
    # Scale to 0-100 range
    ring_risk_score = round(min(100.0, total_score * 100), 1)

    # --------------------------------------------------------------------------
    # Infer Likely Fraud Pattern
    # --------------------------------------------------------------------------
    if ring_risk_score < RISK_THRESHOLD:
        likely_pattern = "BENIGN_SHARED_INFRASTRUCTURE"
        if not evidence:
            evidence.append("Normal transaction behavior across shared network infrastructure")
    elif device_sharing_score >= 0.6 and u_per_d >= 4:
        likely_pattern = "DEVICE_FARM"
    elif card_sharing_score >= 0.5 and u_per_c >= 2:
        likely_pattern = "CARD_CYCLING"
    elif merchant_target_score >= 0.6 and ip_sharing_score >= 0.5:
        likely_pattern = "DISTRIBUTED_ABUSE"
    elif new_account_score >= 0.6 and velocity_score >= 0.5:
        likely_pattern = "ACCOUNT_BURST"
    else:
        likely_pattern = "GENERAL_SUSPICIOUS_RING"

    # Strip node type prefixes for clean output presentation
    clean_users = [u.replace("USER:", "") for u in cluster["users"]]
    clean_devices = [d.replace("DEVICE:", "") for d in cluster["devices"]]
    clean_ips = [ip.replace("IP:", "") for ip in cluster["ips"]]
    clean_cards = [c.replace("CARD:", "") for c in cluster["cards"]]
    clean_txns = [t.replace("TRANSACTION:", "") for t in cluster["transaction_nodes"]]
    clean_merchants = [m.replace("MERCHANT:", "") for m in cluster["merchants"]]

    result = {
        "candidate_id": cluster["candidate_id"],
        "risk_score": ring_risk_score,
        "is_suspicious_ring": ring_risk_score >= RISK_THRESHOLD,
        "likely_pattern": likely_pattern,
        "users_count": user_count,
        "devices_count": device_count,
        "ips_count": ip_count,
        "cards_count": card_count,
        "transactions_count": txn_count,
        "merchants_count": len(clean_merchants),
        "evidence": evidence,
        "details": {
            "users": clean_users,
            "devices": clean_devices,
            "ips": clean_ips,
            "cards": clean_cards,
            "transactions": clean_txns,
            "merchants": clean_merchants
        },
        "ground_truth_scenarios": cluster["ground_truth_scenarios"]
    }

    return result
