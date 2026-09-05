"""
Sentinel — Coordinated Payment Abuse Intelligence
Module: LLM Investigator Test Suite (test_llm_investigator.py)

Purpose:
Comprehensive unit and scenario test suite verifying all 6 architectural requirements:
  Test 1: Normal high-risk case (preserves decision, case ID, risk level).
  Test 2: Benign connected network (acknowledges benign context, graph connection != fraud).
  Test 3: Graph-only suspicious connection (weak signals, graph alone insufficient).
  Test 4: Invalid decision manipulation (rejection of 'INVESTIGATE' -> 'BLOCK').
  Test 5: Fabricated evidence / ground-truth leakage rejection.
  Test 6: Provider failure safety (fails safely, preserving deterministic decision).
"""

import json
import os

try:
    from ml.investigator.evidence_schema import (
        InvestigationCase, Decision, TransactionSummary,
        MLEvidence, GraphEvidence, BehavioralEvidence,
        BenignEvidence, EvidenceItem
    )
    from ml.investigator.llm_investigator import (
        LLMInvestigator, LLMInvestigatorError, LLMProvider, MockLLMProvider
    )
    from ml.investigator.validate_report import validate_investigation_report
except ImportError:
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    from ml.investigator.evidence_schema import (
        InvestigationCase, Decision, TransactionSummary,
        MLEvidence, GraphEvidence, BehavioralEvidence,
        BenignEvidence, EvidenceItem
    )
    from ml.investigator.llm_investigator import (
        LLMInvestigator, LLMInvestigatorError, LLMProvider, MockLLMProvider
    )
    from ml.investigator.validate_report import validate_investigation_report


class BadActionLLMProvider(LLMProvider):
    """Mock provider that attempts to manipulate action from INVESTIGATE to BLOCK."""
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        return json.dumps({
            "case_id": "CASE_TXN_TEST_01",
            "investigation_summary": "Attempting decision override",
            "risk_assessment": {
                "risk_score": 0.85,
                "risk_level": "CRITICAL",
                "action": "BLOCK",  # FORBIDDEN!
                "threshold_applied": 0.45
            },
            "why_flagged": ["High risk"],
            "supporting_evidence": {
                "ml_evidence": "High ML score",
                "graph_evidence": "Shared devices",
                "behavioral_evidence": "High velocity"
            },
            "benign_considerations": "None",
            "analyst_recommendation": "Block immediately",
            "limitations": "None"
        })


class FabricatedLeakageLLMProvider(LLMProvider):
    """Mock provider that attempts to leak forbidden ground-truth labels."""
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        return json.dumps({
            "case_id": "CASE_TXN_TEST_01",
            "investigation_summary": "Attempting ground truth leakage",
            "risk_assessment": {
                "risk_score": 0.85,
                "risk_level": "CRITICAL",
                "action": "INVESTIGATE",
                "threshold_applied": 0.45
            },
            "why_flagged": ["High risk"],
            "supporting_evidence": {
                "ml_evidence": "High ML score",
                "graph_evidence": "Shared devices",
                "behavioral_evidence": "High velocity"
            },
            "benign_considerations": "None",
            "analyst_recommendation": "Review case",
            "limitations": "None",
            "is_fraud": 1  # FORBIDDEN GROUND TRUTH LEAKAGE!
        })


class FailingLLMProvider(LLMProvider):
    """Mock provider that simulates network failure or API exception."""
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        raise RuntimeError("Simulated API connection failure / timeout")


def create_sample_case(case_id="CASE_TXN_TEST_01", action="INVESTIGATE", score=0.85, is_benign=False, ml_prob=0.90):
    return InvestigationCase(
        case_id=case_id,
        timestamp="2026-09-05T12:00:00Z",
        decision=Decision(
            risk_score=score,
            risk_level="CRITICAL" if score >= 0.75 else ("HIGH" if score >= 0.45 else "LOW"),
            action=action,
            threshold_applied=0.45
        ),
        transaction_summary=TransactionSummary(
            target_transaction_id="TXN_TEST_01",
            target_user_id="U_TEST_01",
            amount=150.00,
            timestamp="2026-09-05T12:00:00Z",
            total_transactions_in_cluster=25,
            connected_users_count=10,
            connected_devices_count=2,
            connected_ips_count=3,
            connected_cards_count=5,
            connected_merchants_count=1
        ),
        ml_evidence=MLEvidence(
            ml_model_name="RandomForestClassifier_v1",
            predicted_probability=ml_prob,
            high_risk_flag=(ml_prob >= 0.50)
        ),
        graph_evidence=GraphEvidence(
            users_count=10,
            devices_count=2,
            ips_count=3,
            cards_count=5,
            merchants_count=1,
            user_to_device_ratio=5.0,
            user_to_card_ratio=2.0,
            user_to_ip_ratio=3.33,
            merchant_concentration=0.90,
            top_merchant_id="M_TEST_99",
            is_shared_infrastructure=True
        ),
        behavioral_evidence=BehavioralEvidence(
            account_age_days=10,
            transactions_last_hour=4,
            transactions_last_day=12,
            failed_transactions=1
        ),
        benign_evidence=BenignEvidence(
            is_benign_pattern_detected=is_benign,
            legitimate_users_on_shared_infrastructure=10 if is_benign else 0,
            benign_signals=[
                "10 connected users exhibit mature average account age (45.0 days)"
            ] if is_benign else ["No benign network patterns identified"]
        ),
        evidence_items=[
            EvidenceItem(
                category="ML",
                signal="ml_anomaly_probability",
                value=ml_prob,
                severity="HIGH",
                description=f"Transaction ML baseline predicted anomaly probability: {ml_prob*100:.1f}%",
                source="random_forest_baseline"
            ),
            EvidenceItem(
                category="GRAPH",
                signal="shared_device_density",
                value=5.0,
                severity="HIGH",
                description="10 users connected via 2 shared device(s) (5.0 users/device)",
                source="graph_cluster_analyzer"
            )
        ]
    )


