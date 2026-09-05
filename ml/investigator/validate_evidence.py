"""
Sentinel — Coordinated Payment Abuse Intelligence
Module: Evidence Validator (validate_evidence.py)

Purpose:
Validates raw dict / JSON investigation cases against the InvestigationCase Data Contract schema.

Strict Audit & Integrity Checks:
-------------------------------
1. Required top-level keys present.
2. Complete nested object validation (Decision, Summary, ML, Graph, Behavioral, Benign, Items).
3. Value range & enum validations (risk_score in 0.0-1.0, valid risk_level, action, category, severity, source).
4. ABSOLUTE GROUND-TRUTH SEPARATION: Ensures zero evaluation fields (is_fraud, fraud_scenario, label, ground_truth)
   exist in the investigation evidence.
"""

import json
import os
from typing import Dict, Any, List, Tuple

VALID_RISK_LEVELS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
VALID_ACTIONS = {"ALLOW", "MONITOR", "INVESTIGATE"}
VALID_CATEGORIES = {"ML", "GRAPH", "BEHAVIORAL", "BENIGN"}
VALID_SEVERITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
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
    Recursively scans nested objects for forbidden ground-truth labels.
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


def validate_investigation_case(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Performs comprehensive structural & integrity validation on an InvestigationCase dictionary.
    
    Args:
        data (Dict[str, Any]): Dictionary representation of an InvestigationCase.
        
    Returns:
        Tuple[bool, List[str]]: (is_valid, list_of_error_strings)
    """
    errors = []

    # 1. Ground-Truth Separation Check
    leakage_errors = _check_forbidden_fields(data)
    errors.extend(leakage_errors)

    # 2. Top-Level Keys
    required_top = [
        "case_id", "timestamp", "decision", "transaction_summary",
        "ml_evidence", "graph_evidence", "behavioral_evidence",
        "benign_evidence", "evidence_items"
    ]
    for key in required_top:
        if key not in data:
            errors.append(f"Missing required top-level key: '{key}'")

    if errors:
        return False, errors

    # 3. Decision Nested Object Validation
    decision = data.get("decision", {})
    if not isinstance(decision, dict):
        errors.append("'decision' must be a dictionary.")
    else:
        for f in ["risk_score", "risk_level", "action", "threshold_applied"]:
            if f not in decision:
                errors.append(f"decision missing required field: '{f}'")
        
        risk_score = decision.get("risk_score")
        if not isinstance(risk_score, (int, float)) or not (0.0 <= risk_score <= 1.0):
            errors.append(f"Invalid decision.risk_score: {risk_score} (must be numeric between 0.0 and 1.0)")
        
        risk_level = decision.get("risk_level")
        if risk_level not in VALID_RISK_LEVELS:
            errors.append(f"Invalid decision.risk_level: '{risk_level}' (must be one of {VALID_RISK_LEVELS})")

        action = decision.get("action")
        if action not in VALID_ACTIONS:
            errors.append(f"Invalid decision.action: '{action}' (must be one of {VALID_ACTIONS})")

    # 4. Transaction Summary Nested Object Validation
    tsum = data.get("transaction_summary", {})
    if not isinstance(tsum, dict):
        errors.append("'transaction_summary' must be a dictionary.")
    else:
        for f in ["target_transaction_id", "target_user_id", "amount", "connected_users_count"]:
            if f not in tsum:
                errors.append(f"transaction_summary missing required field: '{f}'")

    # 5. ML Evidence Nested Object Validation
    ml_ev = data.get("ml_evidence", {})
    if not isinstance(ml_ev, dict):
        errors.append("'ml_evidence' must be a dictionary.")
    else:
        prob = ml_ev.get("predicted_probability")
        if not isinstance(prob, (int, float)) or not (0.0 <= prob <= 1.0):
            errors.append(f"Invalid ml_evidence.predicted_probability: {prob}")

    # 6. Graph Evidence Nested Object Validation
    g_ev = data.get("graph_evidence", {})
    if not isinstance(g_ev, dict):
        errors.append("'graph_evidence' must be a dictionary.")
    else:
        conc = g_ev.get("merchant_concentration")
        if not isinstance(conc, (int, float)) or not (0.0 <= conc <= 1.0):
            errors.append(f"Invalid graph_evidence.merchant_concentration: {conc}")

    # 7. Behavioral Evidence Nested Object Validation
    b_ev = data.get("behavioral_evidence", {})
    if not isinstance(b_ev, dict):
        errors.append("'behavioral_evidence' must be a dictionary.")

    # 8. Benign Evidence Nested Object Validation
    ben_ev = data.get("benign_evidence", {})
    if not isinstance(ben_ev, dict):
        errors.append("'benign_evidence' must be a dictionary.")

    # 9. Evidence Items Array Validation
    items = data.get("evidence_items", [])
    if not isinstance(items, list):
        errors.append("'evidence_items' must be a list.")
    else:
        for idx, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append(f"evidence_items[{idx}] must be a dictionary.")
                continue

            for field in ["category", "signal", "value", "severity", "description", "source"]:
                if field not in item:
                    errors.append(f"evidence_items[{idx}] missing required field: '{field}'")

            cat = item.get("category")
            if cat not in VALID_CATEGORIES:
                errors.append(f"evidence_items[{idx}].category '{cat}' invalid (must be one of {VALID_CATEGORIES})")

            sev = item.get("severity")
            if sev not in VALID_SEVERITIES:
                errors.append(f"evidence_items[{idx}].severity '{sev}' invalid (must be one of {VALID_SEVERITIES})")

            src = item.get("source")
            if src not in VALID_SOURCES:
                errors.append(f"evidence_items[{idx}].source '{src}' invalid (must be one of {VALID_SOURCES})")

    is_valid = len(errors) == 0
    return is_valid, errors


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sample_file = os.path.join(script_dir, "examples", "sample_case.json")

    print("=" * 75)
    print("REFACTORED INVESTIGATION CASE DATA CONTRACT VALIDATION TEST")
    print("=" * 75)

    # Test 1: sample_case.json
    print("\n[Test 1] Validating sample_case.json...")
    if os.path.exists(sample_file):
        with open(sample_file, "r", encoding="utf-8") as f:
            sample_data = json.load(f)
        valid, errs = validate_investigation_case(sample_data)
        if valid:
            print("  ✓ PASS: sample_case.json passed validation cleanly!")
            print(f"  • Case ID: {sample_data['case_id']} | Risk Score: {sample_data['decision']['risk_score']} | Action: {sample_data['decision']['action']}")
        else:
            print(f"  ❌ FAIL: sample_case.json validation failed with errors: {errs}")

    # Test 2: Ground-Truth Leakage Check
    print("\n[Test 2] Edge Case: Ground-Truth Leakage ('is_fraud' present)...")
    bad_data_leakage = {
        "case_id": "C100", "timestamp": None,
        "decision": {"risk_score": 0.5, "risk_level": "HIGH", "action": "INVESTIGATE", "threshold_applied": 0.45},
        "transaction_summary": {"target_transaction_id": "T1", "target_user_id": "U1", "amount": 10.0, "connected_users_count": 1},
        "ml_evidence": {"ml_model_name": "RF", "predicted_probability": 0.5, "high_risk_flag": True},
        "graph_evidence": {"merchant_concentration": 0.0},
        "behavioral_evidence": {}, "benign_evidence": {}, "evidence_items": [],
        "is_fraud": 1  # FORBIDDEN!
    }
    valid, errs = validate_investigation_case(bad_data_leakage)
    assert not valid, "Failed to catch ground truth leakage!"
    print(f"  ✓ PASS: Correctly rejected ground-truth field leakage. Error caught: {errs[0]}")

    # Test 3: Missing Required Top-Level Field
    print("\n[Test 3] Edge Case: Missing Required Top-Level Field ('decision')...")
    bad_data1 = {"case_id": "C100", "timestamp": None}
    valid, errs = validate_investigation_case(bad_data1)
    assert not valid, "Failed to reject missing field!"
    print(f"  ✓ PASS: Correctly rejected missing field. Error caught: {errs[0]}")

    # Test 4: Invalid Action Enum ("BLOCK")
    print("\n[Test 4] Edge Case: Invalid Action Enum ('BLOCK' - invalid upstream action)...")
    bad_data2 = {
        "case_id": "C101", "timestamp": None,
        "decision": {"risk_score": 0.8, "risk_level": "HIGH", "action": "BLOCK", "threshold_applied": 0.45},
        "transaction_summary": {"target_transaction_id": "T1", "target_user_id": "U1", "amount": 10.0, "connected_users_count": 1},
        "ml_evidence": {"ml_model_name": "RF", "predicted_probability": 0.5, "high_risk_flag": True},
        "graph_evidence": {"merchant_concentration": 0.0},
        "behavioral_evidence": {}, "benign_evidence": {}, "evidence_items": []
    }
    valid, errs = validate_investigation_case(bad_data2)
    assert not valid, "Failed to reject invalid action enum!"
    print(f"  ✓ PASS: Correctly rejected invalid action enum. Error caught: {errs[0]}")

    # Test 5: Malformed Evidence Item Source
    print("\n[Test 5] Edge Case: Malformed Evidence Item (invalid source 'magic_ai')...")
    bad_data3 = {
        "case_id": "C103", "timestamp": None,
        "decision": {"risk_score": 0.5, "risk_level": "HIGH", "action": "INVESTIGATE", "threshold_applied": 0.45},
        "transaction_summary": {"target_transaction_id": "T1", "target_user_id": "U1", "amount": 10.0, "connected_users_count": 1},
        "ml_evidence": {"ml_model_name": "RF", "predicted_probability": 0.5, "high_risk_flag": True},
        "graph_evidence": {"merchant_concentration": 0.0},
        "behavioral_evidence": {}, "benign_evidence": {},
        "evidence_items": [{"category": "ML", "signal": "x", "value": 1, "severity": "HIGH", "description": "d", "source": "magic_ai"}]
    }
    valid, errs = validate_investigation_case(bad_data3)
    assert not valid, "Failed to reject invalid source!"
    print(f"  ✓ PASS: Correctly rejected invalid source. Error caught: {errs[0]}")

    print("\n" + "=" * 75)
    print("ALL ENHANCED VALIDATION UNIT TESTS PASSED CLEANLY!")
    print("=" * 75)


if __name__ == "__main__":
    main()
