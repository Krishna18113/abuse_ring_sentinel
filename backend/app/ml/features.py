import os
import pandas as pd
import numpy as np
from datetime import datetime

def extract_cutoff_features(data_dir, cutoff_time_str, split_label=None):
    """Extract customer-level tabular and structural features up to a specific cutoff timestamp.
    Ensures that no future events (transactions, referrals, registrations) are used."""
    
    cutoff_time = datetime.strptime(cutoff_time_str, "%Y-%m-%d %H:%M:%S")
    
    # 1. Load baseline CSV files
    df_customers = pd.read_csv(os.path.join(data_dir, "customers.csv"))
    df_transactions = pd.read_csv(os.path.join(data_dir, "transactions.csv"))
    df_referrals = pd.read_csv(os.path.join(data_dir, "referrals.csv"))
    df_gt = pd.read_csv(os.path.join(data_dir, "ground_truth.csv"))
    
    # Filter customers by registration time: only those registered <= cutoff_time are visible
    df_customers["account_created_at_dt"] = pd.to_datetime(df_customers["account_created_at"])
    df_visible_customers = df_customers[df_customers["account_created_at_dt"] <= cutoff_time].copy()
    
    # If a specific split is requested, filter customers accordingly
    if split_label is not None:
        df_visible_customers = df_visible_customers[df_visible_customers["split"] == split_label].copy()
        
    if df_visible_customers.empty:
        raise ValueError(f"No customers registered before or in split {split_label} up to cutoff {cutoff_time_str}")
        
    # Filter transactions and referrals strictly by cutoff time to prevent temporal leakage
    df_transactions["timestamp_dt"] = pd.to_datetime(df_transactions["timestamp"])
    df_tx_filtered = df_transactions[df_transactions["timestamp_dt"] <= cutoff_time].copy()
    
    df_referrals["timestamp_dt"] = pd.to_datetime(df_referrals["timestamp"])
    df_ref_filtered = df_referrals[df_referrals["timestamp_dt"] <= cutoff_time].copy()
    
    # 2. Compute Infrastructure Degrees (sharing counts <= cutoff)
    # device_degree: count unique visible customers sharing each device
    dev_degree = df_visible_customers.groupby("device_id")["customer_id"].nunique().to_dict()
    # ip_degree: count unique visible customers sharing each IP
    ip_degree = df_visible_customers.groupby("ip_address")["customer_id"].nunique().to_dict()
    
    # 3. Compute Coupon Degree (max usage of the coupons used by a customer <= cutoff)
    # Count unique customers per coupon
    coupon_sharing = df_tx_filtered[df_tx_filtered["coupon_id"].notna()].groupby("coupon_id")["customer_id"].nunique().to_dict()
    
    # Map back to transactions
    df_tx_filtered["coupon_degree"] = df_tx_filtered["coupon_id"].map(coupon_sharing).fillna(0)
    
    # 4. Group transactions by customer
    df_tx_filtered["hour"] = df_tx_filtered["timestamp_dt"].dt.hour
    df_tx_filtered["date"] = df_tx_filtered["timestamp_dt"].dt.date
    df_tx_filtered["is_night"] = ((df_tx_filtered["hour"] >= 22) | (df_tx_filtered["hour"] < 6)).astype(int)
    df_tx_filtered["has_coupon"] = df_tx_filtered["coupon_id"].notna().astype(int)
    
    tx_agg = df_tx_filtered.groupby("customer_id").agg(
        transaction_count=("amount", "count"),
        total_transaction_amount=("amount", "sum"),
        average_transaction_amount=("amount", "mean"),
        median_transaction_amount=("amount", "median"),
        transaction_amount_std=("amount", "std"),
        coupon_usage_count=("has_coupon", "sum"),
        unique_coupons_used=("coupon_id", "nunique"),
        active_days=("date", "nunique"),
        night_tx_count=("is_night", "sum"),
        max_coupon_degree=("coupon_degree", "max")
    )
    
    # Fill standard deviation with 0 if count <= 1
    tx_agg["transaction_amount_std"] = tx_agg["transaction_amount_std"].fillna(0.0)
    
    # Calculate ratios
    tx_agg["night_transaction_ratio"] = (tx_agg["night_tx_count"] / tx_agg["transaction_count"]).fillna(0.0)
    tx_agg["average_transactions_per_active_day"] = (tx_agg["transaction_count"] / tx_agg["active_days"]).fillna(0.0)
    
    # 5. Referral Degrees (in/out <= cutoff)
    referrals_made = df_ref_filtered.groupby("referrer_id")["referred_id"].nunique().to_dict()
    was_referred_set = set(df_ref_filtered["referred_id"])
    
    # 6. Assemble features dataframe
    features = []
    for _, row in df_visible_customers.iterrows():
        c_id = row["customer_id"]
        reg_time = row["account_created_at_dt"]
        
        # Account Age in days
        account_age_days = max(0.0, (cutoff_time - reg_time).total_seconds() / (24 * 3600))
        
        # Transaction statistics
        if c_id in tx_agg.index:
            c_tx = tx_agg.loc[c_id]
            tx_cnt = c_tx["transaction_count"]
            tot_amt = c_tx["total_transaction_amount"]
            avg_amt = c_tx["average_transaction_amount"]
            med_amt = c_tx["median_transaction_amount"]
            std_amt = c_tx["transaction_amount_std"]
            cp_cnt = c_tx["coupon_usage_count"]
            cp_uniq = c_tx["unique_coupons_used"]
            act_days = c_tx["active_days"]
            avg_tx_per_day = c_tx["average_transactions_per_active_day"]
            night_ratio = c_tx["night_transaction_ratio"]
            coupon_degree_val = c_tx["max_coupon_degree"]
        else:
            # Cold-start customers with no transactions yet
            tx_cnt, tot_amt, avg_amt, med_amt, std_amt = 0, 0.0, 0.0, 0.0, 0.0
            cp_cnt, cp_uniq, act_days, avg_tx_per_day, night_ratio = 0, 0, 0, 0.0, 0.0
            coupon_degree_val = 0.0
            
        # Infrastructure sharing degrees
        dev_deg = dev_degree.get(row["device_id"], 1)
        ip_deg = ip_degree.get(row["ip_address"], 1)
        
        # Referrals
        ref_out = referrals_made.get(c_id, 0)
        ref_in = 1 if c_id in was_referred_set else 0
        
        features.append({
            "customer_id": c_id,
            "account_age_days": float(account_age_days),
            "transaction_count": int(tx_cnt),
            "total_transaction_amount": float(tot_amt),
            "average_transaction_amount": float(avg_amt),
            "median_transaction_amount": float(med_amt),
            "transaction_amount_std": float(std_amt),
            "coupon_usage_count": int(cp_cnt),
            "unique_coupons_used": int(cp_uniq),
            "referrals_made": int(ref_out),
            "was_referred": int(ref_in),
            "device_customer_count": int(dev_deg), # Tabular name
            "ip_customer_count": int(ip_deg),       # Tabular name
            "active_days": int(act_days),
            "average_transactions_per_active_day": float(avg_tx_per_day),
            "night_transaction_ratio": float(night_ratio),
            # Structural features
            "device_degree": int(dev_deg),
            "ip_degree": int(ip_deg),
            "coupon_degree": int(coupon_degree_val),
            "referral_in_degree": int(ref_in),
            "referral_out_degree": int(ref_out)
        })
        
    df_features = pd.DataFrame(features)
    
    # Join target label from ground truth
    df_features = df_features.merge(df_gt, on="customer_id")
    # Map boolean label to int
    df_features["label"] = df_features["is_abuse"].astype(int)
    
    return df_features

