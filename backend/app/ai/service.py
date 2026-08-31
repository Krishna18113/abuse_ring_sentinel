import os
import re
import time
import json
import logging
from typing import Dict, Any, Set

from app.ai.schemas import RiskExplanation
from app.ai.gemini import query_gemini_explanation

logger = logging.getLogger(__name__)

# Configurable retries
MAX_RETRIES = 3
RETRY_DELAY = 1.0

def sanitize_evidence_package(pkg: dict) -> dict:
    """Removes all ground-truth fields and internal split indicators to prevent target leakage."""
    sanitized = json.loads(json.dumps(pkg)) # Deep clone
    
    # Static forbidden keys to delete recursively
    forbidden_keys = {"is_abuse", "ring_id", "abuse_type", "ground_truth", "split", "label"}
    
    def _sanitize(d: Any) -> Any:
        if isinstance(d, dict):
            return {k: _sanitize(v) for k, v in d.items() if k not in forbidden_keys}
        elif isinstance(d, list):
            return [_sanitize(item) for item in d]
        return d
        
    return _sanitize(sanitized)

def get_all_numbers_from_text(text: str) -> Set[int]:
    """Finds all integers in the text string."""
    return {int(n) for n in re.findall(r"\b\d+\b", text)}

def get_all_numbers_from_dict(d: Any) -> Set[int]:
    """Recursively extracts all integers from the evidence package dictionary values."""
    nums = set()
    if isinstance(d, dict):
        for k, v in d.items():
            nums.update(get_all_numbers_from_dict(v))
    elif isinstance(d, list):
        for item in d:
            nums.update(get_all_numbers_from_dict(item))
    elif isinstance(d, (int, float)):
        # Try to cast to int if it's a whole number
        try:
            nums.add(int(d))
        except (ValueError, TypeError):
            pass
    return nums

def verify_explanation_claims(explanation: dict, evidence: dict) -> bool:
    """Verifies that the generated AI explanation does not contain unsupported numeric claims."""
    # Combine all explanation text
    full_text = " ".join([
        explanation.get("headline", ""),
        explanation.get("summary", ""),
        " ".join(explanation.get("key_signals", [])),
        " ".join(explanation.get("observed_evidence", [])),
        explanation.get("recommended_action", ""),
        explanation.get("uncertainty", "")
    ])
    
    explanation_nums = get_all_numbers_from_text(full_text)
    evidence_nums = get_all_numbers_from_dict(evidence)
    
    # Safe list of common numbers that can appear in descriptions or hours/timeframes
    safe_ignore_nums = {0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 15, 24, 60, 300, 900, 1000, 10000}
    
    unsupported = []
    for num in explanation_nums:
        if num not in evidence_nums and num not in safe_ignore_nums:
            unsupported.append(num)
            
    if unsupported:
        logger.warning(f"Unsupported claims detected in AI explanation: {unsupported} not found in evidence package.")
        return False
        
    return True

def generate_fallback_explanation(evidence_package: dict) -> dict:
    """Generates a deterministic fallback risk explanation in python if Gemini fails."""
    summary = evidence_package.get("summary", {})
    prob = evidence_package.get("risk", {}).get("risk_probability", 0.0)
    review_required = evidence_package.get("risk", {}).get("review_required", False)
    review_str = "Yes" if review_required else "No"
    
    headline = "High-Risk Coordinated Activity Detected" if review_required else "Low Coordinated Risk Observed"
    
    key_signals = []
    observed_evidence = []
    
    strengths = evidence_package.get("strengths", {})
    for category, s in strengths.items():
        if s.get("detected"):
            key_signals.append(f"{category.replace('_', ' ').title()} - {s['strength']} Strength")
            
    # Devices
    devs = evidence_package.get("signals", {}).get("shared_devices", [])
    for d in devs:
        observed_evidence.append(f"Device {d['device_id']} is shared by {d['customer_count']} customers.")
        
    # IPs
    ips = evidence_package.get("signals", {}).get("shared_ips", [])
    for ip in ips:
        observed_evidence.append(f"IP {ip['ip_address']} is shared by {ip['customer_count']} customers.")
        
    # Multi-signal
    multi = evidence_package.get("multi_signal_connections", [])
    if multi:
        observed_evidence.append(f"Found {len(multi)} customers connected via multiple independent signals.")
        
    # Temporal
    temps = evidence_package.get("signals", {}).get("temporal_clusters", [])
    for t in temps:
        observed_evidence.append(f"Transactions occur within a {t['time_window_seconds']}s window ({t['customer_count']} customers, {t['transaction_count']} txs).")
        
    if not key_signals:
        key_signals.append("No unusual coordination signals observed.")
        
    fallback = {
        "headline": headline,
        "summary": f"AI explanation unavailable. Risk probability: {prob:.2%}. Review required: {review_str}.",
        "key_signals": key_signals,
        "observed_evidence": observed_evidence,
        "recommended_action": "Review the connected accounts and transaction activity." if review_required else "No immediate action required.",
        "uncertainty": "These signals indicate coordinated activity but do not independently establish fraudulent intent."
    }
    
    return RiskExplanation(**fallback).model_dump()

def explain_risk(evidence_package: dict) -> dict:
    """Orchestrates risk explanation generation with sanitization, retries, and fallback."""
    # 1. Sanitize payload
    sanitized_pkg = sanitize_evidence_package(evidence_package)
    
    # 2. Run query loop with retries
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # Query Gemini
            explanation = query_gemini_explanation(sanitized_pkg)
            
            # Validate output
            validated = RiskExplanation(**explanation).model_dump()
            
            # Verify claims
            if verify_explanation_claims(validated, sanitized_pkg):
                return validated
            else:
                logger.warning(f"Attempt {attempt}/{MAX_RETRIES} failed verification due to unsupported claims.")
                
        except Exception as e:
            logger.warning(f"Attempt {attempt}/{MAX_RETRIES} failed with error: {str(e)}")
            
        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY)
            
    # 3. Trigger fallback
    logger.info("All Gemini explanation attempts failed. Reverting to fallback summary.")
    return generate_fallback_explanation(evidence_package)
