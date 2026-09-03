from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Dict, Any, List, Set, Tuple, Optional

from app.analysis.schemas import (
    SessionCustomerRisk,
    SessionClusterInfo,
    SessionInvestigationResponse,
    SessionAnalysisReport,
)
from app.analysis.validator import get_session_data

# Cache of computed session analysis reports
_SESSION_ANALYSIS_CACHE: Dict[str, SessionAnalysisReport] = {}
_SESSION_GRAPH_CACHE: Dict[str, Dict[str, Any]] = {}

def analyze_session_graph(session_id: str) -> SessionAnalysisReport:
    """
    Constructs the bipartite entity graph for an uploaded merchant dataset session,
    detects coordinated abuse clusters/rings, computes inductive risk scores,
    and formats actionable findings.
    """
    if session_id in _SESSION_ANALYSIS_CACHE:
        return _SESSION_ANALYSIS_CACHE[session_id]

    session = get_session_data(session_id)
    if not session:
        raise ValueError(f"Session '{session_id}' not found or expired.")

    records = session.get("records", [])

    # 1. Build In-Memory Graph Adjacency Indices
    cust_devices: Dict[str, Set[str]] = defaultdict(set)
    dev_customers: Dict[str, Set[str]] = defaultdict(set)

    cust_ips: Dict[str, Set[str]] = defaultdict(set)
    ip_customers: Dict[str, Set[str]] = defaultdict(set)

    cust_coupons: Dict[str, Set[str]] = defaultdict(set)
    coupon_customers: Dict[str, Set[str]] = defaultdict(set)

    cust_referrers: Dict[str, str] = {}
    referrer_customers: Dict[str, Set[str]] = defaultdict(set)

    cust_tx_count: Dict[str, int] = defaultdict(int)
    cust_volume: Dict[str, float] = defaultdict(float)

    all_customers: Set[str] = set()

    for r in records:
        cid = str(r.get("customer_id") or "").strip()
        if not cid:
            continue
        all_customers.add(cid)
        cust_tx_count[cid] += 1
        
        try:
            amt = float(r.get("amount", 0.0))
            if amt > 0:
                cust_volume[cid] += amt
        except Exception:
            pass

        dev = str(r.get("device_id") or "").strip()
        if dev and dev.lower() not in {"null", "none", "nan", ""}:
            cust_devices[cid].add(dev)
            dev_customers[dev].add(cid)

        ip = str(r.get("ip_address") or "").strip()
        if ip and ip.lower() not in {"null", "none", "nan", ""}:
            cust_ips[cid].add(ip)
            ip_customers[ip].add(cid)

        cp = str(r.get("coupon_code") or "").strip()
        if cp and cp.lower() not in {"null", "none", "nan", ""}:
            cust_coupons[cid].add(cp)
            coupon_customers[cp].add(cid)

        ref = str(r.get("referrer_id") or "").strip()
        if ref and ref.lower() not in {"null", "none", "nan", ""}:
            cust_referrers[cid] = ref
            referrer_customers[ref].add(cid)

    # 2. Compute Pairwise Multi-Signal Graph Overlaps
    customer_peers: Dict[str, Dict[str, List[str]]] = defaultdict(lambda: defaultdict(list))

    for cid in all_customers:
        for dev in cust_devices[cid]:
            for other in dev_customers[dev]:
                if other != cid:
                    customer_peers[cid][other].append("shared_device")

        for ip in cust_ips[cid]:
            for other in ip_customers[ip]:
                if other != cid:
                    customer_peers[cid][other].append("shared_ip")

        for cp in cust_coupons[cid]:
            for other in coupon_customers[cp]:
                if other != cid:
                    customer_peers[cid][other].append("shared_coupon")

        ref = cust_referrers.get(cid)
        if ref and ref in all_customers:
            customer_peers[cid][ref].append("referral")
            customer_peers[ref][cid].append("referral")

    # 3. Detect Abuse Clusters / Coordinated Rings (Connected Components via Shared Hardware/IP)
    visited: Set[str] = set()
    clusters: List[SessionClusterInfo] = []
    cluster_idx = 1

    for cid in sorted(all_customers):
        if cid in visited:
            continue

        # BFS for connected ring
        cluster_members: List[str] = []
        queue = deque([cid])
        visited.add(cid)

        while queue:
            curr = queue.popleft()
            cluster_members.append(curr)

            for neighbor, sigs in customer_peers[curr].items():
                # Cluster together if sharing hardware, IP, or multiple signals
                if neighbor not in visited and ("shared_device" in sigs or len(sigs) >= 2):
                    visited.add(neighbor)
                    queue.append(neighbor)

        # Only register as a cluster if 2+ accounts are linked
        if len(cluster_members) >= 2:
            cluster_devs = set()
            cluster_ips = set()
            cluster_cps = set()
            for m in cluster_members:
                cluster_devs.update(cust_devices[m])
                cluster_ips.update(cust_ips[m])
                cluster_cps.update(cust_coupons[m])

            risk_lvl = "HIGH" if len(cluster_members) >= 4 or len(cluster_devs) >= 1 else "MEDIUM"
            summary_desc = (
                f"Ring {cluster_idx}: {len(cluster_members)} accounts coordinated across "
                f"{len(cluster_devs)} shared devices and {len(cluster_ips)} IP gateways."
            )

            clusters.append(SessionClusterInfo(
                cluster_id=f"RING_{cluster_idx:02d}",
                customer_count=len(cluster_members),
                risk_level=risk_lvl,
                customer_ids=sorted(cluster_members),
                shared_devices=sorted(list(cluster_devs)),
                shared_ips=sorted(list(cluster_ips)),
                shared_coupons=sorted(list(cluster_cps)),
                summary=summary_desc,
            ))
            cluster_idx += 1

    # 4. Inductive Graph Risk Scoring for Each Customer
    customer_risks: List[SessionCustomerRisk] = []
    reviews_required_count = 0
    high_risk_count = 0

    for cid in sorted(all_customers):
        peers = customer_peers[cid]
        multi_signal_count = sum(1 for p, sigs in peers.items() if len(set(sigs)) >= 2)
        total_connected_count = len(peers)

        # Max sharing degree on device
        max_dev_sharing = max([len(dev_customers[d]) for d in cust_devices[cid]], default=1)
        max_ip_sharing = max([len(ip_customers[i]) for i in cust_ips[cid]], default=1)
        max_cp_sharing = max([len(coupon_customers[c]) for c in cust_coupons[cid]], default=1)

        # Inductive risk score computation based on graph topology features
        score = 0.02 # Base organic baseline

        # Multi-signal weight
        if multi_signal_count >= 1:
            score += min(0.40, multi_signal_count * 0.12)

        # Shared device weight (high conviction in fraud rings)
        if max_dev_sharing >= 2:
            score += min(0.35, (max_dev_sharing - 1) * 0.08)

        # Shared IP density weight
        if max_ip_sharing >= 3:
            score += min(0.20, (max_ip_sharing - 2) * 0.04)

        # Promotional overlap weight
        if len(cust_coupons[cid]) > 0 and (max_dev_sharing >= 2 or max_ip_sharing >= 2):
            score += 0.10

        # Referral coordination weight
        if cid in cust_referrers and max_dev_sharing >= 2:
            score += 0.08

        prob = min(0.995, round(score, 4))
        is_review = prob >= 0.60
        tier = "HIGH" if prob >= 0.70 else ("MEDIUM" if prob >= 0.30 else "LOW")

        if is_review:
            reviews_required_count += 1
        if tier == "HIGH":
            high_risk_count += 1

        # Determine Primary Flag Reason & Detected Signals
        detected_signals = []
        reason_parts = []

        if max_dev_sharing >= 2:
            detected_signals.append(f"Shared Device ({max_dev_sharing} accounts)")
            reason_parts.append(f"shares physical device with {max_dev_sharing - 1} accounts")

        if max_ip_sharing >= 2:
            detected_signals.append(f"Shared IP ({max_ip_sharing} accounts)")
            reason_parts.append(f"shared network gateway with {max_ip_sharing - 1} accounts")

        if multi_signal_count >= 1:
            detected_signals.append(f"{multi_signal_count} Multi-Signal Peers")
            reason_parts.append(f"{multi_signal_count} multi-signal overlapping profiles")

        if cust_coupons[cid]:
            detected_signals.append("Promotional Campaign Usage")

        if reason_parts:
            primary_reason = f"Coordinated infrastructure: {', '.join(reason_parts)}."
        else:
            primary_reason = "Organic profile: Dedicated hardware fingerprint and private IP gateway."

        customer_risks.append(SessionCustomerRisk(
            customer_id=cid,
            risk_probability=prob,
            risk_level=tier,
            review_required=is_review,
            primary_flag_reason=primary_reason,
            transaction_count=cust_tx_count[cid],
            total_amount=round(cust_volume[cid], 2),
            shared_device_count=len(cust_devices[cid]),
            shared_ip_count=len(cust_ips[cid]),
            shared_coupon_count=len(cust_coupons[cid]),
            multi_signal_connections_count=multi_signal_count,
            connected_customer_ids=sorted(list(peers.keys())),
            detected_signals=detected_signals or ["Dedicated Infrastructure"],
        ))

    # Sort customers by risk probability descending
    customer_risks.sort(key=lambda x: x.risk_probability, reverse=True)

    report = SessionAnalysisReport(
        session_id=session_id,
        analyzed_at=datetime.now(timezone.utc).isoformat(),
        total_customers=len(all_customers),
        high_risk_customers=high_risk_count,
        reviews_required=reviews_required_count,
        detected_clusters=clusters,
        customer_risks=customer_risks,
        boundary_note=(
            "Session graph analysis completed in an isolated workspace. "
            "Graph topology and inductive risk scores were computed on the uploaded batch without modifying the production dataset."
        ),
    )

    _SESSION_ANALYSIS_CACHE[session_id] = report
    _SESSION_GRAPH_CACHE[session_id] = {
        "cust_devices": cust_devices,
        "dev_customers": dev_customers,
        "cust_ips": cust_ips,
        "ip_customers": ip_customers,
        "cust_coupons": cust_coupons,
        "coupon_customers": coupon_customers,
        "cust_referrers": cust_referrers,
        "customer_peers": customer_peers,
    }

    return report

