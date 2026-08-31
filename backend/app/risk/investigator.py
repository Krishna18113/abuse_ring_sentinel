from typing import Dict, Any, List
from app.risk.scorer import RiskScorer
from app.risk.queries import (
    query_basic_behavior,
    query_shared_devices,
    query_shared_ips,
    query_coupon_coordination,
    query_referrals,
    query_multi_signal_connections,
    query_temporal_coordination
)
from app.risk.evidence import compile_strengths
from app.risk.models import EvidencePackage

# Lazy scorer initialization
_scorer = None

def get_scorer():
    global _scorer
    if _scorer is None:
        _scorer = RiskScorer()
    return _scorer

def investigate_customer(customer_id: str) -> dict:
    """Orchestrates probabilistic GNN scoring and Neo4j deterministic graph queries 
    to compile a comprehensive, stable evidence package for a given customer."""
    
    # 1. Probabilistic GNN score
    score_info = get_scorer().get_risk_score(customer_id)
    
    # 2. Neo4j dynamic neighborhood queries
    behavior = query_basic_behavior(customer_id)
    raw_devices = query_shared_devices(customer_id)
    raw_ips = query_shared_ips(customer_id)
    raw_coupons = query_coupon_coordination(customer_id)
    referral_connections = query_referrals(customer_id)
    raw_multi = query_multi_signal_connections(customer_id)
    raw_temporal = query_temporal_coordination(customer_id)
    
    # 3. Process Signals
    # Shared Devices
    shared_devices = []
    for d in raw_devices:
        shared_devices.append({
            "device_id": d["device_id"],
            "customer_count": d["customer_count"],
            "connected_customers": d["connected_customers"],
            "transaction_count": d["transaction_count"]
        })
        
    # Shared IPs
    shared_ips = []
    for ip in raw_ips:
        shared_ips.append({
            "ip_address": ip["ip_address"],
            "customer_count": ip["customer_count"],
            "connected_customers": ip["connected_customers"],
            "transaction_count": ip["transaction_count"]
        })
        
    # Coupon Coordination
    coupon_coordination = []
    for c in raw_coupons:
        coupon_coordination.append({
            "coupon_id": c["coupon_id"],
            "customer_count": c["customer_count"],
            "connected_customers": c["connected_customers"],
            "shared_device_count": c["shared_device_count"],
            "shared_ip_count": c["shared_ip_count"]
        })
        
    # Multi-signal Connections (A customer is connected if signal_count >= 1)
    multi_signal_connections = []
    unique_connected_custs = set()
    
    for row in raw_multi:
        conn_cust = row["connected_customer"]
        signals = []
        if row["shared_devices"]:
            signals.append("shared_device")
        if row["shared_ips"]:
            signals.append("shared_ip")
        if row["has_referral"]:
            signals.append("referral")
        if row["shared_coupons"]:
            signals.append("shared_coupon")
            
        if signals:
            unique_connected_custs.add(conn_cust)
            multi_signal_connections.append({
                "connected_customer": conn_cust,
                "signals": signals,
                "signal_count": len(signals)
            })
            
    # Sort multi-signal connections by signal count descending to prioritize highly coordinated nodes
    multi_signal_connections = sorted(
        multi_signal_connections, key=lambda x: x["signal_count"], reverse=True
    )
    
    # Temporal Clusters
    # Group pairs into 60s, 5m (300s), and 15m (900s) windows without double-counting transactions
    temporal_clusters = []
    for window in [60, 300, 900]:
        w_pairs = [p for p in raw_temporal if p["time_diff"] <= window]
        if not w_pairs:
            continue
            
        unique_txs = {}
        for p in w_pairs:
            unique_txs[p["target_tx_id"]] = {
                "customer_id": customer_id,
                "transaction_id": p["target_tx_id"],
                "timestamp": p["target_tx_time"],
                "amount": p["target_tx_amount"]
            }
            unique_txs[p["other_tx_id"]] = {
                "customer_id": p["connected_customer"],
                "transaction_id": p["other_tx_id"],
                "timestamp": p["other_tx_time"],
                "amount": p["other_tx_amount"]
            }
            
        tx_list = list(unique_txs.values())
        custs_involved = {tx["customer_id"] for tx in tx_list}
        total_amount = sum(tx["amount"] for tx in tx_list)
        
        temporal_clusters.append({
            "time_window_seconds": window,
            "customer_count": len(custs_involved),
            "transaction_count": len(tx_list),
            "total_amount": round(total_amount, 2),
            "transactions": [
                {
                    "customer_id": t["customer_id"],
                    "transaction_id": t["transaction_id"],
                    "timestamp": t["timestamp"]
                } for t in tx_list
            ]
        })
        
    # Assemble signals dictionary
    signals = {
        "shared_devices": shared_devices,
        "shared_ips": shared_ips,
        "coupon_coordination": coupon_coordination,
        "referral_connections": referral_connections,
        "temporal_clusters": temporal_clusters
    }
    
    # 4. Evaluate evidence strengths
    strengths = compile_strengths(signals)
    
    # 5. Summary metrics
    # Count of active signals (strength LOW, MEDIUM, or HIGH)
    detected_signals_count = sum(1 for s in strengths.values() if s["detected"])
    
    summary = {
        "signal_count": detected_signals_count,
        "connected_customer_count": len(unique_connected_custs),
        "temporal_cluster_count": len(temporal_clusters)
    }
    
    # Assemble package and validate against Pydantic schema
    pkg = {
        "customer": {"customer_id": customer_id},
        "risk": score_info,
        "behavior": behavior,
        "signals": signals,
        "multi_signal_connections": multi_signal_connections,
        "summary": summary,
        "strengths": strengths
    }
    
    # Validation step to ensure schema stability
    validated_pkg = EvidencePackage(**pkg)
    return validated_pkg.model_dump()
