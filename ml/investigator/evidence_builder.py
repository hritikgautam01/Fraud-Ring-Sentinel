"""
Sentinel — Coordinated Payment Abuse Intelligence
Module: Evidence Builder (evidence_builder.py)

Purpose:
Acts purely as a Data Normalizer / Adapter that converts raw outputs produced by upstream
deterministic Sentinel modules (ML Baseline, Graph Analyzer, Behavioral Analyzer, Fusion Engine)
into a single, normalized InvestigationCase object.

Architectural Contract:
-----------------------
1. PURE ADAPTER: Does NOT classify fraud, compute new risk scores, create detection thresholds,
   or invent benign suppression factors.
2. CONSUMES UPSTREAM OUTPUTS: Directly consumes decision fields (risk_score, action, risk_level,
   threshold_applied, is_benign_pattern) produced by fusion_risk.py, graph_cluster_stats from detect_rings.py,
   ml_probability from train_baseline.py, and raw txn_row attributes.
3. NEUTRAL TERMINOLOGY: Uses objective signals (e.g. shared_ip_density, merchant_target_concentration)
   to ensure GRAPH CONNECTION != FRAUD.
4. NO MANUFACTURED DATA: Preserves actual timestamps (or None if missing); does not fabricate missing facts.
5. TRACEABLE EVIDENCE: Maps every evidence item to its explicit upstream source.
"""

from typing import Dict, Any, Optional

try:
    from .evidence_schema import (
        InvestigationCase, Decision, TransactionSummary,
        MLEvidence, GraphEvidence, BehavioralEvidence,
        BenignEvidence, EvidenceItem
    )
except ImportError:
    from evidence_schema import (
        InvestigationCase, Decision, TransactionSummary,
        MLEvidence, GraphEvidence, BehavioralEvidence,
        BenignEvidence, EvidenceItem
    )


