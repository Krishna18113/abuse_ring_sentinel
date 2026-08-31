from typing import Dict, Any, List

def evaluate_device_strength(shared_devices: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Evaluate strength of shared device evidence."""
    if not shared_devices:
        return {"detected": False, "strength": "NONE", "details": {}}
        
    # Get maximum customer count across all devices used by this customer
    max_cust_count = max(d["customer_count"] for d in shared_devices)
    
    if max_cust_count >= 5:
        strength = "HIGH"
    elif max_cust_count >= 2:
        strength = "MEDIUM"
    elif max_cust_count >= 1:
        strength = "LOW"
    else:
        strength = "NONE"
        
    return {
        "detected": strength != "NONE",
        "strength": strength,
        "details": {
            "device_count": len(shared_devices),
            "max_sharing_degree": max_cust_count
        }
    }

def evaluate_ip_strength(shared_ips: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Evaluate strength of shared IP evidence."""
    if not shared_ips:
        return {"detected": False, "strength": "NONE", "details": {}}
        
    max_cust_count = max(ip["customer_count"] for ip in shared_ips)
    
    if max_cust_count >= 10:
        strength = "HIGH"
    elif max_cust_count >= 3:
        strength = "MEDIUM"
    elif max_cust_count >= 1:
        strength = "LOW"
    else:
        strength = "NONE"
        
    return {
        "detected": strength != "NONE",
        "strength": strength,
        "details": {
            "ip_count": len(shared_ips),
            "max_sharing_degree": max_cust_count
        }
    }

def evaluate_coupon_strength(coupons: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Evaluate strength of coupon coordination evidence."""
    if not coupons:
        return {"detected": False, "strength": "NONE", "details": {}}
        
    max_cust_count = max(c["customer_count"] for c in coupons)
    max_overlap = max(c["shared_device_count"] + c["shared_ip_count"] for c in coupons)
    
    if max_cust_count >= 15 or max_overlap >= 3:
        strength = "HIGH"
    elif max_cust_count >= 5 or max_overlap >= 1:
        strength = "MEDIUM"
    elif max_cust_count >= 1:
        strength = "LOW"
    else:
        strength = "NONE"
        
    return {
        "detected": strength != "NONE",
        "strength": strength,
        "details": {
            "coupons_used_count": len(coupons),
            "max_coupon_sharing_degree": max_cust_count,
            "max_infrastructure_overlap": max_overlap
        }
    }

def evaluate_referral_strength(referral_info: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate strength of referral network evidence."""
    comp_size = referral_info.get("referral_component_size", 1)
    out_deg = referral_info.get("referral_out_degree", 0)
    in_deg = referral_info.get("referral_in_degree", 0)
    
    if comp_size >= 10 or out_deg >= 5:
        strength = "HIGH"
    elif comp_size >= 3 or out_deg >= 2:
        strength = "MEDIUM"
    elif comp_size >= 2 or out_deg >= 1 or in_deg >= 1:
        strength = "LOW"
    else:
        strength = "NONE"
        
    return {
        "detected": strength != "NONE",
        "strength": strength,
        "details": {
            "referral_in_degree": in_deg,
            "referral_out_degree": out_deg,
            "referral_component_size": comp_size
        }
    }

def evaluate_temporal_strength(clusters: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Evaluate strength of temporal transaction coordination evidence."""
    if not clusters:
        return {"detected": False, "strength": "NONE", "details": {}}
        
    # Check for clusters of different window sizes
    has_high = False
    has_med = False
    has_low = False
    
    for c in clusters:
        window = c["time_window_seconds"]
        cust_cnt = c["customer_count"]
        
        if window <= 60 and cust_cnt >= 3:
            has_high = True
        elif window <= 300 and cust_cnt >= 5:
            has_high = True
        elif window <= 300 and cust_cnt >= 2:
            has_med = True
        elif window <= 900 and cust_cnt >= 2:
            has_low = True
            
    if has_high:
        strength = "HIGH"
    elif has_med:
        strength = "MEDIUM"
    elif has_low:
        strength = "LOW"
    else:
        strength = "NONE"
        
    return {
        "detected": strength != "NONE",
        "strength": strength,
        "details": {
            "cluster_count": len(clusters),
            "largest_cluster_size": max((c["customer_count"] for c in clusters), default=0)
        }
    }

def compile_strengths(signals: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Compile strengths for all evidence categories."""
    return {
        "shared_device": evaluate_device_strength(signals.get("shared_devices", [])),
        "shared_ip": evaluate_ip_strength(signals.get("shared_ips", [])),
        "coupon_coordination": evaluate_coupon_strength(signals.get("coupon_coordination", [])),
        "referral_coordination": evaluate_referral_strength(signals.get("referral_connections", {})),
        "temporal_coordination": evaluate_temporal_strength(signals.get("temporal_clusters", []))
    }
