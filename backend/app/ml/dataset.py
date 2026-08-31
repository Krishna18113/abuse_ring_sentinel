import os
import pandas as pd
import numpy as np
import torch
from torch_geometric.data import HeteroData
from sklearn.preprocessing import StandardScaler
from app.ml.features import extract_cutoff_features

def build_heterodata_snapshot(data_dir, cutoff_time_str, split_label, scaler=None):
    """Build a PyTorch Geometric HeteroData graph snapshot up to a cutoff time.
    Standardizes features using the provided scaler (or fits one if None)."""
    
    # 1. Extract cutoff customer features & labels
    df_features = extract_cutoff_features(data_dir, cutoff_time_str)
    
    # Filter base CSVs to cutoff
    df_customers = pd.read_csv(os.path.join(data_dir, "customers.csv"))
    df_transactions = pd.read_csv(os.path.join(data_dir, "transactions.csv"))
    df_referrals = pd.read_csv(os.path.join(data_dir, "referrals.csv"))
    df_coupons = pd.read_csv(os.path.join(data_dir, "coupons.csv"))
    
    # Visible customers: registered <= cutoff
    df_customers["account_created_at_dt"] = pd.to_datetime(df_customers["account_created_at"])
    cutoff_dt = pd.to_datetime(cutoff_time_str)
    df_visible_custs = df_customers[df_customers["account_created_at_dt"] <= cutoff_dt].copy()
    visible_cust_ids = set(df_visible_custs["customer_id"])
    
    # Visible transactions & referrals
    df_transactions["timestamp_dt"] = pd.to_datetime(df_transactions["timestamp"])
    df_tx_filtered = df_transactions[
        (df_transactions["timestamp_dt"] <= cutoff_dt) & 
        (df_transactions["customer_id"].isin(visible_cust_ids))
    ].copy()
    
    df_referrals["timestamp_dt"] = pd.to_datetime(df_referrals["timestamp"])
    df_ref_filtered = df_referrals[
        (df_referrals["timestamp_dt"] <= cutoff_dt) & 
        (df_referrals["referrer_id"].isin(visible_cust_ids)) &
        (df_referrals["referred_id"].isin(visible_cust_ids))
    ].copy()
    
    # 2. Node index mappings
    # Customers
    cust_ids = sorted(list(visible_cust_ids))
    cust_id_to_idx = {c_id: idx for idx, c_id in enumerate(cust_ids)}
    
    # Transactions
    tx_ids = sorted(df_tx_filtered["transaction_id"].tolist())
    tx_id_to_idx = {t_id: idx for idx, t_id in enumerate(tx_ids)}
    
    # Devices
    dev_ids = sorted(df_visible_custs["device_id"].unique().tolist())
    dev_id_to_idx = {d_id: idx for idx, d_id in enumerate(dev_ids)}
    
    # IPs
    ip_ids = sorted(df_visible_custs["ip_address"].unique().tolist())
    ip_id_to_idx = {ip: idx for idx, ip in enumerate(ip_ids)}
    
    # Coupons (always use all 50 coupons)
    coupon_ids = sorted(df_coupons["coupon_id"].tolist())
    coupon_id_to_idx = {cp_id: idx for idx, cp_id in enumerate(coupon_ids)}
    
    # 3. Initialize PyG HeteroData object
    data = HeteroData()
    
    # 4. Construct Node Features
    # Customer Features (15 tabular/structural features)
    feature_cols = [
        "account_age_days", "transaction_count", "total_transaction_amount",
        "average_transaction_amount", "median_transaction_amount", "transaction_amount_std",
        "coupon_usage_count", "unique_coupons_used", "referrals_made", "was_referred",
        "device_customer_count", "ip_customer_count", "active_days",
        "average_transactions_per_active_day", "night_transaction_ratio",
        "device_degree", "ip_degree", "coupon_degree", "referral_in_degree", "referral_out_degree"
    ]
    
    # Reindex df_features to match cust_ids sorting
    df_features_sorted = pd.DataFrame({"customer_id": cust_ids})
    df_features_sorted = df_features_sorted.merge(df_features, on="customer_id", how="left").fillna(0.0)
    
    raw_cust_x = df_features_sorted[feature_cols].values.astype(np.float32)
    
    # Standardize customer features (fit only on train split)
    if split_label == "train" and scaler is None:
        # Fit scaler on train split customers only
        train_mask_series = df_features_sorted["customer_id"].isin(
            df_visible_custs[df_visible_custs["split"] == "train"]["customer_id"]
        )
        scaler = StandardScaler()
        scaler.fit(raw_cust_x[train_mask_series])
        
    scaled_cust_x = scaler.transform(raw_cust_x)
    data["customer"].x = torch.tensor(scaled_cust_x, dtype=torch.float32)
    data["customer"].y = torch.tensor(df_features_sorted["label"].values, dtype=torch.long)
    
    # Split Masks
    split_col = df_features_sorted["customer_id"].map(df_customers.set_index("customer_id")["split"])
    df_features_sorted["split"] = split_col
    data["customer"].train_mask = torch.tensor(split_col == "train", dtype=torch.bool)
    data["customer"].val_mask = torch.tensor(split_col == "val", dtype=torch.bool)
    data["customer"].test_mask = torch.tensor(split_col == "test", dtype=torch.bool)
    
    # Store customer_id list for mapping predictions
    data["customer"].customer_ids = cust_ids
    
    # Transaction Features (amount + cyclical time)
    # sin_hour = sin(2pi * hour / 24), cos_hour = cos(2pi * hour / 24)
    # sin_day = sin(2pi * dayofweek / 7), cos_day = cos(2pi * dayofweek / 7)
    df_tx_sorted = pd.DataFrame({"transaction_id": tx_ids}).merge(df_tx_filtered, on="transaction_id")
    tx_hour = df_tx_sorted["timestamp_dt"].dt.hour.values
    tx_day = df_tx_sorted["timestamp_dt"].dt.dayofweek.values
    tx_amount = df_tx_sorted["amount"].values.astype(np.float32)
    
    # Cyclical encodings
    sin_hour = np.sin(2 * np.pi * tx_hour / 24.0)
    cos_hour = np.cos(2 * np.pi * tx_hour / 24.0)
    sin_day = np.sin(2 * np.pi * tx_day / 7.0)
    cos_day = np.cos(2 * np.pi * tx_day / 7.0)
    
    tx_x = np.column_stack([tx_amount, sin_hour, cos_hour, sin_day, cos_day]).astype(np.float32)
    
    # Scale transaction amount using a simple log scale or standard scale
    tx_x[:, 0] = np.log1p(tx_x[:, 0]) # Log transform amount
    data["transaction"].x = torch.tensor(tx_x, dtype=torch.float32)
    
    # Device and IP Features (constant feature vectors since featureless)
    data["device"].x = torch.ones((len(dev_ids), 1), dtype=torch.float32)
    data["ip"].x = torch.ones((len(ip_ids), 1), dtype=torch.float32)
    
    # Coupon Features (discount_percentage scaled)
    df_coupons_sorted = pd.DataFrame({"coupon_id": coupon_ids}).merge(df_coupons, on="coupon_id")
    coupon_x = (df_coupons_sorted["discount_percentage"].values / 100.0).astype(np.float32).reshape(-1, 1)
    data["coupon"].x = torch.tensor(coupon_x, dtype=torch.float32)
    
    # 5. Construct Relationships (Edge Indices)
    # USES_DEVICE (Customer -> Device)
    cust_dev_src, cust_dev_dst = [], []
    for _, row in df_visible_custs.iterrows():
        cust_dev_src.append(cust_id_to_idx[row["customer_id"]])
        cust_dev_dst.append(dev_id_to_idx[row["device_id"]])
    data["customer", "uses_device", "device"].edge_index = torch.tensor(
        [cust_dev_src, cust_dev_dst], dtype=torch.long
    )
    
    # USES_IP (Customer -> IP)
    cust_ip_src, cust_ip_dst = [], []
    for _, row in df_visible_custs.iterrows():
        cust_ip_src.append(cust_id_to_idx[row["customer_id"]])
        cust_ip_dst.append(ip_id_to_idx[row["ip_address"]])
    data["customer", "uses_ip", "ip"].edge_index = torch.tensor(
        [cust_ip_src, cust_ip_dst], dtype=torch.long
    )
    
    # MADE (Customer -> Transaction)
    cust_tx_src, cust_tx_dst = [], []
    for _, row in df_tx_filtered.iterrows():
        cust_tx_src.append(cust_id_to_idx[row["customer_id"]])
        cust_tx_dst.append(tx_id_to_idx[row["transaction_id"]])
    data["customer", "made", "transaction"].edge_index = torch.tensor(
        [cust_tx_src, cust_tx_dst], dtype=torch.long
    )
    
    # USED_COUPON (Customer -> Coupon)
    cust_cp_src, cust_cp_dst = [], []
    df_tx_coupon = df_tx_filtered[df_tx_filtered["coupon_id"].notna()]
    # Drop duplicates to only map unique Customer-Coupon pairs
    df_cust_cp_pairs = df_tx_coupon[["customer_id", "coupon_id"]].drop_duplicates()
    for _, row in df_cust_cp_pairs.iterrows():
        cust_cp_src.append(cust_id_to_idx[row["customer_id"]])
        cust_cp_dst.append(coupon_id_to_idx[row["coupon_id"]])
    data["customer", "used_coupon", "coupon"].edge_index = torch.tensor(
        [cust_cp_src, cust_cp_dst], dtype=torch.long
    )
    
    # REFERRED (Customer -> Customer)
    ref_src, ref_dst = [], []
    for _, row in df_ref_filtered.iterrows():
        ref_src.append(cust_id_to_idx[row["referrer_id"]])
        ref_dst.append(cust_id_to_idx[row["referred_id"]])
    data["customer", "referred", "customer"].edge_index = torch.tensor(
        [ref_src, ref_dst], dtype=torch.long
    )
    
    # APPLIED_COUPON (Transaction -> Coupon)
    tx_cp_src, tx_cp_dst = [], []
    for _, row in df_tx_coupon.iterrows():
        tx_cp_src.append(tx_id_to_idx[row["transaction_id"]])
        tx_cp_dst.append(coupon_id_to_idx[row["coupon_id"]])
    data["transaction", "applied_coupon", "coupon"].edge_index = torch.tensor(
        [tx_cp_src, tx_cp_dst], dtype=torch.long
    )
    
    return data, df_features_sorted, scaler

def get_temporal_datasets(data_dir):
    """Load the train, validation, and test graph snapshots and features."""
    
    # Fetch cutoffs
    # Cutoff timelines (exact dates from Phase 1)
    train_cutoff = "2025-09-13 12:00:00"
    val_cutoff = "2025-11-07 06:00:00"
    test_cutoff = "2025-12-31 23:59:59"
    
    print("Building training graph snapshot G_train...")
    train_data, train_df, scaler = build_heterodata_snapshot(
        data_dir, train_cutoff, "train", scaler=None
    )
    
    print("Building validation graph snapshot G_val...")
    val_data, val_df, _ = build_heterodata_snapshot(
        data_dir, val_cutoff, "val", scaler=scaler
    )
    
    print("Building testing graph snapshot G_test...")
    test_data, test_df, _ = build_heterodata_snapshot(
        data_dir, test_cutoff, "test", scaler=scaler
    )
    
    return {
        "train": (train_data, train_df),
        "val": (val_data, val_df),
        "test": (test_data, test_df)
    }
