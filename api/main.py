"""
Sentinel — Coordinated Payment Abuse Intelligence
Module: FastAPI Backend Application (api/main.py)

Purpose:
Exposes REST API endpoints connecting the React Frontend Dashboard to the deterministic
Sentinel ML baseline, NetworkX graph analyzer, Fusion Risk Engine, and LLM Investigator.

Architectural Guarantees:
------------------------
1. LAZY-LOAD LLM REPORTS: Fast startup without freezes. LLM reports generated ON-DEMAND when
   a user selects a case, and cached in memory.
2. DETERMINISTIC DECISION AUTHORITY: Backend endpoints preserve Fusion Risk Engine decisions.
3. GRAPH CONNECTION != FRAUD: Subgraph endpoint explicitly includes metadata guardrails.
"""

import os
import pandas as pd
import joblib
import networkx as nx
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

# Upstream Sentinel Imports
try:
    from ml.graph.build_graph import build_heterogeneous_graph
    from ml.graph.detect_rings import extract_candidate_clusters
    from ml.graph.fusion_risk import compute_fusion_risk
    from ml.investigator.evidence_builder import build_investigation_case
    from ml.investigator.llm_investigator import LLMInvestigator
except ImportError:
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from ml.graph.build_graph import build_heterogeneous_graph
    from ml.graph.detect_rings import extract_candidate_clusters
    from ml.graph.fusion_risk import compute_fusion_risk
    from ml.investigator.evidence_builder import build_investigation_case
    from ml.investigator.llm_investigator import LLMInvestigator


app = FastAPI(
    title="Sentinel Coordinated Abuse Intelligence API",
    description="FastAPI service serving Sentinel Risk Detection, Graph Subgraph, and LLM Investigation Reports.",
    version="1.0.0"
)

# Enable CORS for local Vite development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global State Container for Pipeline Artifacts
PIPELINE_STATE: Dict[str, Any] = {
    "df": None,
    "model": None,
    "graph": None,
    "clusters": None,
    "investigator": None,
    "cases_dict": {},       # case_id -> InvestigationCase object
    "reports_cache": {},    # case_id -> InvestigationReport dict (Lazy-loaded)
    "summary_list": []      # list of lightweight summary dicts for triage queue
}


