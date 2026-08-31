import os
import time
import argparse
import random
import pandas as pd
import numpy as np

from app.ml.utils import DATA_DIR
from app.risk.investigator import investigate_customer

def print_report(pkg: dict):
    """Outputs a clean, human-readable terminal report matching the requested style."""
    c_id = pkg["customer"]["customer_id"]
    risk = pkg["risk"]
    behavior = pkg["behavior"]
    signals = pkg["signals"]
    multi = pkg["multi_signal_connections"]
    summary = pkg["summary"]
    
    print("\n" + "=" * 40)
    print("ABUSE RING SENTINEL")
    print("RISK INVESTIGATION REPORT")
    print("=" * 40)
    
    print(f"Customer: {c_id}")
    print(f"\nRisk Probability: {risk['risk_probability']:.2%}")
    print(f"Risk Level:       {risk['risk_level']}")
    print(f"Review Required:  {'YES' if risk['review_required'] else 'NO'}")
    
    print("\n" + "-" * 40)
    print("BEHAVIOR")
    print("-" * 40)
    print(f"Transactions:  {behavior['transaction_count']}")
    print(f"Coupon Usage:  {behavior['coupon_usage_count']}")
    print(f"Referrals:     {behavior['referrals_made']}")
    
    print("\n" + "-" * 40)
    print("GRAPH SIGNALS")
    print("-" * 40)
    
    # Shared Device
    devs = signals["shared_devices"]
    if devs:
        print("Shared Device:")
        for d in devs:
            print(f"  Device {d['device_id']}")
            print(f"  {d['customer_count']} connected customers | {d['transaction_count']} txs")
    else:
        print("Shared Device:\n  None")
        
    # Shared IP
    ips = signals["shared_ips"]
    if ips:
        print("\nShared IP:")
        for ip in ips:
            print(f"  IP {ip['ip_address']}")
            print(f"  {ip['customer_count']} connected customers | {ip['transaction_count']} txs")
    else:
        print("\nShared IP:\n  None")
        
    # Coupon Coordination
    cps = signals["coupon_coordination"]
    if cps:
        print("\nCoupon Coordination:")
        for cp in cps:
            print(f"  Coupon {cp['coupon_id']}")
            print(f"  {cp['customer_count']} users | Device overlap: {cp['shared_device_count']} | IP overlap: {cp['shared_ip_count']}")
    else:
        print("\nCoupon Coordination:\n  None")
        
    # Referral Coordination
    refs = signals["referral_connections"]
    if refs["referral_in_degree"] > 0 or refs["referral_out_degree"] > 0:
        print("\nReferral Coordination:")
        print(f"  Referrer: {refs['referrer_id'] or 'None'}")
        print(f"  Referred accounts count: {refs['referral_out_degree']}")
        print(f"  Local referral component size: {refs['referral_component_size']}")
    else:
        print("\nReferral Coordination:\n  None")
        
    # Temporal Coordination
    temps = signals["temporal_clusters"]
    if temps:
        print("\nTemporal Coordination:")
        for t in temps:
            print(f"  {t['time_window_seconds']}s window: {t['customer_count']} customers | {t['transaction_count']} transactions")
            print(f"  Total amount: INR {t['total_amount']:,.2f}")
    else:
        print("\nTemporal Coordination:\n  None")
        
    print("\n" + "-" * 40)
    print("MULTI-SIGNAL CONNECTIONS (Ranked)")
    print("-" * 40)
    if multi:
        for m in multi[:5]: # Top 5 connections
            print(f"Customer {m['connected_customer']}")
            for sig in m["signals"]:
                print(f"  - {sig}")
    else:
        print("  None")
        
    print("\n" + "=" * 40)
    print(f"Evidence Signals Detected: {summary['signal_count']}")
    print(f"Connected Customers:      {summary['connected_customer_count']}")
    print("=" * 40 + "\n")

def run_benchmarks(data_dir=DATA_DIR):
    """Measures latency over 20 random customers and runs ground-truth leakage checks."""
    print("Initializing Scorer and preloading graph...")
    start_init = time.time()
    investigate_customer("C_00000") # Force lazy scorer init
    init_latency = time.time() - start_init
    print(f"Initialization completed in {init_latency:.2f}s")
    
    # 1. Load customers list
    df_cust = pd.read_csv(os.path.join(data_dir, "customers.csv"))
    customer_ids = df_cust["customer_id"].tolist()
    
    # Select 20 random customer IDs
    sampled_ids = random.sample(customer_ids, min(20, len(customer_ids)))
    
    latencies = []
    print(f"\nBenchmarking query latency on {len(sampled_ids)} customers...")
    
    for c_id in sampled_ids:
        t0 = time.time()
        investigate_customer(c_id)
        latency_ms = (time.time() - t0) * 1000.0
        latencies.append(latency_ms)
        print(f"  Customer {c_id} investigated in {latency_ms:.2f} ms")
        
    avg_latency = np.mean(latencies)
    p95_latency = np.percentile(latencies, 95)
    
    print("\n" + "=" * 40)
    print("BENCHMARK REPORT")
    print("=" * 40)
    print(f"Average Latency:  {avg_latency:.2f} ms")
    print(f"p95 Latency:      {p95_latency:.2f} ms")
    print("=" * 40)
    
    # 2. Ground truth leakage static check
    # Assert that no file in the app/risk directory accesses ground_truth or ground-truth fields
    risk_dir = os.path.dirname(os.path.abspath(__file__))
    forbidden_words = ["ground_truth", "is_abuse", "ring_id", "abuse_type"]
    
    print("\nRunning ground-truth leakage static scan...")
    leakage_found = False
    
    for filename in os.listdir(risk_dir):
        if not filename.endswith(".py") or filename == "cli.py":
            continue
        filepath = os.path.join(risk_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            # Exclude imports and comments if any, but since we wrote it, we can scan the entire string
            for word in forbidden_words:
                if word in content:
                    print(f"  [WARNING] Possible leakage indicator: '{word}' found in {filename}")
                    leakage_found = True
                    
    if not leakage_found:
        print("  => LEAKAGE STATIC CHECK: PASS (No ground-truth references found in risk package)")
    else:
        print("  => LEAKAGE STATIC CHECK: WARNING (Possible reference found)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Investigation CLI & Evidence Engine.")
    parser.add_argument("--customer-id", type=str, help="Customer ID to investigate")
    parser.add_argument("--benchmark", action="store_true", help="Run latency benchmark on 20 random customers")
    args = parser.parse_args()
    
    if args.benchmark:
        run_benchmarks()
    elif args.customer_id:
        pkg = investigate_customer(args.customer_id)
        print_report(pkg)
    else:
        parser.print_help()