def run_leakage_test(data_dir, cutoff_time_str, split_label="train"):
    """Leakage Test: Modifies future data and checks that re-extracted features are unchanged."""
    print(f"Running explicit leakage test for split '{split_label}' and cutoff '{cutoff_time_str}'...")
    
    # 1. Extract base features
    df_base = extract_cutoff_features(data_dir, cutoff_time_str, split_label)
    
    # 2. Simulate future activity in source CSVs (add future transactions/referrals in temporary data copy)
    temp_dir = os.path.join(data_dir, "..", "temp_leakage_test")
    os.makedirs(temp_dir, exist_ok=True)
    
    df_customers = pd.read_csv(os.path.join(data_dir, "customers.csv"))
    df_transactions = pd.read_csv(os.path.join(data_dir, "transactions.csv"))
    df_referrals = pd.read_csv(os.path.join(data_dir, "referrals.csv"))
    df_gt = pd.read_csv(os.path.join(data_dir, "ground_truth.csv"))
    
    # Add a future transaction for EVERY visible customer (timestamped in 2026, well after cutoff)
    future_tx = []
    cutoff_dt = datetime.strptime(cutoff_time_str, "%Y-%m-%d %H:%M:%S")
    future_time_str = "2026-06-01 12:00:00"
    
    df_customers_visible = df_customers[pd.to_datetime(df_customers["account_created_at"]) <= cutoff_dt]
    
    for idx, row in df_customers_visible.iterrows():
        future_tx.append({
            "transaction_id": f"TX_LEAK_{idx}",
            "customer_id": row["customer_id"],
            "amount": 9999.0, # Obvious dummy amount
            "timestamp": future_time_str,
            "coupon_id": "COUPON_99",
            "product_id": "PROD_999",
            "payment_method": "Credit Card"
        })
        
    df_tx_corrupted = pd.concat([df_transactions, pd.DataFrame(future_tx)], ignore_index=True)
    
    # Write to temp folder
    df_customers.to_csv(os.path.join(temp_dir, "customers.csv"), index=False)
    df_tx_corrupted.to_csv(os.path.join(temp_dir, "transactions.csv"), index=False)
    df_referrals.to_csv(os.path.join(temp_dir, "referrals.csv"), index=False)
    df_gt.to_csv(os.path.join(temp_dir, "ground_truth.csv"), index=False)
    
    # 3. Re-extract features from corrupted temp directory using original cutoff
    df_corrupted = extract_cutoff_features(temp_dir, cutoff_time_str, split_label)
    
    # Clean up temp files
    for f in os.listdir(temp_dir):
        os.remove(os.path.join(temp_dir, f))
    os.rmdir(temp_dir)
    
    # 4. Compare feature matrices
    assert len(df_base) == len(df_corrupted), "Leakage test: row count changed!"
    
    # Merge on customer_id to compare features
    merged = df_base.merge(df_corrupted, on="customer_id", suffixes=("_base", "_corr"))
    
    # Check key features like transaction_count and total_transaction_amount
    for feat in ["transaction_count", "total_transaction_amount", "device_degree", "ip_degree", "coupon_degree"]:
        base_col = f"{feat}_base"
        corr_col = f"{feat}_corr"
        diff = (merged[base_col] != merged[corr_col]).sum()
        assert diff == 0, f"LEAKAGE DETECTED: Feature '{feat}' changed by {diff} rows after adding future transactions!"
        
    print("  => LEAKAGE TEST PASSED: Future events do not affect historical feature matrices.")
    return True
