"""
Sentinel — Coordinated Payment Abuse Intelligence
Module: Ring Detector (detect_rings.py)

Purpose:
Analyzes the heterogeneous NetworkX graph to discover candidate infrastructure clusters 
(connected components of users sharing hardware devices, cards, or IP addresses).

Important Design Principle:
Does NOT rely on ground truth scenario labels ('fraud_scenario') or hardcoded ID rules.
Discovers clusters dynamically using pure graph topology and aggregates behavioral
signals for downstream risk scoring.
"""

import networkx as nx
from typing import List, Dict, Any


def extract_candidate_clusters(G: nx.Graph) -> List[Dict[str, Any]]:
    """
    Identifies connected components of users sharing infrastructure (Devices, IPs, Cards).
    
    Args:
        G (nx.Graph): Heterogeneous graph built by build_graph.py.
        
    Returns:
        List[Dict[str, Any]]: List of cluster statistics dictionaries.
    """
    print("Analyzing graph topology to discover shared infrastructure components...")

    # Step 1: Find shared infrastructure entities (Device, IP, Card connected to >1 User)
    shared_entities = set()
    for node, attrs in G.nodes(data=True):
        ntype = attrs.get("node_type")
        if ntype in ["DEVICE", "IP", "CARD"]:
            # Count connected user neighbors
            user_neighbors = [
                nbr for nbr in G.neighbors(node) 
                if G.nodes[nbr].get("node_type") == "USER"
            ]
            if len(user_neighbors) > 1:
                shared_entities.add(node)

    # Step 2: Build a subgraph containing Users and Shared Infrastructure entities
    user_nodes = {node for node, attrs in G.nodes(data=True) if attrs.get("node_type") == "USER"}
    subgraph_nodes = user_nodes.union(shared_entities)
    subgraph = G.subgraph(subgraph_nodes)

    # Step 3: Find connected components in the shared infrastructure subgraph
    connected_components = list(nx.connected_components(subgraph))
    print(f"Discovered {len(connected_components)} raw connected infrastructure components.")

    candidate_clusters = []
    cluster_idx = 1

    for comp in connected_components:
        comp_nodes = set(comp)
        users = [n for n in comp_nodes if G.nodes[n].get("node_type") == "USER"]
        
        # Filter: Only process clusters with at least 2 users sharing infrastructure
        if len(users) < 2:
            continue

        devices = [n for n in comp_nodes if G.nodes[n].get("node_type") == "DEVICE"]
        ips = [n for n in comp_nodes if G.nodes[n].get("node_type") == "IP"]
        cards = [n for n in comp_nodes if G.nodes[n].get("node_type") == "CARD"]

        # Step 4: Gather all transactions associated with users in this component
        txn_nodes = set()
        for u in users:
            for nbr in G.neighbors(u):
                if G.nodes[nbr].get("node_type") == "TRANSACTION":
                    txn_nodes.add(nbr)

        merchants = set()
        for t in txn_nodes:
            for nbr in G.neighbors(t):
                if G.nodes[nbr].get("node_type") == "MERCHANT":
                    merchants.add(nbr)

        # Step 5: Calculate aggregate behavioral metrics across cluster transactions
        txn_data = [G.nodes[t] for t in txn_nodes]
        
        if not txn_data:
            continue

        total_txns = len(txn_data)
        avg_amount = sum(t["amount"] for t in txn_data) / total_txns
        avg_account_age = sum(t["account_age_days"] for t in txn_data) / total_txns
        avg_tx_hour = sum(t["transactions_last_hour"] for t in txn_data) / total_txns
        avg_tx_day = sum(t["transactions_last_day"] for t in txn_data) / total_txns
        avg_failed_tx = sum(t["failed_transactions"] for t in txn_data) / total_txns
        
        new_account_txns = sum(1 for t in txn_data if t["account_age_days"] <= 5)
        new_account_ratio = new_account_txns / total_txns

        # Merchant concentration (percentage of txns going to the single top merchant)
        merchant_counts = {}
        for t_node in txn_nodes:
            for nbr in G.neighbors(t_node):
                if G.nodes[nbr].get("node_type") == "MERCHANT":
                    m_id = G.nodes[nbr]["raw_id"]
                    merchant_counts[m_id] = merchant_counts.get(m_id, 0) + 1

        if merchant_counts:
            top_merchant_id, top_merchant_cnt = max(merchant_counts.items(), key=lambda x: x[1])
            merchant_concentration = top_merchant_cnt / total_txns
        else:
            top_merchant_id = None
            merchant_concentration = 0.0

        # Ground truth scenario tracking (RETAINED ONLY FOR POST-DETECTION EVALUATION)
        ground_truth_scenarios = {}
        for t in txn_data:
            sc = t.get("fraud_scenario", "NONE")
            ground_truth_scenarios[sc] = ground_truth_scenarios.get(sc, 0) + 1

        cluster_summary = {
            "candidate_id": f"CANDIDATE_{cluster_idx:03d}",
            "users": users,
            "devices": devices,
            "ips": ips,
            "cards": cards,
            "transaction_nodes": list(txn_nodes),
            "merchants": list(merchants),
            "user_count": len(users),
            "device_count": len(devices),
            "ip_count": len(ips),
            "card_count": len(cards),
            "transaction_count": total_txns,
            "merchant_count": len(merchants),
            "avg_amount": avg_amount,
            "avg_account_age": avg_account_age,
            "avg_tx_hour": avg_tx_hour,
            "avg_tx_day": avg_tx_day,
            "avg_failed_tx": avg_failed_tx,
            "new_account_ratio": new_account_ratio,
            "top_merchant_id": top_merchant_id,
            "merchant_concentration": merchant_concentration,
            "ground_truth_scenarios": ground_truth_scenarios
        }
        candidate_clusters.append(cluster_summary)
        cluster_idx += 1

    print(f"Extracted {len(candidate_clusters)} multi-user infrastructure candidate clusters.")
    return candidate_clusters