def load_pipeline_state():
    """Loads dataset, model, graph, and initializes cases state without LLM startup freeze."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    v3_path = os.path.join(project_root, "ml", "data", "raw", "transactions_v3.csv")
    model_path = os.path.join(project_root, "ml", "models", "frozen_rf_model.joblib")

    print("[FastAPI Startup] Loading transactions_v3.csv dataset...")
    df = pd.read_csv(v3_path)
    PIPELINE_STATE["df"] = df

    print("[FastAPI Startup] Loading frozen Random Forest model...")
    model = joblib.load(model_path)
    PIPELINE_STATE["model"] = model

    print("[FastAPI Startup] Constructing NetworkX heterogeneous graph...")
    G = build_heterogeneous_graph(df)
    PIPELINE_STATE["graph"] = G

    print("[FastAPI Startup] Extracting candidate infrastructure clusters...")
    clusters = extract_candidate_clusters(G)
    PIPELINE_STATE["clusters"] = clusters

    print("[FastAPI Startup] Initializing LLM Investigator...")
    PIPELINE_STATE["investigator"] = LLMInvestigator()

    # Pre-build lightweight cases for fast triage queue (0 LLM API calls)
    print("[FastAPI Startup] Building lightweight triage case summaries...")
    feature_cols = [
        "amount", "account_age_days", "transactions_last_hour",
        "transactions_last_day", "failed_transactions", "unique_devices", "unique_cards"
    ]

    cases_dict = {}
    summary_list = []

    # Map user to cluster
    user_cluster_map = {}
    for c in clusters:
        for u in c["users"]:
            user_cluster_map[u] = c

    # Process transactions (sample up to 250 diverse transactions for fast UI demo)
    sample_df = df.head(250)

    for idx, row in sample_df.iterrows():
        txn_row = row.to_dict()
        txn_id = str(txn_row["transaction_id"])
        user_id = str(txn_row["user_id"])
        u_node = f"USER:{user_id}"

        # Single transaction ML inference
        X = pd.DataFrame([txn_row])[feature_cols]
        ml_prob = float(model.predict_proba(X)[0, 1])

        # Cluster stats
        c_stats = user_cluster_map.get(u_node, {})

        # Compute Fusion Risk Engine outcome
        fusion_res = compute_fusion_risk(txn_row, ml_prob, c_stats)

        # Build InvestigationCase via pure adapter
        case = build_investigation_case(txn_row, ml_prob, c_stats, fusion_res)
        case_dict_obj = case
        cases_dict[case.case_id] = case

        # Build lightweight summary
        primary_driver = "normal_behavior"
        if case.evidence_items:
            primary_driver = case.evidence_items[0].signal

        summary_list.append({
            "case_id": case.case_id,
            "target_transaction_id": case.transaction_summary.target_transaction_id,
            "user_id": case.transaction_summary.target_user_id,
            "amount": case.transaction_summary.amount,
            "timestamp": case.transaction_summary.timestamp or "2026-09-05T00:00:00Z",
            "risk_score": case.decision.risk_score,
            "risk_level": case.decision.risk_level,
            "action": case.decision.action,
            "primary_driver": primary_driver,
            "connected_users_count": case.transaction_summary.connected_users_count,
            "is_benign_pattern": case.benign_evidence.is_benign_pattern_detected
        })

    PIPELINE_STATE["cases_dict"] = cases_dict
    PIPELINE_STATE["summary_list"] = summary_list
    print(f"[FastAPI Startup] Pipeline ready! Pre-loaded {len(summary_list)} cases instantly.")


@app.on_event("startup")
def on_startup():
    if not PIPELINE_STATE["summary_list"]:
        load_pipeline_state()

# Ensure state is loaded if imported directly
if not PIPELINE_STATE["summary_list"]:
    load_pipeline_state()


@app.get("/")
def read_root():
    return {
        "service": "Sentinel Risk Engine API",
        "status": "online",
        "loaded_cases": len(PIPELINE_STATE["summary_list"]),
        "deterministic_engine": "Fusion Risk Engine v1.0"
    }


@app.get("/api/cases")
def get_cases(
    sort_by: str = Query("risk_score", description="Sort field: risk_score, amount, connected_users_count"),
    order: str = Query("desc", description="Sort order: desc or asc"),
    risk_level: Optional[str] = Query(None, description="Filter by risk_level: LOW, MEDIUM, HIGH, CRITICAL"),
    action: Optional[str] = Query(None, description="Filter by action: ALLOW, MONITOR, INVESTIGATE")
):
    """
    Returns lightweight summary list of cases for the risk analyst triage queue.
    Instant execution without LLM delay.
    """
    cases = list(PIPELINE_STATE["summary_list"])

    if risk_level:
        cases = [c for c in cases if c["risk_level"].upper() == risk_level.upper()]

    if action:
        cases = [c for c in cases if c["action"].upper() == action.upper()]

    reverse = (order.lower() == "desc")
    cases.sort(key=lambda x: x.get(sort_by, 0), reverse=reverse)
    return cases


@app.get("/api/cases/{case_id}")
def get_case_detail(case_id: str):
    """
    Returns full InvestigationCase data and LAZY-LOADS LLM InvestigationReport on-demand.
    Resulting report is cached in memory for subsequent requests.
    """
    case = PIPELINE_STATE["cases_dict"].get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case ID '{case_id}' not found.")

    # Lazy-load LLM report on demand
    if case_id not in PIPELINE_STATE["reports_cache"]:
        print(f"[FastAPI] Lazy-loading LLM InvestigationReport for '{case_id}' on-demand...")
        investigator = PIPELINE_STATE["investigator"]
        report = investigator.generate_report(case)
        PIPELINE_STATE["reports_cache"][case_id] = report.to_dict()

    return {
        "case": case.to_dict(),
        "report": PIPELINE_STATE["reports_cache"][case_id]
    }


@app.get("/api/cases/{case_id}/subgraph")
def get_case_subgraph(case_id: str):
    """
    Returns entity network nodes and edges for visual graph rendering.
    Enforces GRAPH CONNECTION != FRAUD metadata guardrails.
    """
    case = PIPELINE_STATE["cases_dict"].get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case ID '{case_id}' not found.")

    G = PIPELINE_STATE["graph"]
    target_user = case.transaction_summary.target_user_id
    u_node = f"USER:{target_user}"

    # Extract 2-hop neighborhood around target user for clear visual layout
    if u_node in G:
        nodes_set = {u_node}
        for nbr in G.neighbors(u_node):
            nodes_set.add(nbr)
            for nbr2 in G.neighbors(nbr):
                nodes_set.add(nbr2)
        sub_g = G.subgraph(nodes_set)
    else:
        sub_g = nx.Graph()

    nodes = []
    for n, attrs in sub_g.nodes(data=True):
        ntype = attrs.get("node_type", "UNKNOWN")
        raw_id = attrs.get("raw_id", n)
        nodes.append({
            "id": n,
            "label": f"{ntype}:{raw_id}",
            "type": ntype,
            "raw_id": raw_id,
            "is_seed": (n == u_node)
        })

    edges = []
    for u, v, attrs in sub_g.edges(data=True):
        rel = attrs.get("relation", "CONNECTED")
        edges.append({
            "source": u,
            "target": v,
            "relation": rel
        })

    return {
        "case_id": case_id,
        "target_user_id": target_user,
        "nodes": nodes,
        "edges": edges,
        "metadata": {
            "statement": "GRAPH CONNECTION != FRAUD",
            "notice": "Shared infrastructure indicates topological relationship, not confirmed fraud."
        }
    }