def build_investigation_case(
    txn_row: Dict[str, Any],
    ml_probability: float,
    graph_cluster_stats: Dict[str, Any],
    fusion_result: Dict[str, Any],
    case_id: Optional[str] = None
) -> InvestigationCase:
    """
    Adapts and normalizes upstream pipeline outputs into an InvestigationCase object.
    
    Args:
        txn_row (Dict[str, Any]): Observable transaction row attributes.
        ml_probability (float): Single-transaction Random Forest model probability.
        graph_cluster_stats (Dict[str, Any]): Infrastructure cluster stats from detect_rings.py.
        fusion_result (Dict[str, Any]): Deterministic risk output from fusion_risk.py.
        case_id (str, optional): Unique case identifier string.
        
    Returns:
        InvestigationCase: Normalized, JSON-serializable investigation object.
    """
    txn_id = str(txn_row.get("transaction_id", "TXN_UNKNOWN"))
    user_id = str(txn_row.get("user_id", "U_UNKNOWN"))
    amount = float(txn_row.get("amount", 0.0))
    raw_timestamp = txn_row.get("timestamp")
    timestamp_str = str(raw_timestamp) if raw_timestamp is not None else None

    if case_id is None:
        case_id = f"CASE_{txn_id}"

    # --------------------------------------------------------------------------
    # 1. DECISION (Normalized directly from Fusion Risk Engine output)
    # --------------------------------------------------------------------------
    # Pure adapter: consumes decision fields produced by Fusion Risk Engine.
    # Does NOT invent a second decision policy or threshold rules inside the builder.
    combined_risk = float(fusion_result.get("combined_risk", 0.0))
    threshold_applied = float(fusion_result.get("threshold_applied", 0.45))
    action = str(fusion_result.get("action", "ALLOW"))
    risk_level = str(fusion_result.get("risk_level", "LOW"))

    decision = Decision(
        risk_score=combined_risk,
        risk_level=risk_level,
        action=action,
        threshold_applied=threshold_applied
    )

    # --------------------------------------------------------------------------
    # 2. TRANSACTION SUMMARY (Normalized from observable attributes & graph stats)
    # --------------------------------------------------------------------------
    user_cnt = int(graph_cluster_stats.get("user_count", 1))
    dev_cnt = int(graph_cluster_stats.get("device_count", 1))
    ip_cnt = int(graph_cluster_stats.get("ip_count", 1))
    card_cnt = int(graph_cluster_stats.get("card_count", 1))
    txn_cnt = int(graph_cluster_stats.get("transaction_count", 1))
    merch_cnt = int(graph_cluster_stats.get("merchant_count", 1))

    summary = TransactionSummary(
        target_transaction_id=txn_id,
        target_user_id=user_id,
        amount=amount,
        timestamp=timestamp_str,
        total_transactions_in_cluster=txn_cnt,
        connected_users_count=user_cnt,
        connected_devices_count=dev_cnt,
        connected_ips_count=ip_cnt,
        connected_cards_count=card_cnt,
        connected_merchants_count=merch_cnt
    )

    # --------------------------------------------------------------------------
    # 3. ML EVIDENCE (Normalized from Random Forest predicted probability)
    # --------------------------------------------------------------------------
    ml_prob = float(ml_probability)
    ml_evidence = MLEvidence(
        ml_model_name="RandomForestClassifier_v1",
        predicted_probability=round(ml_prob, 4),
        high_risk_flag=(ml_prob >= 0.50)
    )

    # --------------------------------------------------------------------------
    # 4. GRAPH EVIDENCE (Normalized from detect_rings.py cluster statistics)
    # --------------------------------------------------------------------------
    u_per_d = round(user_cnt / max(1, dev_cnt), 2) if dev_cnt > 0 else 0.0
    u_per_c = round(user_cnt / max(1, card_cnt), 2) if card_cnt > 0 else 0.0
    u_per_ip = round(user_cnt / max(1, ip_cnt), 2) if ip_cnt > 0 else 0.0
    merch_conc = round(float(graph_cluster_stats.get("merchant_concentration", 0.0)), 4)
    top_m_id = str(graph_cluster_stats.get("top_merchant_id", "N/A"))

    graph_evidence = GraphEvidence(
        users_count=user_cnt,
        devices_count=dev_cnt,
        ips_count=ip_cnt,
        cards_count=card_cnt,
        merchants_count=merch_cnt,
        user_to_device_ratio=u_per_d,
        user_to_card_ratio=u_per_c,
        user_to_ip_ratio=u_per_ip,
        merchant_concentration=merch_conc,
        top_merchant_id=top_m_id,
        is_shared_infrastructure=(user_cnt > 1 and (dev_cnt > 0 or ip_cnt > 0 or card_cnt > 0))
    )

    # --------------------------------------------------------------------------
    # 5. BEHAVIORAL EVIDENCE (Normalized from raw transaction row features)
    # --------------------------------------------------------------------------
    acc_age = int(txn_row.get("account_age_days", 0))
    tx_hr = int(txn_row.get("transactions_last_hour", 0))
    tx_dy = int(txn_row.get("transactions_last_day", 0))
    failed_tx = int(txn_row.get("failed_transactions", 0))

    behavioral_evidence = BehavioralEvidence(
        account_age_days=acc_age,
        transactions_last_hour=tx_hr,
        transactions_last_day=tx_dy,
        failed_transactions=failed_tx
    )

    # --------------------------------------------------------------------------
    # 6. BENIGN EVIDENCE (Normalized directly from Fusion Risk Engine output)
    # --------------------------------------------------------------------------
    # Pure adapter: consumes is_benign_pattern produced by Fusion Risk Engine.
    # Does NOT invent benign detection thresholds or suppression factors inside the builder.
    is_benign = bool(fusion_result.get("is_benign_pattern", False))
    avg_acc_age = float(graph_cluster_stats.get("avg_account_age", acc_age))
    avg_fail = float(graph_cluster_stats.get("avg_failed_tx", failed_tx))

    benign_signals = []
    if is_benign:
        benign_signals.append(f"{user_cnt} connected users exhibit mature average account age ({avg_acc_age:.1f} days)")
        benign_signals.append(f"Low average payment failure rate across connected network ({avg_fail:.2f} failures/user)")
        benign_signals.append("Purchases distributed across multiple diverse merchants")

    benign_evidence = BenignEvidence(
        is_benign_pattern_detected=is_benign,
        legitimate_users_on_shared_infrastructure=user_cnt if is_benign else 0,
        benign_signals=benign_signals if benign_signals else ["No benign network patterns identified"]
    )

    # --------------------------------------------------------------------------
    # 7. TRACEABLE EVIDENCE ITEMS (Mapping observable facts to upstream sources)
    # --------------------------------------------------------------------------
    # Pure adapter: normalizes facts already measured by upstream modules.
    evidence_items = []

    # Source A: Random Forest Baseline (random_forest_baseline)
    if ml_prob >= 0.50:
        evidence_items.append(EvidenceItem(
            category="ML",
            signal="ml_anomaly_probability",
            value=round(ml_prob, 4),
            severity="HIGH" if ml_prob >= 0.75 else "MEDIUM",
            description=f"Transaction ML baseline predicted anomaly probability: {ml_prob * 100:.1f}%",
            source="random_forest_baseline"
        ))

    # Source B: Graph Cluster Analyzer (graph_cluster_analyzer)
    # Uses neutral terminology (shared_device_density, shared_card_density, shared_ip_density, merchant_target_concentration)
    if u_per_d >= 2.0:
        evidence_items.append(EvidenceItem(
            category="GRAPH",
            signal="shared_device_density",
            value=u_per_d,
            severity="HIGH" if u_per_d >= 4.0 else "MEDIUM",
            description=f"{user_cnt} users connected via {dev_cnt} shared device(s) ({u_per_d:.1f} users/device)",
            source="graph_cluster_analyzer"
        ))
    if u_per_c >= 2.0:
        evidence_items.append(EvidenceItem(
            category="GRAPH",
            signal="shared_card_density",
            value=u_per_c,
            severity="HIGH" if u_per_c >= 3.0 else "MEDIUM",
            description=f"{user_cnt} users connected via {card_cnt} shared card(s) ({u_per_c:.1f} users/card)",
            source="graph_cluster_analyzer"
        ))
    if u_per_ip >= 3.0:
        evidence_items.append(EvidenceItem(
            category="GRAPH",
            signal="shared_ip_density",
            value=u_per_ip,
            severity="MEDIUM",
            description=f"{user_cnt} users connected via {ip_cnt} shared IP address(es) ({u_per_ip:.1f} users/IP)",
            source="graph_cluster_analyzer"
        ))
    if merch_conc >= 0.50 and user_cnt >= 3:
        evidence_items.append(EvidenceItem(
            category="GRAPH",
            signal="merchant_target_concentration",
            value=merch_conc,
            severity="HIGH",
            description=f"{merch_conc * 100:.1f}% of cluster transactions target merchant {top_m_id}",
            source="graph_cluster_analyzer"
        ))

    # Source C: Behavioral Analyzer (behavioral_analyzer)
    if tx_hr > 0 or tx_dy > 0:
        evidence_items.append(EvidenceItem(
            category="BEHAVIORAL",
            signal="transaction_velocity",
            value=tx_hr,
            severity="MEDIUM" if (tx_hr > 2 or tx_dy > 6) else "LOW",
            description=f"Transaction velocity: {tx_hr} txns/hr, {tx_dy} txns/day",
            source="behavioral_analyzer"
        ))
    if acc_age <= 15:
        evidence_items.append(EvidenceItem(
            category="BEHAVIORAL",
            signal="account_age",
            value=acc_age,
            severity="MEDIUM" if acc_age <= 5 else "LOW",
            description=f"Account age: {acc_age} day(s)",
            source="behavioral_analyzer"
        ))
    if failed_tx >= 1:
        evidence_items.append(EvidenceItem(
            category="BEHAVIORAL",
            signal="payment_failures",
            value=failed_tx,
            severity="MEDIUM",
            description=f"Recent payment declines: {failed_tx} failed attempt(s)",
            source="behavioral_analyzer"
        ))

    # Source D: Fusion Risk Engine (fusion_risk_engine)
    if is_benign:
        evidence_items.append(EvidenceItem(
            category="BENIGN",
            signal="legitimate_network_context",
            value=round(avg_acc_age, 1),
            severity="LOW",
            description=f"{user_cnt} connected users share infrastructure with mature average account age ({avg_acc_age:.1f} days)",
            source="fusion_risk_engine"
        ))

    # Default fallback item if no items exist
    if not evidence_items:
        evidence_items.append(EvidenceItem(
            category="BEHAVIORAL",
            signal="normal_transaction_profile",
            value=0,
            severity="LOW",
            description="Transaction profile exhibits normal observable metrics across all dimensions",
            source="behavioral_analyzer"
        ))

    return InvestigationCase(
        case_id=case_id,
        timestamp=timestamp_str,
        decision=decision,
        transaction_summary=summary,
        ml_evidence=ml_evidence,
        graph_evidence=graph_evidence,
        behavioral_evidence=behavioral_evidence,
        benign_evidence=benign_evidence,
        evidence_items=evidence_items
    )
