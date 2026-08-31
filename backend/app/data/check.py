import os
import json
import pandas as pd
from datetime import datetime

def check_signal_overlap(customers, transactions, referrals):
    """Verify that individual signals overlap between legitimate and abuse users,
    so they cannot be trivially separated by a single feature."""
    print("Running Behavioral Overlap and Realism Checks...")
    
    # 1. Device sharing
    device_counts = customers['device_id'].value_counts()
    shared_devices = set(device_counts[device_counts > 1].index)
    customers['shares_device'] = customers['device_id'].isin(shared_devices)
    
    legit_share_dev = customers[~customers['is_abuse']]['shares_device'].mean()
    abuse_share_dev = customers[customers['is_abuse']]['shares_device'].mean()
    
    print(f"  - Device sharing rate: Legitimate = {legit_share_dev:.2%}, Abuse = {abuse_share_dev:.2%}")
    
    # 2. IP sharing
    ip_counts = customers['ip_address'].value_counts()
    shared_ips = set(ip_counts[ip_counts > 1].index)
    customers['shares_ip'] = customers['ip_address'].isin(shared_ips)
    
    legit_share_ip = customers[~customers['is_abuse']]['shares_ip'].mean()
    abuse_share_ip = customers[customers['is_abuse']]['shares_ip'].mean()
    
    print(f"  - IP sharing rate: Legitimate = {legit_share_ip:.2%}, Abuse = {abuse_share_ip:.2%}")
    
    # 3. Referral rates
    referred_custs = set(referrals['referred_id'])
    referring_custs = set(referrals['referrer_id'])
    
    customers['has_referred'] = customers['customer_id'].isin(referring_custs)
    customers['was_referred'] = customers['customer_id'].isin(referred_custs)
    
    legit_was_referred = customers[~customers['is_abuse']]['was_referred'].mean()
    abuse_was_referred = customers[customers['is_abuse']]['was_referred'].mean()
    
    print(f"  - Referral rate (was referred): Legitimate = {legit_was_referred:.2%}, Abuse = {abuse_was_referred:.2%}")
    
    # 4. Coupon usage rate
    used_coupon_custs = set(transactions[transactions['coupon_id'].notna()]['customer_id'])
    customers['used_coupon'] = customers['customer_id'].isin(used_coupon_custs)
    
    legit_used_coupon = customers[~customers['is_abuse']]['used_coupon'].mean()
    abuse_used_coupon = customers[customers['is_abuse']]['used_coupon'].mean()
    
    print(f"  - Coupon usage rate: Legitimate = {legit_used_coupon:.2%}, Abuse = {abuse_used_coupon:.2%}")
    
    # Overlap Assertions (verify no single feature separates groups perfectly)
    assert legit_share_dev > 0.01, f"Legitimate device sharing is too low: {legit_share_dev:.4%}"
    assert legit_share_ip > 0.01, f"Legitimate IP sharing is too low: {legit_share_ip:.4%}"
    assert legit_was_referred > 0.05, f"Legitimate referral rate is too low: {legit_was_referred:.4%}"
    assert legit_used_coupon > 0.05, f"Legitimate coupon usage is too low: {legit_used_coupon:.4%}"
    
    # Check that fraud doesn't have 100% or 0% values on these single features
    assert abuse_share_dev < 0.99, "Abuse device sharing is 100% (should have distributed rings that don't share)"
    assert abuse_share_dev > 0.10, "Abuse device sharing is too low"
    assert abuse_share_ip < 0.99, "Abuse IP sharing is 100% (should have distributed rings that don't share)"
    assert abuse_share_ip > 0.10, "Abuse IP sharing is too low"
    
    print("  => SUCCESS: Strong behavioral overlaps confirmed. No single feature is a trivial predictor.")
    return True

