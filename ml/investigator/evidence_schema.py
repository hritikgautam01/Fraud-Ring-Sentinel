"""
Sentinel — Coordinated Payment Abuse Intelligence
Module: Evidence Schema (evidence_schema.py)

Purpose:
Defines the formal Data Contract for Investigation Cases passed from the deterministic
Sentinel detection pipeline to the product layer and future LLM Investigator.

Design Guidelines:
------------------
1. Represents FACTS produced by upstream deterministic systems (NO AI-generated conclusions).
2. GRAPH CONNECTION != FRAUD: Uses neutral evidence terminology for shared infrastructure.
3. Traceable Evidence Items: Every evidence item includes an explicit `source` mapping.
4. Clean Separation: Separates DECISION (score/action) from RAW EVIDENCE (ML/Graph/Behav/Benign).
5. No Duplicated IDs or Manufactured Fields.
6. 100% Standard JSON Serializable.
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional


@dataclass
class EvidenceItem:
    """
    Single traceable evidence item representing an observable fact with upstream source mapping.
    """
    category: str        # "ML" | "GRAPH" | "BEHAVIORAL" | "BENIGN"
    signal: str          # e.g. "shared_ip_density", "ml_anomaly_probability", "merchant_target_concentration"
    value: Any           # Measurable numeric or string value (e.g. 7.2, 0.94, "M_TARGET_99")
    severity: str        # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
    description: str     # Human-readable factual description
    source: str          # "random_forest_baseline" | "graph_cluster_analyzer" | "behavioral_analyzer" | "fusion_risk_engine"


@dataclass
class Decision:
    """
    Deterministic decision outcome produced by Fusion Risk Engine.
    """
    risk_score: float             # Combined risk score (0.0 to 1.0)
    risk_level: str               # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
    action: str                   # "ALLOW" | "MONITOR" | "INVESTIGATE"
    threshold_applied: float      # e.g. 0.45


@dataclass
class TransactionSummary:
    """
    Basic observable context of the target transaction being investigated.
    """
    target_transaction_id: str
    target_user_id: str
    amount: float
    timestamp: Optional[str]
    total_transactions_in_cluster: int
    connected_users_count: int
    connected_devices_count: int
    connected_ips_count: int
    connected_cards_count: int
    connected_merchants_count: int


@dataclass
class MLEvidence:
    """
    Single-transaction ML model prediction facts.
    """
    ml_model_name: str
    predicted_probability: float
    high_risk_flag: bool


@dataclass
class GraphEvidence:
    """
    Graph topology and infrastructure sharing facts.
    """
    users_count: int
    devices_count: int
    ips_count: int
    cards_count: int
    merchants_count: int
    user_to_device_ratio: float
    user_to_card_ratio: float
    user_to_ip_ratio: float
    merchant_concentration: float
    top_merchant_id: str
    is_shared_infrastructure: bool


@dataclass
class BehavioralEvidence:
    """
    Single-transaction observable behavioral metrics.
    """
    account_age_days: int
    transactions_last_hour: int
    transactions_last_day: int
    failed_transactions: int


@dataclass
class BenignEvidence:
    """
    Observable evidence of legitimate network connectivity (GRAPH CONNECTION != FRAUD).
    """
    is_benign_pattern_detected: bool
    legitimate_users_on_shared_infrastructure: int
    benign_signals: List[str]


@dataclass
class InvestigationCase:
    """
    Root Data Contract container for an Investigation Case.
    """
    case_id: str
    timestamp: Optional[str]
    decision: Decision
    transaction_summary: TransactionSummary
    ml_evidence: MLEvidence
    graph_evidence: GraphEvidence
    behavioral_evidence: BehavioralEvidence
    benign_evidence: BenignEvidence
    evidence_items: List[EvidenceItem]

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts dataclass to a standard Python dict for clean JSON serialization.
        """
        return asdict(self)