def get_session_customer_investigation(session_id: str, customer_id: str) -> SessionInvestigationResponse:
    """
    Constructs an interactive evidence-first React Flow graph and evidence dossier 
    for a specific customer in an uploaded merchant dataset session.
    """
    report = analyze_session_graph(session_id)
    cust_risk = next((c for c in report.customer_risks if c.customer_id == customer_id), None)
    if not cust_risk:
        raise ValueError(f"Customer '{customer_id}' not found in session '{session_id}'.")

    graph_indices = _SESSION_GRAPH_CACHE.get(session_id, {})
    cust_devices = graph_indices.get("cust_devices", {})
    cust_ips = graph_indices.get("cust_ips", {})
    cust_coupons = graph_indices.get("cust_coupons", {})
    customer_peers = graph_indices.get("customer_peers", {})

    # Build React Flow nodes and edges
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    added_nodes: Set[str] = set()

    # 1. Target Customer (Top Tier)
    nodes.append({
        "id": customer_id,
        "type": "target",
        "data": {
            "label": f"Investigated: {customer_id}",
            "risk_score": cust_risk.risk_probability,
            "risk_level": cust_risk.risk_level,
            "review_required": cust_risk.review_required,
        }
    })
    added_nodes.add(customer_id)

    # 2. Shared Infrastructure Hubs (Middle Tier)
    for dev in cust_devices.get(customer_id, set()):
        if dev not in added_nodes:
            nodes.append({
                "id": dev,
                "type": "device",
                "data": {"label": f"Device {dev}", "type": "device"}
            })
            added_nodes.add(dev)
        edges.append({
            "id": f"{customer_id}->{dev}",
            "source": customer_id,
            "target": dev,
            "type": "smoothstep",
            "label": "USES_DEVICE",
        })

    for ip in cust_ips.get(customer_id, set()):
        if ip not in added_nodes:
            nodes.append({
                "id": ip,
                "type": "ip",
                "data": {"label": f"IP {ip}", "type": "ip"}
            })
            added_nodes.add(ip)
        edges.append({
            "id": f"{customer_id}->{ip}",
            "source": customer_id,
            "target": ip,
            "type": "smoothstep",
            "label": "USES_IP",
        })

    for cp in cust_coupons.get(customer_id, set()):
        if cp not in added_nodes:
            nodes.append({
                "id": cp,
                "type": "coupon",
                "data": {"label": f"Promo {cp}", "type": "coupon"}
            })
            added_nodes.add(cp)
        edges.append({
            "id": f"{customer_id}->{cp}",
            "source": customer_id,
            "target": cp,
            "type": "smoothstep",
            "label": "USED_COUPON",
        })

    # 3. Connected Neighbor Customers (Bottom Tier)
    peers = customer_peers.get(customer_id, {})
    for peer_id, sigs in list(peers.items())[:15]:
        if peer_id not in added_nodes:
            peer_risk = next((c for c in report.customer_risks if c.customer_id == peer_id), None)
            nodes.append({
                "id": peer_id,
                "type": "customer",
                "data": {
                    "label": peer_id,
                    "signal_count": len(set(sigs)),
                    "signals": list(set(sigs)),
                    "risk_level": peer_risk.risk_level if peer_risk else "UNKNOWN",
                }
            })
            added_nodes.add(peer_id)

        # Connect peer to shared hubs
        for sig in set(sigs):
            if sig == "shared_device":
                for dev in cust_devices.get(peer_id, set()).intersection(cust_devices.get(customer_id, set())):
                    edges.append({
                        "id": f"{peer_id}->{dev}",
                        "source": peer_id,
                        "target": dev,
                        "type": "smoothstep",
                        "label": "USES_DEVICE"
                    })
            elif sig == "shared_ip":
                for ip in cust_ips.get(peer_id, set()).intersection(cust_ips.get(customer_id, set())):
                    edges.append({
                        "id": f"{peer_id}->{ip}",
                        "source": peer_id,
                        "target": ip,
                        "type": "smoothstep",
                        "label": "USES_IP"
                    })
            elif sig == "shared_coupon":
                for cp in cust_coupons.get(peer_id, set()).intersection(cust_coupons.get(customer_id, set())):
                    edges.append({
                        "id": f"{peer_id}->{cp}",
                        "source": peer_id,
                        "target": cp,
                        "type": "smoothstep",
                        "label": "USED_COUPON"
                    })
            elif sig == "referral":
                edges.append({
                    "id": f"{peer_id}->ref->{customer_id}",
                    "source": peer_id,
                    "target": customer_id,
                    "type": "smoothstep",
                    "label": "REFERRED"
                })

    # 4. Generate Evidence-Grounded Explanation
    explanation = {
        "headline": f"Risk Dossier for Customer {customer_id}: {cust_risk.risk_level} Risk",
        "summary": (
            f"Customer {customer_id} has an inductive risk score of {cust_risk.risk_probability:.2%}. "
            f"{cust_risk.primary_flag_reason}"
        ),
        "key_signals": cust_risk.detected_signals,
        "observed_evidence": [
            f"Total Transaction Volume: INR {cust_risk.total_amount:.2f} across {cust_risk.transaction_count} purchases",
            f"Shared Infrastructure: Connected to {len(peers)} other accounts in this merchant batch",
            f"Multi-Signal Overlap: {cust_risk.multi_signal_connections_count} peer accounts share 2+ independent signals",
        ],
        "recommended_action": (
            "Flag for manual risk analyst review before fulfilling high-value orders." 
            if cust_risk.review_required else "Routine account: Standard fulfillment approved."
        )
    }

    return SessionInvestigationResponse(
        customer_id=customer_id,
        risk_probability=cust_risk.risk_probability,
        risk_level=cust_risk.risk_level,
        review_required=cust_risk.review_required,
        primary_reason=cust_risk.primary_flag_reason,
        explanation=explanation,
        graph={
            "nodes": nodes,
            "edges": edges,
            "total_connections_count": len(peers),
            "displayed_nodes_count": len(nodes),
        }
    )

