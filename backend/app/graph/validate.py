import os
import json
import pandas as pd
from app.graph.connection import get_driver

def run_count_query(session, query, params=None):
    """Helper to run a query that returns a single count value."""
    result = session.run(query, params or {})
    single_record = result.single()
    return single_record[0] if single_record else 0

def run_graph_validation(data_dir):
    """Run referential, count, temporal, and structural validation checks on the Neo4j graph."""
    print("\n==============================================")
    print("=== Abuse Ring Sentinel — Graph Validation ===")
    print("==============================================")
    
    # Load source CSV files to get baseline counts
    df_customers = pd.read_csv(os.path.join(data_dir, "customers.csv"))
    df_transactions = pd.read_csv(os.path.join(data_dir, "transactions.csv"))
    df_referrals = pd.read_csv(os.path.join(data_dir, "referrals.csv"))
    df_coupons = pd.read_csv(os.path.join(data_dir, "coupons.csv"))
    df_gt = pd.read_csv(os.path.join(data_dir, "ground_truth.csv"))
    
    # Calculate expected count of USED_COUPON relationships
    # This is the number of unique (customer_id, coupon_id) pairs in transactions using a coupon
    expected_used_coupon = len(df_transactions[df_transactions["coupon_id"].notna()][["customer_id", "coupon_id"]].drop_duplicates())
    
    # Calculate expected count of APPLIED_COUPON relationships
    # This is the number of transactions using a coupon
    expected_applied_coupon = len(df_transactions[df_transactions["coupon_id"].notna()])

    driver = get_driver()
    with driver.session() as session:
        # 1. Node Counts
        print("Checking node counts...")
        db_customers = run_count_query(session, "MATCH (c:Customer) RETURN count(c)")
        db_transactions = run_count_query(session, "MATCH (t:Transaction) RETURN count(t)")
        db_devices = run_count_query(session, "MATCH (d:Device) RETURN count(d)")
        db_ips = run_count_query(session, "MATCH (i:IP) RETURN count(i)")
        db_coupons = run_count_query(session, "MATCH (co:Coupon) RETURN count(co)")
        
        expected_devices = df_customers["device_id"].nunique()
        expected_ips = df_customers["ip_address"].nunique()
        
        print(f"  Customers:    DB={db_customers:<8} CSV={len(df_customers)}")
        print(f"  Transactions: DB={db_transactions:<8} CSV={len(df_transactions)}")
        print(f"  Devices:      DB={db_devices:<8} CSV={expected_devices}")
        print(f"  IPs:          DB={db_ips:<8} CSV={expected_ips}")
        print(f"  Coupons:      DB={db_coupons:<8} CSV={len(df_coupons)}")
        
        assert db_customers == len(df_customers), "Customers node count mismatch"
        assert db_transactions == len(df_transactions), "Transactions node count mismatch"
        assert db_devices == expected_devices, "Devices node count mismatch"
        assert db_ips == expected_ips, "IPs node count mismatch"
        assert db_coupons == len(df_coupons), "Coupons node count mismatch"
        
        # 2. Relationship Counts
        print("\nChecking relationship counts...")
        db_made = run_count_query(session, "MATCH ()-[r:MADE]->() RETURN count(r)")
        db_uses_device = run_count_query(session, "MATCH ()-[r:USES_DEVICE]->() RETURN count(r)")
        db_uses_ip = run_count_query(session, "MATCH ()-[r:USES_IP]->() RETURN count(r)")
        db_used_coupon = run_count_query(session, "MATCH (c:Customer)-[r:USED_COUPON]->(co:Coupon) RETURN count(r)")
        db_referred = run_count_query(session, "MATCH ()-[r:REFERRED]->() RETURN count(r)")
        db_applied_coupon = run_count_query(session, "MATCH (t:Transaction)-[r:APPLIED_COUPON]->(co:Coupon) RETURN count(r)")
        
        print(f"  MADE:               DB={db_made:<8} CSV={len(df_transactions)}")
        print(f"  USES_DEVICE:        DB={db_uses_device:<8} CSV={len(df_customers)}")
        print(f"  USES_IP:            DB={db_uses_ip:<8} CSV={len(df_customers)}")
        print(f"  USED_COUPON:        DB={db_used_coupon:<8} CSV={expected_used_coupon}")
        print(f"  REFERRED:           DB={db_referred:<8} CSV={len(df_referrals)}")
        print(f"  APPLIED_COUPON:     DB={db_applied_coupon:<8} CSV={expected_applied_coupon}")
        
        assert db_made == len(df_transactions), "MADE relationships count mismatch"
        assert db_uses_device == len(df_customers), "USES_DEVICE relationships count mismatch"
        assert db_uses_ip == len(df_customers), "USES_IP relationships count mismatch"
        assert db_used_coupon == expected_used_coupon, "USED_COUPON relationships count mismatch"
        assert db_referred == len(df_referrals), "REFERRED relationships count mismatch"
        assert db_applied_coupon == expected_applied_coupon, "APPLIED_COUPON relationships count mismatch"
        
        # 3. Referential Integrity
        print("\nChecking referential integrity...")
        orphaned_tx = run_count_query(session, "MATCH (t:Transaction) WHERE NOT ()-[:MADE]->(t) RETURN count(t)")
        assert orphaned_tx == 0, f"Found {orphaned_tx} orphaned transactions"
        
        orphaned_device_rels = run_count_query(session, "MATCH (c:Customer) WHERE NOT (c)-[:USES_DEVICE]->() RETURN count(c)")
        assert orphaned_device_rels == 0, f"Found {orphaned_device_rels} customers without a device relationship"
        
        orphaned_ip_rels = run_count_query(session, "MATCH (c:Customer) WHERE NOT (c)-[:USES_IP]->() RETURN count(c)")
        assert orphaned_ip_rels == 0, f"Found {orphaned_ip_rels} customers without an IP relationship"
        
        # Referrals integrity (dangling links check)
        dangling_referrals = run_count_query(
            session, 
            "MATCH (c1)-[r:REFERRED]->(c2) WHERE NOT c1:Customer OR NOT c2:Customer RETURN count(r)"
        )
        assert dangling_referrals == 0, f"Found {dangling_referrals} referrals pointing to non-customer nodes"
        print("  Integrity:       PASS")
        
        # 4. Duplicate Checks
        print("\nChecking for duplicate relationships...")
        dup_uses_device = run_count_query(session, "MATCH (c:Customer)-[:USES_DEVICE]->(d:Device) WITH c, d, count(*) AS count WHERE count > 1 RETURN count(*)")
        dup_uses_ip = run_count_query(session, "MATCH (c:Customer)-[:USES_IP]->(i:IP) WITH c, i, count(*) AS count WHERE count > 1 RETURN count(*)")
        dup_made = run_count_query(session, "MATCH (c:Customer)-[:MADE]->(t:Transaction) WITH c, t, count(*) AS count WHERE count > 1 RETURN count(*)")
        dup_used_coupon = run_count_query(session, "MATCH (c:Customer)-[:USED_COUPON]->(co:Coupon) WITH c, co, count(*) AS count WHERE count > 1 RETURN count(*)")
        dup_referred = run_count_query(session, "MATCH (c1:Customer)-[:REFERRED]->(c2:Customer) WITH c1, c2, count(*) AS count WHERE count > 1 RETURN count(*)")
        dup_applied_coupon = run_count_query(session, "MATCH (t:Transaction)-[:APPLIED_COUPON]->(co:Coupon) WITH t, co, count(*) AS count WHERE count > 1 RETURN count(*)")
        
        assert dup_uses_device == 0, f"Found {dup_uses_device} duplicate USES_DEVICE relationships"
        assert dup_uses_ip == 0, f"Found {dup_uses_ip} duplicate USES_IP relationships"
        assert dup_made == 0, f"Found {dup_made} duplicate MADE relationships"
        assert dup_used_coupon == 0, f"Found {dup_used_coupon} duplicate USED_COUPON relationships"
        assert dup_referred == 0, f"Found {dup_referred} duplicate REFERRED relationships"
        assert dup_applied_coupon == 0, f"Found {dup_applied_coupon} duplicate APPLIED_COUPON relationships"
        print("  Duplicates:      PASS")
        
        # 5. Temporal Checks
        print("\nChecking temporal consistency...")
        bad_tx_time = run_count_query(
            session,
            "MATCH (c:Customer)-[:MADE]->(t:Transaction) "
            "WHERE t.timestamp < c.account_created_at "
            "RETURN count(t)"
        )
        assert bad_tx_time == 0, f"Found {bad_tx_time} transactions created before customer account registration"
        
        bad_ref_time = run_count_query(
            session,
            "MATCH (c1:Customer)-[r:REFERRED]->(c2:Customer) "
            "WHERE r.timestamp < c1.account_created_at OR r.timestamp < c2.account_created_at "
            "RETURN count(r)"
        )
        assert bad_ref_time == 0, f"Found {bad_ref_time} referrals occurring before referrer/referee registration"
        print("  Temporal checks: PASS")
        
        # 6. Abuse-Ring Structural Investigation (using Ground Truth mapping)
        print("\nChecking Abuse-Ring structures (exploratory)...")
        
        # Get list of fraud customer IDs
        abuse_ids = df_gt[df_gt["is_abuse"]]["customer_id"].tolist()
        
        # Find shared device infrastructure within fraud rings
        shared_devices_count = run_count_query(
            session,
            "MATCH (c1:Customer)-[:USES_DEVICE]->(d:Device)<-[:USES_DEVICE]-(c2:Customer) "
            "WHERE c1.customer_id IN $abuse_ids AND c2.customer_id IN $abuse_ids AND c1.customer_id < c2.customer_id "
            "RETURN count(distinct d)",
            {"abuse_ids": abuse_ids}
        )
        
        # Find shared IP infrastructure within fraud rings
        shared_ips_count = run_count_query(
            session,
            "MATCH (c1:Customer)-[:USES_IP]->(i:IP)<-[:USES_IP]-(c2:Customer) "
            "WHERE c1.customer_id IN $abuse_ids AND c2.customer_id IN $abuse_ids AND c1.customer_id < c2.customer_id "
            "RETURN count(distinct i)",
            {"abuse_ids": abuse_ids}
        )
        
        # Find multi-signal connections (e.g. shared device AND coupon)
        multi_signal_count = run_count_query(
            session,
            "MATCH (c1:Customer)-[:USES_DEVICE]->(d:Device)<-[:USES_DEVICE]-(c2:Customer) "
            "MATCH (c1)-[:USED_COUPON]->(co:Coupon)<-[:USED_COUPON]-(c2) "
            "WHERE c1.customer_id < c2.customer_id "
            "RETURN count(*)"
        )
        
        # Find temporal coordination
        temporal_coor_count = run_count_query(
            session,
            "MATCH (c1:Customer)-[:MADE]->(t1:Transaction) "
            "MATCH (c2:Customer)-[:MADE]->(t2:Transaction) "
            "MATCH (c1)-[:USES_DEVICE]->(d:Device)<-[:USES_DEVICE]-(c2) "
            "WHERE c1.customer_id < c2.customer_id "
            "  AND abs(duration.inSeconds(datetime(replace(t1.timestamp, ' ', 'T')), datetime(replace(t2.timestamp, ' ', 'T'))).seconds) <= 60 "
            "RETURN count(*)"
        )
        
        print(f"  Shared Devices found in fraud: {shared_devices_count}")
        print(f"  Shared IPs found in fraud:     {shared_ips_count}")
        print(f"  Multi-signal connections (Device + Coupon): {multi_signal_count}")
        print(f"  Temporally coordinated transactions (<=60s, same device): {temporal_coor_count}")
        
    print("\nOverall: PASS")
    return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="backend/data/generated", help="Path to directory containing generated CSVs")
    args = parser.parse_args()
    
    # Resolve relative path if needed
    data_dir = args.data_dir
    if not os.path.isabs(data_dir):
        # Resolve relative to backend/
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        data_dir = os.path.join(base_dir, data_dir)
        
    if os.path.exists(data_dir):
        run_graph_validation(data_dir)
        close_driver()
    else:
        print(f"Data directory {data_dir} does not exist.")
