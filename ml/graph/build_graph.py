"""
Sentinel — Coordinated Payment Abuse Intelligence
Module: Graph Builder (build_graph.py)

Purpose:
Loads payment transaction data from CSV and constructs a heterogeneous network graph
using NetworkX.

Node Taxonomy:
- USER:<user_id>               (User entity)
- DEVICE:<device_id>           (Hardware device entity)
- IP:<ip_id>                   (IP address entity)
- CARD:<card_id>               (Payment card entity)
- MERCHANT:<merchant_id>       (Merchant entity)
- TRANSACTION:<transaction_id> (Specific transaction instance)

Edge Relationships:
- (USER, DEVICE)       relation="USES"
- (USER, IP)           relation="USES"
- (USER, CARD)         relation="USES"
- (USER, TRANSACTION)  relation="MADE"
- (TRANSACTION, MERCHANT) relation="PAID_TO"
- (TRANSACTION, DEVICE) relation="USED_DEVICE"
- (TRANSACTION, IP)     relation="USED_IP"
- (TRANSACTION, CARD)   relation="USED_CARD"
"""

import os
import networkx as nx
import pandas as pd


def build_heterogeneous_graph(df: pd.DataFrame) -> nx.Graph:
    """
    Constructs a heterogeneous NetworkX Graph from a DataFrame of transactions.
    
    Args:
        df (pd.DataFrame): DataFrame containing payment transaction records.
        
    Returns:
        nx.Graph: Multi-entity heterogeneous network graph.
    """
    G = nx.Graph()

    print(f"Building heterogeneous graph from {len(df)} transaction records...")

    for idx, row in df.iterrows():
        txn_id_str = str(row["transaction_id"])
        user_id_str = str(row["user_id"])
        device_id_str = str(row["device_id"])
        ip_id_str = str(row["ip_id"])
        card_id_str = str(row["card_id"])
        merchant_id_str = str(row["merchant_id"])

        # Construct prefixed Node IDs to guarantee no ID collisions across types
        u_node = f"USER:{user_id_str}"
        d_node = f"DEVICE:{device_id_str}"
        ip_node = f"IP:{ip_id_str}"
        c_node = f"CARD:{card_id_str}"
        m_node = f"MERCHANT:{merchant_id_str}"
        t_node = f"TRANSACTION:{txn_id_str}"

        # ----------------------------------------------------------------------
        # Add Nodes with Type Attributes and Properties
        # ----------------------------------------------------------------------
        G.add_node(u_node, node_type="USER", raw_id=user_id_str)
        G.add_node(d_node, node_type="DEVICE", raw_id=device_id_str)
        G.add_node(ip_node, node_type="IP", raw_id=ip_id_str)
        G.add_node(c_node, node_type="CARD", raw_id=card_id_str)
        G.add_node(m_node, node_type="MERCHANT", raw_id=merchant_id_str)

        # Store transaction metadata on transaction node
        # Note: is_fraud and fraud_scenario are retained ONLY for evaluation purposes
        G.add_node(
            t_node,
            node_type="TRANSACTION",
            raw_id=txn_id_str,
            amount=float(row["amount"]),
            account_age_days=int(row["account_age_days"]),
            transactions_last_hour=int(row["transactions_last_hour"]),
            transactions_last_day=int(row["transactions_last_day"]),
            failed_transactions=int(row["failed_transactions"]),
            unique_devices=int(row["unique_devices"]),
            unique_cards=int(row["unique_cards"]),
            is_fraud=int(row["is_fraud"]),
            fraud_scenario=str(row["fraud_scenario"])
        )

        # ----------------------------------------------------------------------
        # Add Edges (Relationships)
        # ----------------------------------------------------------------------
        # User -> Infrastructure linkages
        G.add_edge(u_node, d_node, relation="USES")
        G.add_edge(u_node, ip_node, relation="USES")
        G.add_edge(u_node, c_node, relation="USES")
        G.add_edge(u_node, t_node, relation="MADE")

        # Transaction -> Infrastructure linkages
        G.add_edge(t_node, m_node, relation="PAID_TO")
        G.add_edge(t_node, d_node, relation="USED_DEVICE")
        G.add_edge(t_node, ip_node, relation="USED_IP")
        G.add_edge(t_node, c_node, relation="USED_CARD")

    print(f"Graph construction complete: {G.number_of_nodes()} total nodes, {G.number_of_edges()} total edges.")
    return G


def load_graph_from_csv(csv_path: str) -> nx.Graph:
    """
    Helper function to load CSV from path and return constructed graph.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Transaction CSV not found at: {csv_path}")
    df = pd.read_csv(csv_path)
    return build_heterogeneous_graph(df)


if __name__ == "__main__":
    # Test script directly
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
    default_csv = os.path.join(project_root, "ml", "data", "raw", "transactions.csv")
    
    graph = load_graph_from_csv(default_csv)
    
    # Print node count summary by type
    counts = {}
    for node, attrs in graph.nodes(data=True):
        ntype = attrs.get("node_type", "UNKNOWN")
        counts[ntype] = counts.get(ntype, 0) + 1
        
    print("\nNode Counts by Type:")
    for ntype, count in sorted(counts.items()):
        print(f"  • {ntype:12s}: {count}")
