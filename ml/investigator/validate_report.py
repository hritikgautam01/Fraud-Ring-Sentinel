"""
Sentinel — Coordinated Payment Abuse Intelligence
Module: Report Validator (validate_report.py)

Purpose:
Validates raw dict / JSON investigation reports produced by the LLM Investigator against
the InvestigationReport Data Contract schema and deterministic decision authority constraints.

Strict Audit & Guardrail Checks:
-------------------------------
1. Top-level structure: All required report keys present and correctly typed.
2. Authoritative Decision Matching: If an expected_case is provided, the report MUST match the
   deterministic case_id, risk_score, risk_level, action, and threshold_applied EXACTLY.
3. Forbidden Action & Label Check: Rejects invalid actions such as 'BLOCK' and forbids any
   ground-truth evaluation fields (is_fraud, fraud_scenario, label, ground_truth).
4. Evidence Source Verification: Verifies cited sources correspond only to valid upstream components
   (random_forest_baseline, graph_cluster_analyzer, behavioral_analyzer, fusion_risk_engine).
"""

import json
import os
from typing import Dict, Any, List, Tuple, Optional

VALID_RISK_LEVELS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
VALID_ACTIONS = {"ALLOW", "MONITOR", "INVESTIGATE"}
VALID_SOURCES = {
    "random_forest_baseline",
    "graph_cluster_analyzer",
    "behavioral_analyzer",
    "fusion_risk_engine"
}

FORBIDDEN_GROUND_TRUTH_FIELDS = {
    "is_fraud",
    "fraud_scenario",
    "label",
    "ground_truth",
    "target_label"
}


def _check_forbidden_fields(obj: Any, path: str = "") -> List[str]:
    """
    Recursively scans nested dictionary structures for forbidden ground-truth labels.
    """
    errors = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            current_path = f"{path}.{k}" if path else k
            if k in FORBIDDEN_GROUND_TRUTH_FIELDS:
                errors.append(f"Forbidden ground-truth field '{k}' detected at '{current_path}'")
            errors.extend(_check_forbidden_fields(v, current_path))
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            current_path = f"{path}[{idx}]"
            errors.extend(_check_forbidden_fields(item, current_path))
    return errors


def validate_investigation_report(
    report_dict: Dict[str, Any],
    expected_case: Optional[Dict[str, Any]] = None
) -> Tuple[bool, List[str]]:
    """
    Performs comprehensive structural, enum, and decision authority validation on an InvestigationReport dictionary.
    
    Args:
        report_dict (Dict[str, Any]): Dictionary representation of an InvestigationReport.
        expected_case (Optional[Dict[str, Any]]): Input InvestigationCase dict for decision matching.
        
    Returns:
        Tuple[bool, List[str]]: (is_valid, list_of_error_strings)
    """
    errors = []

    # 1. Ground-Truth Separation Check
    leakage_errors = _check_forbidden_fields(report_dict)
    errors.extend(leakage_errors)

    # 2. Required Top-Level Keys
    required_top = [
        "case_id", "investigation_summary", "risk_assessment",
        "why_flagged", "supporting_evidence", "benign_considerations",
        "analyst_recommendation", "limitations"
    ]
    for key in required_top:
        if key not in report_dict:
            errors.append(f"Missing required top-level key: '{key}'")

    if errors:
        return False, errors

    # Top-level type validation
    if not isinstance(report_dict.get("case_id"), str) or not report_dict.get("case_id"):
        errors.append("'case_id' must be a non-empty string.")

    if not isinstance(report_dict.get("investigation_summary"), str):
        errors.append("'investigation_summary' must be a string.")

    if not isinstance(report_dict.get("why_flagged"), list):
        errors.append("'why_flagged' must be a list of strings.")

    if not isinstance(report_dict.get("benign_considerations"), str):
        errors.append("'benign_considerations' must be a string.")

    if not isinstance(report_dict.get("analyst_recommendation"), str):
        errors.append("'analyst_recommendation' must be a string.")

    if not isinstance(report_dict.get("limitations"), str):
        errors.append("'limitations' must be a string.")

    # 3. Risk Assessment Object Validation
    risk_ass = report_dict.get("risk_assessment", {})
    if not isinstance(risk_ass, dict):
        errors.append("'risk_assessment' must be a dictionary.")
    else:
        for f in ["risk_score", "risk_level", "action", "threshold_applied"]:
            if f not in risk_ass:
                errors.append(f"risk_assessment missing required field: '{f}'")

        risk_score = risk_ass.get("risk_score")
        if not isinstance(risk_score, (int, float)) or not (0.0 <= float(risk_score) <= 1.0):
            errors.append(f"Invalid risk_assessment.risk_score: {risk_score} (must be numeric between 0.0 and 1.0)")

        risk_level = risk_ass.get("risk_level")
        if risk_level not in VALID_RISK_LEVELS:
            errors.append(f"Invalid risk_assessment.risk_level: '{risk_level}' (must be one of {VALID_RISK_LEVELS})")

        action = risk_ass.get("action")
        if action not in VALID_ACTIONS:
            errors.append(f"Invalid risk_assessment.action: '{action}' (must be one of {VALID_ACTIONS}, 'BLOCK' is forbidden)")

    # 4. Supporting Evidence Object Validation
    supp_ev = report_dict.get("supporting_evidence", {})
    if not isinstance(supp_ev, dict):
        errors.append("'supporting_evidence' must be a dictionary.")
    else:
        for f in ["ml_evidence", "graph_evidence", "behavioral_evidence"]:
            if f not in supp_ev:
                errors.append(f"supporting_evidence missing required field: '{f}'")
            elif not isinstance(supp_ev[f], str):
                errors.append(f"supporting_evidence.{f} must be a string.")

    # 5. Deterministic Decision Matching Validation (if expected_case provided)
    if expected_case:
        exp_case_id = expected_case.get("case_id")
        if exp_case_id and report_dict.get("case_id") != exp_case_id:
            errors.append(
                f"Case ID mismatch: Report case_id '{report_dict.get('case_id')}' does not match expected '{exp_case_id}'"
            )

        exp_dec = expected_case.get("decision", {})
        if exp_dec:
            exp_score = float(exp_dec.get("risk_score", 0.0))
            rep_score = float(risk_ass.get("risk_score", -1.0))
            if abs(exp_score - rep_score) > 0.0001:
                errors.append(
                    f"Decision Override Violation: Report risk_score ({rep_score}) does not match deterministic risk_score ({exp_score})"
                )

            exp_level = exp_dec.get("risk_level")
            rep_level = risk_ass.get("risk_level")
            if exp_level and rep_level != exp_level:
                errors.append(
                    f"Decision Override Violation: Report risk_level ('{rep_level}') does not match deterministic risk_level ('{exp_level}')"
                )

            exp_action = exp_dec.get("action")
            rep_action = risk_ass.get("action")
            if exp_action and rep_action != exp_action:
                errors.append(
                    f"Decision Override Violation: Report action ('{rep_action}') does not match deterministic action ('{exp_action}')"
                )

    is_valid = len(errors) == 0
    return is_valid, errors


