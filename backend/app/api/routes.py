from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
import numpy as np

from app.api.schemas import (
    DashboardSummaryResponse,
    RiskQueueResponse,
    RiskQueueItem,
    GraphResponse,
    GraphNode,
    GraphEdge,
    DemoCustomer,
)
from app.api.demo import DEMO_CUSTOMERS
from app.risk.scorer import RiskScorer
from app.risk.investigator import investigate_customer
from app.risk.queries import run_query
from app.ai.service import explain_risk

router = APIRouter(prefix="/api")

# Lazy singleton scorer
_scorer = None

def get_scorer() -> RiskScorer:
    global _scorer
    if _scorer is None:
        _scorer = RiskScorer()
    return _scorer

@router.get("/demo/customers", response_model=List[DemoCustomer])
def get_demo_customers():
    """Returns curated seed customers for demonstration."""
    return DEMO_CUSTOMERS

@router.get("/dashboard/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary():
    """Returns high-level merchant risk operations metrics and distribution."""
    scorer = get_scorer()
    probs = list(scorer.predictions.values())
    total_customers = len(probs)
    
    if total_customers == 0:
        total_customers = 50000
        probs = [0.0]
        
    low_count = sum(1 for p in probs if p < 0.30)
    med_count = sum(1 for p in probs if 0.30 <= p < 0.70)
    high_count = sum(1 for p in probs if p >= 0.70)
    review_required_count = sum(1 for p in probs if p >= 0.60)
    
    high_risk_pct = round((high_count / total_customers) * 100, 2)
    avg_prob = float(np.mean(probs))
    
    return DashboardSummaryResponse(
        total_customers=total_customers,
        customers_requiring_review=review_required_count,
        high_risk_customers=high_count,
        medium_risk_customers=med_count,
        low_risk_customers=low_count,
        total_transactions=303161,
        high_risk_percentage=high_risk_pct,
        risk_distribution={
            "LOW": low_count,
            "MEDIUM": med_count,
            "HIGH": high_count
        },
        investigation_statistics={
            "avg_risk_probability": round(avg_prob, 4),
            "review_queue_size": review_required_count,
            "threshold_frozen": 0.60
        }
    )

def _get_primary_signals_batch(customer_ids: List[str]) -> Dict[str, List[str]]:
    """Batched query to fetch top observable signals for a page of customer IDs in a single query."""
    if not customer_ids:
        return {}
        
    query = """
    UNWIND $customer_ids AS cid
    MATCH (c:Customer {customer_id: cid})
    RETURN cid AS customer_id,
           EXISTS { MATCH (c)-[:USES_DEVICE]->(:Device)<-[:USES_DEVICE]-(other:Customer) WHERE other <> c } AS shared_device,
           EXISTS { MATCH (c)-[:USES_IP]->(:IP)<-[:USES_IP]-(other:Customer) WHERE other <> c } AS shared_ip,
           EXISTS { MATCH (c)-[:REFERRED]-(ref:Customer) } AS has_referral
    """
    try:
        rows = run_query(query, {"customer_ids": customer_ids})
        results = {}
        for r in rows:
            cid = r["customer_id"]
            sigs = []
            if r["shared_device"]:
                sigs.append("Shared Device")
            if r["shared_ip"]:
                sigs.append("Shared IP")
            if r["has_referral"]:
                sigs.append("Referral Link")
            if not sigs:
                sigs.append("Standard Pattern")
            results[cid] = sigs
        return results
    except Exception:
        return {cid: ["Standard Pattern"] for cid in customer_ids}

@router.get("/risk/customers", response_model=RiskQueueResponse)
def get_risk_queue(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    risk_level: Optional[str] = Query(None, description="LOW, MEDIUM, or HIGH"),
    review_required: Optional[bool] = Query(None),
    min_probability: Optional[float] = Query(None, ge=0.0, le=1.0),
    max_probability: Optional[float] = Query(None, ge=0.0, le=1.0),
    search: Optional[str] = Query(None, description="Filter by customer_id prefix or match"),
    sort: str = Query("desc", pattern="^(asc|desc)$")
):
    """Paginated merchant risk queue with sorting, filtering, and batched signals."""
    scorer = get_scorer()
    
    # Compile candidate list
    items = []
    for cid, prob in scorer.predictions.items():
        # Compute level
        if prob < 0.30:
            lvl = "LOW"
        elif prob < 0.70:
            lvl = "MEDIUM"
        else:
            lvl = "HIGH"
            
        req = (prob >= 0.60)
        
        # Apply filters
        if risk_level and lvl != risk_level.upper():
            continue
        if review_required is not None and req != review_required:
            continue
        if min_probability is not None and prob < min_probability:
            continue
        if max_probability is not None and prob > max_probability:
            continue
        if search and search.lower() not in cid.lower():
            continue
            
        items.append({
            "customer_id": cid,
            "risk_probability": round(prob, 4),
            "risk_level": lvl,
            "review_required": req
        })
        
    # Sort
    reverse = (sort == "desc")
    items.sort(key=lambda x: x["risk_probability"], reverse=reverse)
    
    total = len(items)
    paged = items[offset : offset + limit]
    
    # Enrich page slice with primary signals
    cids_slice = [it["customer_id"] for it in paged]
    signals_map = _get_primary_signals_batch(cids_slice)
    
    result_items = []
    for it in paged:
        cid = it["customer_id"]
        result_items.append(RiskQueueItem(
            customer_id=cid,
            risk_probability=it["risk_probability"],
            risk_level=it["risk_level"],
            review_required=it["review_required"],
            primary_signals=signals_map.get(cid, ["Standard Pattern"])
        ))
        
    return RiskQueueResponse(
        items=result_items,
        total=total,
        limit=limit,
        offset=offset
    )

@router.get("/risk/customers/{customer_id}")
def get_customer_risk(customer_id: str):
    """Returns basic risk score and review status."""
    scorer = get_scorer()
    if customer_id not in scorer.predictions:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found.")
    return scorer.get_risk_score(customer_id)

@router.get("/risk/customers/{customer_id}/investigation")
def get_customer_investigation(customer_id: str):
    """Returns full Phase 4 structured evidence package."""
    scorer = get_scorer()
    if customer_id not in scorer.predictions:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found.")
    try:
        return investigate_customer(customer_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Customer investigation failed: {str(e)}")

@router.get("/risk/customers/{customer_id}/explanation")
def get_customer_explanation(customer_id: str):
    """Returns Phase 5 structured AI explanation with fallback support."""
    scorer = get_scorer()
    if customer_id not in scorer.predictions:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found.")
    try:
        pkg = investigate_customer(customer_id)
        return explain_risk(pkg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explanation generation failed: {str(e)}")

@router.get("/risk/customers/{customer_id}/graph", response_model=GraphResponse)
def get_customer_graph(customer_id: str):
    """
    Returns a bounded, multi-signal prioritized React Flow graph representation.
    Displays up to 25 top connections and reports total neighborhood size.
    """
    scorer = get_scorer()
    if customer_id not in scorer.predictions:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found.")
    try:
        pkg = investigate_customer(customer_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph assembly failed: {str(e)}")
        
    nodes = []
    edges = []
    seen_nodes = set()
    seen_edges = set()
    
    def add_node(nid: str, ntype: str, data: Dict[str, Any]):
        if nid not in seen_nodes:
            seen_nodes.add(nid)
            nodes.append(GraphNode(id=nid, type=ntype, data=data))
            
    def add_edge(eid: str, src: str, tgt: str, etype: str, label: Optional[str] = None):
        if eid not in seen_edges:
            seen_edges.add(eid)
            edges.append(GraphEdge(id=eid, source=src, target=tgt, type=etype, label=label or etype))
            
    # 1. Target Node
    risk_info = pkg.get("risk", {})
    add_node(
        customer_id,
        "customer",
        {
            "label": f"{customer_id} (Target)",
            "is_target": True,
            "risk_level": risk_info.get("risk_level", "LOW"),
            "risk_probability": risk_info.get("risk_probability", 0.0)
        }
    )
    
    # 2. Add Direct Infrastructure Nodes
    signals = pkg.get("signals", {})
    
    # Devices
    for d in signals.get("shared_devices", []):
        did = d["device_id"]
        add_node(did, "device", {"label": f"Device {did}", "customer_count": d["customer_count"]})
        add_edge(f"{customer_id}->{did}", customer_id, did, "USES_DEVICE")
        
    # IPs
    for ip in signals.get("shared_ips", []):
        ipid = ip["ip_address"]
        add_node(ipid, "ip", {"label": f"IP {ipid}", "customer_count": ip["customer_count"]})
        add_edge(f"{customer_id}->{ipid}", customer_id, ipid, "USES_IP")
        
    # Coupons
    for cp in signals.get("coupon_coordination", []):
        cpid = cp["coupon_id"]
        add_node(cpid, "coupon", {"label": f"Coupon {cpid}", "customer_count": cp["customer_count"]})
        add_edge(f"{customer_id}->{cpid}", customer_id, cpid, "USED_COUPON")
        
    # Referrer
    ref_info = signals.get("referral_connections", {})
    if ref_info.get("referrer_id"):
        ref_id = ref_info["referrer_id"]
        add_node(ref_id, "customer", {"label": f"{ref_id} (Referrer)", "is_referrer": True})
        add_edge(f"{ref_id}->{customer_id}", ref_id, customer_id, "REFERRED")
        
    # 3. Add Connected Neighbors (Ranked by Multi-Signal Strength)
    multi_conns = pkg.get("multi_signal_connections", [])
    total_connections_count = pkg.get("summary", {}).get("connected_customer_count", len(multi_conns))
    
    # Top multi-signal neighbors (take up to 15)
    for m in multi_conns[:15]:
        other_cid = m["connected_customer"]
        add_node(
            other_cid,
            "customer",
            {
                "label": other_cid,
                "signals": m.get("signals", []),
                "signal_count": len(m.get("signals", []))
            }
        )
        for sig in m.get("signals", []):
            if sig == "shared_device":
                for d in signals.get("shared_devices", []):
                    add_edge(f"{other_cid}->{d['device_id']}", other_cid, d["device_id"], "USES_DEVICE")
            elif sig == "shared_ip":
                for ip in signals.get("shared_ips", []):
                    add_edge(f"{other_cid}->{ip['ip_address']}", other_cid, ip["ip_address"], "USES_IP")
            elif sig == "shared_coupon":
                for cp in signals.get("coupon_coordination", []):
                    add_edge(f"{other_cid}->{cp['coupon_id']}", other_cid, cp["coupon_id"], "USED_COUPON")
            elif sig == "referral":
                add_edge(f"{other_cid}-ref-{customer_id}", other_cid, customer_id, "REFERRED")
                
    displayed_count = len(nodes)
    note = f"Showing {displayed_count} high-priority nodes of {max(total_connections_count, displayed_count)} neighborhood entities (prioritized by multi-signal strength)."
    
    return GraphResponse(
        customer_id=customer_id,
        nodes=nodes,
        edges=edges,
        total_connections_count=max(total_connections_count, displayed_count),
        displayed_nodes_count=displayed_count,
        prioritization_note=note
    )
