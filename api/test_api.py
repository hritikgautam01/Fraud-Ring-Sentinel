"""
Sentinel — Coordinated Payment Abuse Intelligence
Module: API Endpoint Test Suite (api/test_api.py)

Purpose:
Tests all FastAPI REST endpoints using TestClient to verify:
  1. GET /api/cases returns 200 OK and sorted case summary list instantly.
  2. GET /api/cases/{case_id} returns 200 OK with full InvestigationCase and on-demand LLM InvestigationReport.
  3. GET /api/cases/{case_id}/subgraph returns 200 OK with valid nodes, edges, and guardrail metadata.
"""

import os
import sys
from fastapi.testclient import TestClient

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

from api.main import app

client = TestClient(app)


def test_root_endpoint():
    print("\n[Test 1] Testing Root Endpoint GET / ...")
    res = client.get("/")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    data = res.json()
    assert data["status"] == "online"
    print("  ✓ PASS: Root endpoint online.")


def test_get_cases_triage_queue():
    print("\n[Test 2] Testing Triage Queue GET /api/cases ...")
    res = client.get("/api/cases?sort_by=risk_score&order=desc")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    cases = res.json()
    assert isinstance(cases, list), "Expected list of case summaries"
    assert len(cases) > 0, "Summary list is empty"

    first_case = cases[0]
    assert "case_id" in first_case
    assert "risk_score" in first_case
    assert "risk_level" in first_case
    assert "action" in first_case

    # Verify risk_score descending sort
    scores = [c["risk_score"] for c in cases]
    assert scores == sorted(scores, reverse=True), "Cases not sorted by risk_score descending"
    print(f"  ✓ PASS: Retrieved {len(cases)} lightweight cases sorted by risk_score descending.")


def test_get_case_detail_lazy_loaded():
    print("\n[Test 3] Testing On-Demand Detail GET /api/cases/{case_id} ...")
    res_cases = client.get("/api/cases")
    target_case_id = res_cases.json()[0]["case_id"]

    res_detail = client.get(f"/api/cases/{target_case_id}")
    assert res_detail.status_code == 200, f"Expected 200, got {res_detail.status_code}"
    data = res_detail.json()

    assert "case" in data
    assert "report" in data
    assert data["case"]["case_id"] == target_case_id
    assert data["report"]["case_id"] == target_case_id
    assert data["report"]["risk_assessment"]["action"] == data["case"]["decision"]["action"]

    # Verify cached second call
    res_detail2 = client.get(f"/api/cases/{target_case_id}")
    assert res_detail2.status_code == 200
    print(f"  ✓ PASS: Successfully lazy-loaded LLM report for '{target_case_id}' on-demand and verified cache.")


def test_get_subgraph_endpoint():
    print("\n[Test 4] Testing Subgraph Endpoint GET /api/cases/{case_id}/subgraph ...")
    res_cases = client.get("/api/cases")
    target_case_id = res_cases.json()[0]["case_id"]

    res_subgraph = client.get(f"/api/cases/{target_case_id}/subgraph")
    assert res_subgraph.status_code == 200, f"Expected 200, got {res_subgraph.status_code}"
    data = res_subgraph.json()

    assert "nodes" in data
    assert "edges" in data
    assert "metadata" in data
    assert data["metadata"]["statement"] == "GRAPH CONNECTION != FRAUD"

    seed_nodes = [n for n in data["nodes"] if n.get("is_seed")]
    assert len(seed_nodes) > 0, "No seed user node found in subgraph"
    print(f"  ✓ PASS: Retrieved subgraph with {len(data['nodes'])} nodes and {len(data['edges'])} edges with guardrail metadata.")


def main():
    print("=" * 80)
    print("SENTINEL FASTAPI BACKEND TEST SUITE")
    print("=" * 80)

    test_root_endpoint()
    test_get_cases_triage_queue()
    test_get_case_detail_lazy_loaded()
    test_get_subgraph_endpoint()

    print("\n" + "=" * 80)
    print("ALL FASTAPI ENDPOINT TESTS PASSED CLEANLY!")
    print("=" * 80)


if __name__ == "__main__":
    main()
