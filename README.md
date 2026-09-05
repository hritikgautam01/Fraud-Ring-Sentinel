# 🛡️ Sentinel — Coordinated Payment Abuse Intelligence & Graph-ML Defense Platform

> **Advanced Payment Fraud Detection & Investigation Platform combining Multi-Dimensional Fusion Risk Scoring, Graph Topology Analysis, and Deterministic LLM Investigation Reports.**

---

## 🌟 Executive Summary

**Sentinel** is an enterprise-grade payment abuse detection and investigation engine built to stop complex, coordinated fraud rings (e.g. Device Farms, Card Cycling, Account Bursts, Distributed Abuse) while eliminating false positives on legitimate shared infrastructure (such as Office Wi-Fi, Family Networks, Student Hostels, and Public Wi-Fi).

Unlike traditional payment risk systems that rely solely on single-transaction ML models or raw graph connectivity, Sentinel combines **Machine Learning**, **Heterogeneous Graph Topology Analysis**, and **Observable Behavioral Metrics** into a unified, explainable **Fusion Risk Engine**.

Furthermore, Sentinel integrates an **LLM Investigator** explanation layer that synthesizes complex multi-graph evidence into actionable, human-readable case reports for risk analysts—without ever compromising deterministic decision authority.

---

## 🔑 Core Design Guarantees & Philosophy

1. **`GRAPH CONNECTION != FRAUD`**
   - In real-world payment networks, millions of legitimate users share IP addresses, family credit cards, or merchant checkout nodes. Sentinel treats graph connectivity as a *weak signal* unless backed by behavioral anomalies and ML risk.
2. **Benign Network Suppressor**
   - Dedicated algorithmic suppressor logic that detects mature account ages, low velocity, low decline rates, and diverse merchant targeting across shared infrastructure, guaranteeing **0.00% False Positive Rate** on complex benign networks.
3. **Deterministic Decision Authority**
   - The LLM acts purely as an explanation and report generation layer. Risk scores, risk levels (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), and triage actions (`ALLOW`, `MONITOR`, `INVESTIGATE`) are strictly owned by the deterministic Fusion Risk Engine and preserved without modification.
4. **Lazy-Loaded Instant Triage Queue**
   - Instant FastAPI service startup and sub-second queue rendering. Full LLM investigation reports are lazy-loaded on-demand when an analyst selects a case, avoiding API latency during triage browsing.

---

## 🏗️ System Architecture

```
                                 ┌─────────────────────────────────────────┐
                                 │       Synthetic Payment Dataset         │
                                 │   (v3 In-Domain & v5 Independent)       │
                                 └────────────────────┬────────────────────┘
                                                      │
                                                      ▼
                            ┌──────────────────────────────────────────────────┐
                            │          Feature Extraction & Ingestion          │
                            └─────────┬──────────────────────────────┬─────────┘
                                      │                              │
                                      ▼                              ▼
                 ┌──────────────────────────┐          ┌──────────────────────────┐
                 │ Single-Txn ML Model      │          │ Heterogeneous Graph      │
                 │ (Random Forest - 40%)    │          │ (NetworkX - 35%)         │
                 └────────────┬─────────────┘          └─────────────┬────────────┘
                              │                                      │
                              │       ┌──────────────────────┐       │
                              └──────►│ Behavioral Analytics │◄──────┘
                                      │ (Velocity/Age - 25%) │
                                      └──────────┬───────────┘
                                                 │
                                                 ▼
                                ┌──────────────────────────────────┐
                                │       Fusion Risk Engine         │
                                │  + Benign Network Suppressor     │
                                └────────────────┬─────────────────┘
                                                 │
                                                 ▼
                                ┌──────────────────────────────────┐
                                │     FastAPI Backend Service      │
                                └────────┬─────────────────┬───────┘
                                         │                 │
             ┌───────────────────────────┘                 └───────────────────────────┐
             ▼                                                                         ▼
┌───────────────────────────┐                                             ┌───────────────────────────┐
│     React 19 Dashboard    │                                             │      LLM Investigator     │
│  • Triage Queue           │                                             │  • Structured Evidence    │
│  • Graph Explorer         │◄───────────────────────────────────────────┤  • Lazy-Loaded Reports    │
│  • Case Details           │         (On-Demand Report API)              │  • Strict Schema Guard    │
└───────────────────────────┘                                             └───────────────────────────┘
```