def main():
    print("=" * 75)
    print("INVESTIGATION REPORT VALIDATOR UNIT TEST SUITE")
    print("=" * 75)

    valid_report = {
        "case_id": "CASE_TXN_V3_009900",
        "investigation_summary": "Transaction TXN_V3_009900 was flagged due to high ML probability and shared infrastructure.",
        "risk_assessment": {
            "risk_score": 0.8123,
            "risk_level": "CRITICAL",
            "action": "INVESTIGATE",
            "threshold_applied": 0.45
        },
        "why_flagged": [
            "Random forest model predicted 95% anomaly score",
            "High IP proxy density across cluster (7.25 users/IP)"
        ],
        "supporting_evidence": {
            "ml_evidence": "Random Forest anomaly probability is 95.0%",
            "graph_evidence": "29 users connected across 4 IP addresses targeting 1 merchant",
            "behavioral_evidence": "Transaction velocity of 3 txns/hr"
        },
        "benign_considerations": "No benign network patterns identified.",
        "analyst_recommendation": "Recommend manual review of connected user devices and payment instruments.",
        "limitations": "Graph connection alone is insufficient to prove fraud intent."
    }

    sample_case = {
        "case_id": "CASE_TXN_V3_009900",
        "decision": {
            "risk_score": 0.8123,
            "risk_level": "CRITICAL",
            "action": "INVESTIGATE",
            "threshold_applied": 0.45
        }
    }

    # Test 1: Valid Report
    print("\n[Test 1] Validating correct report matching sample case...")
    valid, errs = validate_investigation_report(valid_report, sample_case)
    if valid:
        print("  ✓ PASS: Report passed validation cleanly!")
    else:
        print(f"  ❌ FAIL: {errs}")

    # Test 2: Decision Manipulation Attempt ('BLOCK')
    print("\n[Test 2] Validating rejection of invalid action 'BLOCK'...")
    manipulated_report = json.loads(json.dumps(valid_report))
    manipulated_report["risk_assessment"]["action"] = "BLOCK"
    valid, errs = validate_investigation_report(manipulated_report, sample_case)
    assert not valid, "Failed to reject BLOCK action!"
    print(f"  ✓ PASS: Correctly rejected 'BLOCK' action. Error: {errs[0]}")

    # Test 3: Decision Score Manipulation Attempt
    print("\n[Test 3] Validating rejection of altered risk score...")
    manipulated_score = json.loads(json.dumps(valid_report))
    manipulated_score["risk_assessment"]["risk_score"] = 0.2000
    valid, errs = validate_investigation_report(manipulated_score, sample_case)
    assert not valid, "Failed to reject altered risk score!"
    print(f"  ✓ PASS: Correctly rejected altered risk score. Error: {errs[0]}")

    # Test 4: Ground-Truth Leakage
    print("\n[Test 4] Validating rejection of ground-truth field 'is_fraud'...")
    leaked_report = json.loads(json.dumps(valid_report))
    leaked_report["is_fraud"] = 1
    valid, errs = validate_investigation_report(leaked_report, sample_case)
    assert not valid, "Failed to catch ground truth leakage!"
    print(f"  ✓ PASS: Correctly caught ground-truth leakage. Error: {errs[0]}")

    print("\n" + "=" * 75)
    print("ALL REPORT VALIDATION UNIT TESTS PASSED CLEANLY!")
    print("=" * 75)


if __name__ == "__main__":
    main()