def test_1_normal_high_risk_case():
    print("\n[Test 1] Normal High-Risk Case Report Generation...")
    case = create_sample_case(score=0.85, action="INVESTIGATE")
    investigator = LLMInvestigator(provider=MockLLMProvider())

    report = investigator.generate_report(case)
    report_dict = report.to_dict()

    assert report.case_id == case.case_id, "Case ID mismatch"
    assert report.risk_assessment.risk_score == 0.85, "Risk score mismatch"
    assert report.risk_assessment.risk_level == "CRITICAL", "Risk level mismatch"
    assert report.risk_assessment.action == "INVESTIGATE", "Action mismatch"
    assert len(report.why_flagged) > 0, "Missing why_flagged bullet points"

    is_valid, errs = validate_investigation_report(report_dict, expected_case=case.to_dict())
    assert is_valid, f"Validation failed: {errs}"
    print("  ✓ PASS: Report generated and preserved decision, case_id, and risk score perfectly.")


def test_2_benign_connected_network():
    print("\n[Test 2] Benign Connected Network Case...")
    case = create_sample_case(score=0.20, action="ALLOW", is_benign=True, ml_prob=0.15)
    investigator = LLMInvestigator(provider=MockLLMProvider())

    report = investigator.generate_report(case)

    assert report.risk_assessment.action == "ALLOW"
    assert "benign" in report.benign_considerations.lower() or "legitimate" in report.benign_considerations.lower()
    assert "not prove" in report.limitations.lower() or "insufficient" in report.limitations.lower()
    print("  ✓ PASS: Correctly acknowledged benign network pattern without treating graph connection as fraud.")


def test_3_graph_only_suspicious_connection():
    print("\n[Test 3] Graph-Only Suspicious Connection (Weak Behavioral/ML Signals)...")
    case = create_sample_case(score=0.35, action="MONITOR", is_benign=False, ml_prob=0.10)
    investigator = LLMInvestigator(provider=MockLLMProvider())

    report = investigator.generate_report(case)

    assert report.risk_assessment.action == "MONITOR"
    assert "does not prove" in report.limitations.lower() or "contextual" in report.limitations.lower()
    print("  ✓ PASS: Report explicitly noted that graph connectivity alone is contextual evidence.")


def test_4_invalid_decision_manipulation():
    print("\n[Test 4] Rejection of Invalid Decision Manipulation ('INVESTIGATE' -> 'BLOCK')...")
    case = create_sample_case(score=0.85, action="INVESTIGATE")
    bad_investigator = LLMInvestigator(provider=BadActionLLMProvider())

    caught = False
    try:
        bad_investigator.generate_report(case)
    except LLMInvestigatorError as e:
        caught = True
        print(f"  ✓ PASS: Successfully caught and rejected decision override. Exception: {e}")

    assert caught, "Failed to reject invalid action manipulation ('BLOCK')!"


def test_5_fabricated_evidence_rejection():
    print("\n[Test 5] Rejection of Fabricated Ground-Truth Field Leakage...")
    case = create_sample_case(score=0.85, action="INVESTIGATE")
    leaking_investigator = LLMInvestigator(provider=FabricatedLeakageLLMProvider())

    caught = False
    try:
        leaking_investigator.generate_report(case)
    except LLMInvestigatorError as e:
        caught = True
        print(f"  ✓ PASS: Successfully caught and rejected ground-truth leakage. Exception: {e}")

    assert caught, "Failed to reject ground-truth leakage ('is_fraud')!"


def test_6_provider_unavailable_safe_failure():
    print("\n[Test 6] Safe Failure Behavior When Provider Fails...")
    case = create_sample_case(score=0.85, action="INVESTIGATE")
    failing_investigator = LLMInvestigator(provider=FailingLLMProvider())

    caught = False
    try:
        failing_investigator.generate_report(case)
    except LLMInvestigatorError as e:
        caught = True
        print(f"  ✓ PASS: Provider failure caught safely without corrupting deterministic decision. Exception: {e}")

    assert caught, "Failed to raise LLMInvestigatorError on provider failure!"
    # Verify input case deterministic decision is unchanged and fully intact
    assert case.decision.risk_score == 0.85
    assert case.decision.action == "INVESTIGATE"


def main():
    print("=" * 80)
    print("SENTINEL LLM INVESTIGATOR COMPREHENSIVE TEST SUITE")
    print("=" * 80)

    test_1_normal_high_risk_case()
    test_2_benign_connected_network()
    test_3_graph_only_suspicious_connection()
    test_4_invalid_decision_manipulation()
    test_5_fabricated_evidence_rejection()
    test_6_provider_unavailable_safe_failure()

    print("\n" + "=" * 80)
    print("ALL 6 LLM INVESTIGATOR SUITE TESTS PASSED CLEANLY!")
    print("=" * 80)


if __name__ == "__main__":
    main()