---

## 📊 Benchmark & Benchmark Performance Results

Tested on a completely fresh, un-tuned, blind synthetic test dataset (`transactions_v5_independent.csv`):

### 1. Overall System Comparison

| System Paradigm | Precision | Recall | F1-Score | False Positives | False Negatives |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Random Forest Baseline** | 90.75% | 94.20% | 92.44% | 96 | 58 |
| **Graph Detector Alone** | 100.00% | 12.50% | 22.22% | 0 | 875 |
| 🛡️ **Sentinel Fusion System** | **99.78%** | **89.30%** | **94.25%** | **2** | 107 |

*Key Insight:* The Fusion Risk Engine suppressed **94 out of 96 false positives** generated by the Random Forest model during legitimate user onboarding waves and high-value transaction shifts.

---

### 2. Fraud Scenario Detection Breakdown

| Fraud Scenario | Random Forest ML | Graph Alone | 🛡️ Sentinel Fusion |
| :--- | :---: | :---: | :---: |
| **`INDIVIDUAL_FRAUD`** (Isolated high-velocity/stolen card) | 100.00% | 0.00% | **87.00%** |
| **`DEVICE_FARM`** (Botnets executing coordinated payments) | 100.00% | 100.00% | **100.00%** |
| **`CARD_CYCLING`** (Testing stolen cards across multiple users) | 96.00% | 0.00% | **95.20%** |
| **`ACCOUNT_BURST`** (Dormant account sudden activity burst) | 100.00% | 0.00% | **100.00%** |
| **`DISTRIBUTED_ABUSE`** (Stealth low-velocity distributed fraud) | 57.60% | 0.00% | **71.20%** |

---

### 3. Benign Network Stress Test

| Benign Network Scenario | Total Transactions | Flagged Transactions | False Positive Rate (FPR) |
| :--- | :---: | :---: | :---: |
| **`FAMILY_NETWORK`** (Shared family credit cards & devices) | 300 | 0 | **0.00%** |
| **`OFFICE_NETWORK`** (Corporate Wi-Fi IP shared by 80+ employees) | 800 | 0 | **0.00%** |
| **`HOSTEL_NETWORK`** (Student Wi-Fi IP shared by 50+ students) | 600 | 0 | **0.00%** |
| **`PUBLIC_WIFI_NETWORK`** (Cafe Wi-Fi shared with fraud user) | 500 | 0 | **0.00%** |
| **`LEGITIMATE_BUSINESS_NETWORK`** (B2B Supplier transactions) | 800 | 0 | **0.00%** |

---

## 📁 Repository Structure