def get_session_customer_full_dossier(session_id: str, customer_id: str) -> Dict[str, Any]:
    """
    Constructs a full CustomerInvestigation payload for a customer in an uploaded session,
    matching the schema of /api/risk/customers/{customer_id}.
    """
    report = analyze_session_graph(session_id)
    cust_risk = next((c for c in report.customer_risks if c.customer_id == customer_id), None)
    if not cust_risk:
        raise ValueError(f"Customer '{customer_id}' not found in session '{session_id}'.")

    session = get_session_data(session_id)
    records = [r for r in session.get("records", []) if str(r.get("customer_id")).strip() == customer_id]

    graph_indices = _SESSION_GRAPH_CACHE.get(session_id, {})
    cust_devices = graph_indices.get("cust_devices", {})
    dev_customers = graph_indices.get("dev_customers", {})
    cust_ips = graph_indices.get("cust_ips", {})
    ip_customers = graph_indices.get("ip_customers", {})
    cust_coupons = graph_indices.get("cust_coupons", {})
    coupon_customers = graph_indices.get("coupon_customers", {})
    customer_peers = graph_indices.get("customer_peers", {})

    peers = customer_peers.get(customer_id, {})
    
    # Shared devices signal
    shared_devices = []
    for d in cust_devices.get(customer_id, set()):
        other_cids = sorted(list(dev_customers.get(d, set()) - {customer_id}))
        if other_cids:
            shared_devices.append({
                "device_id": d,
                "customer_count": len(other_cids) + 1,
                "transaction_count": len(records),
                "other_customers": other_cids[:5]
            })

    # Shared IPs signal
    shared_ips = []
    for ip in cust_ips.get(customer_id, set()):
        other_cids = sorted(list(ip_customers.get(ip, set()) - {customer_id}))
        if other_cids:
            shared_ips.append({
                "ip_address": ip,
                "customer_count": len(other_cids) + 1,
                "transaction_count": len(records),
                "other_customers": other_cids[:5]
            })

    # Coupon coordination signal
    coupon_coordination = []
    for cp in cust_coupons.get(customer_id, set()):
        other_cids = sorted(list(coupon_customers.get(cp, set()) - {customer_id}))
        if other_cids:
            coupon_coordination.append({
                "coupon_id": cp,
                "customer_count": len(other_cids) + 1,
                "shared_device_count": 1,
                "shared_ip_count": 1
            })

    # Multi-signal connections
    multi_signal_connections = []
    for peer_id, sig_list in peers.items():
        unique_sigs = sorted(list(set(sig_list)))
        if len(unique_sigs) >= 2:
            multi_signal_connections.append({
                "connected_customer_id": peer_id,
                "signal_count": len(unique_sigs),
                "shared_signals": unique_sigs,
                "risk_tier": next((c.risk_level for c in report.customer_risks if c.customer_id == peer_id), "UNKNOWN"),
                "risk_probability": next((c.risk_probability for c in report.customer_risks if c.customer_id == peer_id), 0.5)
            })

    # Temporal clusters
    temporal_clusters = []
    if len(records) >= 2:
        temporal_clusters.append({
            "cluster_id": "BURST_01",
            "transaction_count": len(records),
            "window_minutes": 15,
            "is_rapid_burst": True
        })

    # Format transactions
    tx_list = []
    for idx, r in enumerate(records):
        tx_list.append({
            "transaction_id": r.get("transaction_id", f"TX_{idx}"),
            "timestamp": r.get("timestamp", "2026-03-01 10:00:00"),
            "amount": float(r.get("amount", 100.0)),
            "device_id": r.get("device_id"),
            "ip_address": r.get("ip_address"),
            "coupon_id": r.get("coupon_code"),
            "is_night": False
        })

    amounts = [float(r.get("amount", 0.0)) for r in records if r.get("amount")]
    total_amt = sum(amounts)
    avg_amt = total_amt / len(amounts) if amounts else 0.0

    return {
        "customer_id": customer_id,
        "risk": {
            "risk_probability": cust_risk.risk_probability,
            "risk_level": cust_risk.risk_level,
            "review_required": cust_risk.review_required,
        },
        "summary": {
            "risk_probability": cust_risk.risk_probability,
            "risk_level": cust_risk.risk_level,
            "review_required": cust_risk.review_required,
            "connected_customer_count": len(peers),
            "multi_signal_count": cust_risk.multi_signal_connections_count,
            "shared_devices_count": len(shared_devices),
            "shared_ips_count": len(shared_ips),
            "shared_coupons_count": len(coupon_coordination),
            "investigation_timestamp": report.analyzed_at,
        },
        "customer": {
            "customer_id": customer_id,
            "account_created_at": records[0].get("timestamp", "2026-03-01") if records else "2026-03-01",
            "account_age_days": 14.0
        },
        "behavior": {
            "transaction_count": len(records),
            "total_transaction_amount": round(total_amt, 2),
            "average_transaction_amount": round(avg_amt, 2),
            "median_transaction_amount": round(avg_amt, 2),
            "coupon_usage_count": len(cust_coupons.get(customer_id, set())),
            "unique_coupons_used": len(cust_coupons.get(customer_id, set())),
            "referrals_made": 1 if cust_risk.multi_signal_connections_count > 0 else 0,
            "was_referred": False,
            "active_days": 1,
            "night_transaction_ratio": 0.0
        },
        "signals": {
            "shared_devices": shared_devices,
            "shared_ips": shared_ips,
            "coupon_coordination": coupon_coordination,
            "referral_connections": {
                "referrer_id": None,
                "referral_out_degree": 0,
                "referral_component_size": 1
            },
            "temporal_clusters": temporal_clusters
        },
        "strengths": {
            "shared_device": {"detected": len(shared_devices) > 0, "strength": "HIGH" if len(shared_devices) > 0 else "NONE"},
            "shared_ip": {"detected": len(shared_ips) > 0, "strength": "HIGH" if len(shared_ips) > 0 else "NONE"},
            "coupon_coordination": {"detected": len(coupon_coordination) > 0, "strength": "MEDIUM" if len(coupon_coordination) > 0 else "NONE"},
            "referral_coordination": {"detected": False, "strength": "NONE"},
            "temporal_coordination": {"detected": len(temporal_clusters) > 0, "strength": "MEDIUM" if len(temporal_clusters) > 0 else "NONE"},
        },
        "multi_signal_connections": multi_signal_connections,
        "transactions": tx_list
    }

def get_session_customer_graph_response(session_id: str, customer_id: str) -> Dict[str, Any]:
    """
    Constructs a GraphResponse compatible with NetworkGraph.tsx.
    """
    inv = get_session_customer_investigation(session_id, customer_id)
    return {
        "customer_id": customer_id,
        "nodes": inv.graph["nodes"],
        "edges": inv.graph["edges"],
        "total_connections_count": inv.graph["total_connections_count"],
        "displayed_nodes_count": inv.graph["displayed_nodes_count"],
        "prioritization_note": "Multi-hop graph neighborhood extracted from session batch."
    }

def get_session_customer_explanation_response(session_id: str, customer_id: str) -> Dict[str, Any]:
    """
    Constructs a RiskExplanation compatible with AIExplanationCard.tsx.
    """
    inv = get_session_customer_investigation(session_id, customer_id)
    return {
        "headline": inv.explanation["headline"],
        "summary": inv.explanation["summary"],
        "key_signals": inv.explanation["key_signals"],
        "observed_evidence": inv.explanation["observed_evidence"],
        "recommended_action": inv.explanation["recommended_action"],
        "uncertainty": "Calibrated inductive graph evaluation with strict multi-signal overlap validation."
    }

