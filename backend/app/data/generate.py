import os
import json
import argparse
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from app.data.behavior import (
    generate_device_and_ip_pools,
    generate_coupons,
    generate_legitimate_customers,
    generate_legitimate_referrals,
    generate_customer_transactions,
    generate_abuse_rings
)
from app.data.check import run_validation_checks

def main():
    parser = argparse.ArgumentParser(description="Synthetic fraud/abuse dataset generator.")
    parser.add_argument("--seed", type=int, default=42, help="Fixed random seed for reproducibility.")
    parser.add_argument("--output-dir", type=str, default=None, help="Directory to save generated CSVs.")
    args = parser.parse_args()

    # Set seed
    random.seed(args.seed)
    np.random.seed(args.seed)

    # Setup directories
    if args.output_dir:
        output_dir = args.output_dir
    else:
        # Default to backend/data/generated/ relative to this script
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        output_dir = os.path.join(base_dir, "data", "generated")

    os.makedirs(output_dir, exist_ok=True)
    print(f"Generating synthetic dataset using seed {args.seed}...")
    print(f"Output directory: {output_dir}")

    # Configuration for timeline
    start_time = datetime(2025, 1, 1, 0, 0, 0)
    total_seconds = 365 * 24 * 3600  # 1 year

    # Time cutoffs for splits
    t1_seconds = int(0.70 * total_seconds)
    t2_seconds = int(0.85 * total_seconds)
    t1_time = start_time + timedelta(seconds=t1_seconds)
    t2_time = start_time + timedelta(seconds=t2_seconds)

    print("Generating pools (devices, IPs, coupons)...")
    devices, ips, device_locs, ip_locs = generate_device_and_ip_pools()
    coupons = generate_coupons(start_time, total_seconds)

    # 1. Generate legitimate customers
    print("Generating legitimate customers...")
    legit_customers = generate_legitimate_customers(
        num_customers=46000,
        start_time=start_time,
        total_seconds=total_seconds,
        devices=devices,
        ips=ips,
        device_locs=device_locs,
        ip_locs=ip_locs,
        coupons=coupons
    )

    # 2. Generate referrals for legitimate customers
    print("Generating legitimate referrals...")
    legit_referrals = generate_legitimate_referrals(legit_customers, p_referred=0.72)

    # 3. Generate legitimate transactions
    print("Generating legitimate transactions...")
    legit_transactions = []
    for cust in legit_customers:
        txs = generate_customer_transactions(cust, coupons, start_time, total_seconds)
        legit_transactions.extend(txs)

    # 4. Generate abuse rings (customers, referrals, transactions)
    print("Generating abuse rings...")
    # target ~4,000 fraud customers to reach 8% fraud overall
    abuse_customers, abuse_transactions, abuse_referrals = generate_abuse_rings(
        num_rings=120,
        start_idx=46000,
        target_total_fraud=4000,
        start_time=start_time,
        total_seconds=total_seconds,
        devices=devices,
        ips=ips,
        device_locs=device_locs,
        ip_locs=ip_locs,
        coupons=coupons
    )

    # Combine customers
    all_customers_raw = legit_customers + abuse_customers
    
    # Separate customer info and ground truth metadata
    customers_list = []
    ground_truth_list = []
    for c in all_customers_raw:
        # Determine split
        if "split" in c:
            split = c["split"]
        else:
            reg_time = c["account_created_at"]
            if reg_time <= t1_time:
                split = "train"
            elif reg_time <= t2_time:
                split = "val"
            else:
                split = "test"
                
        customers_list.append({
            "customer_id": c["customer_id"],
            "account_created_at": c["account_created_at"].strftime("%Y-%m-%d %H:%M:%S"),
            "location": c["location"],
            "device_id": c["device_id"],
            "ip_address": c["ip_address"],
            "split": split
        })
        ground_truth_list.append({
            "customer_id": c["customer_id"],
            "is_abuse": c["is_abuse"],
            "ring_id": c["ring_id"],
            "abuse_type": c["abuse_type"]
        })

    # Combine referrals and sort chronologically
    all_referrals = legit_referrals + abuse_referrals
    all_referrals.sort(key=lambda x: x["timestamp"])

    # Combine transactions and sort chronologically to assign ordered transaction_ids
    all_transactions = legit_transactions + abuse_transactions
    all_transactions.sort(key=lambda x: x["timestamp"])
    for idx, tx in enumerate(all_transactions):
        tx["transaction_id"] = f"TX_{idx:06d}"

    # Convert to DataFrames
    df_customers = pd.DataFrame(customers_list)
    df_transactions = pd.DataFrame(all_transactions)
    df_referrals = pd.DataFrame(all_referrals)
    df_coupons = pd.DataFrame(coupons)
    df_ground_truth = pd.DataFrame(ground_truth_list)

    # Reorder transaction columns to match requested schema:
    # transaction_id, customer_id, amount, timestamp, coupon_id, product_id, payment_method
    df_transactions = df_transactions[[
        "transaction_id", "customer_id", "amount", "timestamp", "coupon_id", "product_id", "payment_method"
    ]]

    # Save to CSV files
    print("Saving CSV files...")
    df_customers.to_csv(os.path.join(output_dir, "customers.csv"), index=False)
    df_transactions.to_csv(os.path.join(output_dir, "transactions.csv"), index=False)
    df_referrals.to_csv(os.path.join(output_dir, "referrals.csv"), index=False)
    df_coupons.to_csv(os.path.join(output_dir, "coupons.csv"), index=False)
    df_ground_truth.to_csv(os.path.join(output_dir, "ground_truth.csv"), index=False)

    # Compute missing values counts
    missing_counts = {
        "customers": df_customers.isna().sum().to_dict(),
        "transactions": df_transactions.isna().sum().to_dict(),
        "referrals": df_referrals.isna().sum().to_dict(),
        "coupons": df_coupons.isna().sum().to_dict(),
        "ground_truth": df_ground_truth.isna().sum().to_dict()
    }
    
    # Cast numpy types to python native types in dict for JSON serialization
    for df_name in missing_counts:
        missing_counts[df_name] = {k: int(v) for k, v in missing_counts[df_name].items()}

    # Compute abuse type distribution
    abuse_type_dist = df_ground_truth[df_ground_truth['is_abuse']]['abuse_type'].value_counts().to_dict()
    abuse_type_dist = {k: int(v) for k, v in abuse_type_dist.items()}

    # Calculate date range
    tx_min_date = df_transactions['timestamp'].min()
    tx_max_date = df_transactions['timestamp'].max()

    # Calculate rings count
    unique_rings = df_ground_truth['ring_id'].dropna().nunique()

    # Create dataset_summary.json
    summary = {
        "row_counts": {
            "customers": len(df_customers),
            "transactions": len(df_transactions),
            "referrals": len(df_referrals),
            "coupons": len(df_coupons),
            "ground_truth": len(df_ground_truth)
        },
        "number_of_legitimate_customers": int(len(df_customers) - df_ground_truth['is_abuse'].sum()),
        "number_of_abuse_customers": int(df_ground_truth['is_abuse'].sum()),
        "number_of_abuse_rings": int(unique_rings),
        "abuse_type_distribution": abuse_type_dist,
        "transaction_date_range": {
            "start": tx_min_date,
            "end": tx_max_date
        },
        "time_split_cutoffs": {
            "train_validation_cutoff": t1_time.strftime("%Y-%m-%d %H:%M:%S"),
            "validation_test_cutoff": t2_time.strftime("%Y-%m-%d %H:%M:%S")
        },
        "missing_value_counts": missing_counts
    }

    # Save summary to file
    summary_path = os.path.join(output_dir, "dataset_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=4)
    print(f"Saved dataset summary to {summary_path}")

    # Run post-generation quality checks
    print("Running validation checks...")
    success = run_validation_checks(output_dir)
    
    if success:
        print("\nGeneration and validation completed successfully.")
        exit(0)
    else:
        print("\nValidation failed!")
        exit(1)

if __name__ == "__main__":
    main()
