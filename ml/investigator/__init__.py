"""
Sentinel — Coordinated Payment Abuse Intelligence
Package: ml.investigator

Product Layer Data Contract: Structured Evidence, Investigation Case Generator, & LLM Investigator
"""

from .evidence_schema import (
    InvestigationCase,
    Decision,
    TransactionSummary,
    MLEvidence,
    GraphEvidence,
    BehavioralEvidence,
    BenignEvidence,
    EvidenceItem
)
from .evidence_builder import build_investigation_case
from .validate_evidence import validate_investigation_case
from .report_schema import (
    InvestigationReport,
    RiskAssessment,
    SupportingEvidence
)
from .validate_report import validate_investigation_report
from .llm_investigator import (
    LLMInvestigator,
    LLMInvestigatorError,
    LLMProvider,
    MockLLMProvider,
    GeminiProvider,
    OpenAIProvider,
    AutoLLMProvider
)

__all__ = [
    "InvestigationCase",
    "Decision",
    "TransactionSummary",
    "MLEvidence",
    "GraphEvidence",
    "BehavioralEvidence",
    "BenignEvidence",
    "EvidenceItem",
    "build_investigation_case",
    "validate_investigation_case",
    "InvestigationReport",
    "RiskAssessment",
    "SupportingEvidence",
    "validate_investigation_report",
    "LLMInvestigator",
    "LLMInvestigatorError",
    "LLMProvider",
    "MockLLMProvider",
    "GeminiProvider",
    "OpenAIProvider",
    "AutoLLMProvider"
]
