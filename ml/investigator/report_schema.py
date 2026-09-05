"""
Sentinel — Coordinated Payment Abuse Intelligence
Module: Report Schema (report_schema.py)

Purpose:
Defines the formal Data Contract for Investigation Reports produced by the LLM Investigator.

Design Guidelines:
------------------
1. Structured Data Contract for machine-readable JSON output.
2. Authoritative Risk Assessment: Preserves exact deterministic decision fields produced by Fusion Risk Engine.
3. Factual Traceability: Explains ML, Graph, Behavioral, and Benign evidence signals without inventing facts.
4. Neutral & Objective: Communicates uncertainty, limitations, and distinguishes connectivity from fraud.
5. 100% Standard JSON Serializable.
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional


@dataclass
class RiskAssessment:
    """
    Authoritative deterministic risk assessment outcome preserved directly from input InvestigationCase.
    """
    risk_score: float             # Combined risk score (0.0 to 1.0)
    risk_level: str               # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
    action: str                   # "ALLOW" | "MONITOR" | "INVESTIGATE"
    threshold_applied: float      # Deterministic decision threshold (e.g. 0.45)


@dataclass
class SupportingEvidence:
    """
    Factual summary of observable evidence grouped by pipeline layer.
    """
    ml_evidence: str              # Random forest model anomaly prediction facts
    graph_evidence: str           # Graph topology and shared infrastructure facts
    behavioral_evidence: str      # Velocity, account age, and decline rate facts


@dataclass
class InvestigationReport:
    """
    Root Data Contract container for an LLM-generated Investigation Report.
    """
    case_id: str
    investigation_summary: str
    risk_assessment: RiskAssessment
    why_flagged: List[str]
    supporting_evidence: SupportingEvidence
    benign_considerations: str
    analyst_recommendation: str
    limitations: str

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts dataclass to a standard Python dict for clean JSON serialization.
        """
        return asdict(self)