```
Fraud Ring Sentinel/
├── api/                        # FastAPI REST API Backend
│   ├── main.py                 # FastAPI application, startup state, & REST routes
│   └── test_api.py             # TestClient suite for API endpoints
│
├── frontend/                   # React 19 + Vite Dashboard
│   ├── src/
│   │   ├── components/
│   │   │   ├── CaseQueue.jsx   # Analyst triage queue & risk filter table
│   │   │   ├── CaseDetail.jsx  # Multi-tab investigation case dashboard
│   │   │   ├── EntityGraph.jsx # Interactive 2-hop entity network visualization
│   │   │   └── Header.jsx     # Header banner & system stats indicator
│   │   ├── App.jsx             # Main view state & layout manager
│   │   └── index.css           # Styling system & dark-mode theme
│   ├── package.json
│   └── vite.config.js
│
├── ml/                         # Core Machine Learning & Graph Analysis Engine
│   ├── data/                   # Raw & generated dataset CSVs (v3, v5)
│   ├── evaluation/             # Independent benchmark & stress test scripts
│   │   └── final_independent_test_report.md
│   ├── generators/             # Synthetic payment network data generators
│   │   ├── generate_dataset_v3.py
│   │   └── generate_dataset_v5_independent.py
│   ├── graph/                  # Graph Construction & Fusion Risk Engine
│   │   ├── build_graph.py      # NetworkX heterogeneous graph builder
│   │   ├── detect_rings.py     # Candidate infrastructure cluster extractor
│   │   ├── fusion_risk.py      # Multi-dimensional Fusion Risk Engine & Suppressor
│   │   └── ring_risk.py        # Graph structural anomaly analyzer
│   ├── investigator/           # LLM Case Investigator & Evidence Adapter
│   │   ├── evidence_builder.py # Converts raw transaction/graph data to cases
│   │   ├── evidence_schema.py  # Pydantic-style evidence schemas
│   │   ├── llm_investigator.py # LLM Provider & Mock report generator
│   │   ├── report_schema.py    # Structured investigation report schema
│   │   └── validate_report.py  # Validation & guardrail enforcer
│   └── models/                 # Pre-trained ML models (Random Forest)
│       └── train_baseline.py   # Baseline model training script
│
├── test.py                     # Quick dataset inspector script
└── README.md                   # Project documentation
```

---

## ⚡ Quickstart Guide

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** and **npm**

---

### 1. Backend Setup & Run

1. Open terminal in the project root directory:
   ```bash
   cd "Fraud Ring Sentinel"
   ```

2. Install Python dependencies:
   ```bash
   pip install fastapi uvicorn pandas scikit-learn joblib networkx pydantic requests
   ```

3. Launch the FastAPI server:
   ```bash
   uvicorn api.main:app --reload --port 8000
   ```
   *The backend will initialize the transaction dataset, train/load the Random Forest model, build the NetworkX heterogeneous graph, and start the service at `http://127.0.0.1:8000`.*

---

### 2. Frontend Setup & Run

1. Open a new terminal in the `frontend/` directory:
   ```bash
   cd frontend
   ```

2. Install Node dependencies:
   ```bash
   npm install
   ```

3. Launch the Vite development server:
   ```bash
   npm run dev
   ```

4. Open your browser and navigate to `http://localhost:5173`.

---

## 🔌 API Endpoint Documentation

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | System health status and loaded case count |
| `GET` | `/api/cases` | Returns lightweight summary triage queue list. Supports `sort_by`, `order`, `risk_level`, and `action` query parameters |
| `GET` | `/api/cases/{case_id}` | Retrieves full `InvestigationCase` details and lazy-loads structured `InvestigationReport` |
| `GET` | `/api/cases/{case_id}/subgraph` | Returns 2-hop neighborhood nodes and edges for graph visualization with guardrail metadata |

### Sample API Request & Response

#### `GET /api/cases/CASE_1002/subgraph`
```json
{
  "case_id": "CASE_1002",
  "target_user_id": "USR_1002",
  "nodes": [
    { "id": "USER:USR_1002", "label": "USER:USR_1002", "type": "USER", "raw_id": "USR_1002", "is_seed": true },
    { "id": "DEVICE:DEV_9912", "label": "DEVICE:DEV_9912", "type": "DEVICE", "raw_id": "DEV_9912", "is_seed": false }
  ],
  "edges": [
    { "source": "USER:USR_1002", "target": "DEVICE:DEV_9912", "relation": "USED_DEVICE" }
  ],
  "metadata": {
    "statement": "GRAPH CONNECTION != FRAUD",
    "notice": "Shared infrastructure indicates topological relationship, not confirmed fraud."
  }
}
```

---

## 🧪 Running Tests & Evaluation Benchmarks

- **Run FastAPI Backend Tests:**
  ```bash
  python api/test_api.py
  ```

- **Run LLM Investigator Integration Tests:**
  ```bash
  python -m ml.investigator.test_pipeline_integration
  ```

- **Run V5 Independent Generalization Benchmark:**
  ```bash
  python -m ml.evaluation.evaluate_v5_independent
  ```

---

## 📄 License

This project is created for the **Razorpay AI Buildathon**. All rights reserved.