def run_validation_checks(data_dir):
    """Load and validate the synthetic dataset files."""
    print("Starting validation checks on generated CSV files...")
    
    # Check file existence
    required_files = ['customers.csv', 'transactions.csv', 'referrals.csv', 'coupons.csv', 'ground_truth.csv', 'dataset_summary.json']
    for f in required_files:
        path = os.path.join(data_dir, f)
        if not os.path.exists(path):
            print(f"ERROR: Missing file {path}")
            return False
            
    # Load DataFrames
    customers = pd.read_csv(os.path.join(data_dir, 'customers.csv'))
    transactions = pd.read_csv(os.path.join(data_dir, 'transactions.csv'))
    referrals = pd.read_csv(os.path.join(data_dir, 'referrals.csv'))
    coupons = pd.read_csv(os.path.join(data_dir, 'coupons.csv'))
    ground_truth = pd.read_csv(os.path.join(data_dir, 'ground_truth.csv'))
    
    with open(os.path.join(data_dir, 'dataset_summary.json'), 'r') as sf:
        summary = json.load(sf)
        
    print("Verifying Row Counts and Scale...")
    print(f"  - Customers: {len(customers)} (expected ~50,000)")
    print(f"  - Transactions: {len(transactions)} (expected ~300,000)")
    print(f"  - Devices: {customers['device_id'].nunique()} (expected ~35,000)")
    print(f"  - IPs: {customers['ip_address'].nunique()} (expected ~40,000)")
    print(f"  - Coupons: {len(coupons)} (expected 50)")
    print(f"  - Referrals: {len(referrals)} (expected 30,000–50,000)")
    print(f"  - Abuse Rings: {summary['number_of_abuse_rings']} (expected 100–150)")
    
    # Scale validation assertions
    assert 45000 <= len(customers) <= 55000, f"Customer count {len(customers)} out of range"
    assert 250000 <= len(transactions) <= 350000, f"Transaction count {len(transactions)} out of range"
    assert 30000 <= customers['device_id'].nunique() <= 40000, f"Device count out of range"
    assert 35000 <= customers['ip_address'].nunique() <= 45000, f"IP count out of range"
    assert len(coupons) == 50, f"Coupon count is {len(coupons)} (expected 50)"
    assert 30000 <= len(referrals) <= 50000, f"Referral count {len(referrals)} out of range"
    assert 100 <= summary['number_of_abuse_rings'] <= 150, f"Abuse rings count {summary['number_of_abuse_rings']} out of range"
    
    # 1. Uniqueness Checks
    print("Checking uniqueness constraints...")
    assert customers['customer_id'].is_unique, "Customer IDs must be unique"
    assert transactions['transaction_id'].is_unique, "Transaction IDs must be unique"
    assert coupons['coupon_id'].is_unique, "Coupon IDs must be unique"
    assert ground_truth['customer_id'].is_unique, "Ground truth customer IDs must be unique"
    
    # 2. Foreign Key Integrity
    print("Checking foreign key constraints...")
    cust_ids = set(customers['customer_id'])
    coupon_ids = set(coupons['coupon_id'])
    
    # Transactions keys
    tx_cust_ids = set(transactions['customer_id'])
    assert tx_cust_ids.issubset(cust_ids), "Some transactions reference non-existent customers"
    
    tx_coupon_ids = set(transactions['coupon_id'].dropna())
    assert tx_coupon_ids.issubset(coupon_ids), "Some transactions reference non-existent coupons"
    
    # Referrals keys
    ref_referrer_ids = set(referrals['referrer_id'])
    ref_referred_ids = set(referrals['referred_id'])
    assert ref_referrer_ids.issubset(cust_ids), "Some referrers do not exist in customers"
    assert ref_referred_ids.issubset(cust_ids), "Some referred customers do not exist in customers"
    
    # Ground truth keys
    gt_cust_ids = set(ground_truth['customer_id'])
    assert gt_cust_ids == cust_ids, "Ground truth and customer IDs must match exactly"
    
    # 3. Ground truth consistency
    print("Checking ground truth consistency...")
    merged_cust = customers.merge(ground_truth, on='customer_id')
    
    # Rings consistency
    abuse_custs = merged_cust[merged_cust['is_abuse']]
    legit_custs = merged_cust[~merged_cust['is_abuse']]
    
    assert legit_custs['ring_id'].isna().all(), "Legitimate customers must not have a ring_id"
    assert legit_custs['abuse_type'].isna().all(), "Legitimate customers must not have an abuse_type"
    
    # Each abuse customer should be in a ring and have an abuse type
    assert abuse_custs['ring_id'].notna().all(), "All abuse customers must have a ring_id"
    assert abuse_custs['abuse_type'].notna().all(), "All abuse customers must have an abuse_type"
    
    # Verify that ring members exist
    ring_members_counts = abuse_custs['ring_id'].value_counts()
    assert (ring_members_counts >= 2).all(), "All abuse rings must contain at least 2 members"
    
    # 4. Temporal Validity
    print("Checking temporal constraints...")
    
    # Account registration vs transactions
    cust_reg = customers.set_index('customer_id')['account_created_at'].to_dict()
    
    # Parse transaction timestamps
    tx_times = transactions['timestamp'].apply(lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M:%S"))
    for idx, row in transactions.iterrows():
        c_id = row['customer_id']
        c_reg = datetime.strptime(cust_reg[c_id], "%Y-%m-%d %H:%M:%S")
        tx_t = tx_times.iloc[idx]
        assert c_reg <= tx_t, f"Transaction timestamp {tx_t} is before registration {c_reg} for customer {c_id}"
        
    # Referrer registration vs referred registration
    for _, row in referrals.iterrows():
        referrer = row['referrer_id']
        referred = row['referred_id']
        ref_time = datetime.strptime(row['timestamp'], "%Y-%m-%d %H:%M:%S")
        
        referrer_reg = datetime.strptime(cust_reg[referrer], "%Y-%m-%d %H:%M:%S")
        referred_reg = datetime.strptime(cust_reg[referred], "%Y-%m-%d %H:%M:%S")
        
        assert referrer_reg <= referred_reg, f"Referrer {referrer} registered after referee {referred}"
        assert abs((referred_reg - ref_time).total_seconds()) < 1.0, f"Referral timestamp {ref_time} does not match referee registration time {referred_reg}"
        
    # Coupon usage timeline
    coupon_valid_from = coupons.set_index('coupon_id')['valid_from'].to_dict()
    coupon_valid_until = coupons.set_index('coupon_id')['valid_until'].to_dict()
    
    for _, row in transactions[transactions['coupon_id'].notna()].iterrows():
        cp_id = row['coupon_id']
        tx_t = datetime.strptime(row['timestamp'], "%Y-%m-%d %H:%M:%S")
        c_from = datetime.strptime(coupon_valid_from[cp_id], "%Y-%m-%d %H:%M:%S")
        c_until = datetime.strptime(coupon_valid_until[cp_id], "%Y-%m-%d %H:%M:%S")
        assert c_from <= tx_t <= c_until, f"Coupon {cp_id} was used outside valid range {c_from} to {c_until} at {tx_t}"
        
    # 5. Signal Overlap Checks
    check_signal_overlap(merged_cust, transactions, referrals)
    
    # 6. Fraud proportion
    abuse_proportion = summary['number_of_abuse_customers'] / len(customers)
    print(f"  - Coordinated abuse rate: {abuse_proportion:.2%} (expected 7-10%)")
    assert 0.07 <= abuse_proportion <= 0.10, f"Abuse rate {abuse_proportion:.4%} is not in [7%, 10%]"
    
    print("\n>>> ALL VALIDATION CHECKS PASSED SUCCESSFULLY! <<<\n")
    return True

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-dir', default='backend/data/generated', help='Path to directory containing generated CSVs')
    args = parser.parse_args()
    
    if os.path.exists(args.data_dir):
        run_validation_checks(args.data_dir)
    else:
        print(f"Data directory {args.data_dir} does not exist.")
