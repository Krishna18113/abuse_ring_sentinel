import os
import argparse
from app.graph.connection import get_driver, close_driver

def get_customer_neighborhood(customer_id):
    """Retrieve all direct connections and attributes of a single customer."""
    driver = get_driver()
    query = """
    MATCH (c:Customer {customer_id: $customer_id})
    OPTIONAL MATCH (c)-[:USES_DEVICE]->(d:Device)
    OPTIONAL MATCH (c)-[:USES_IP]->(ip:IP)
    OPTIONAL MATCH (c)-[:USED_COUPON]->(co:Coupon)
    OPTIONAL MATCH (referrer:Customer)-[:REFERRED]->(c)
    OPTIONAL MATCH (c)-[:REFERRED]->(referred:Customer)
    OPTIONAL MATCH (c)-[:MADE]->(t:Transaction)
    RETURN c.customer_id AS customer_id,
           c.account_created_at AS account_created_at,
           c.location AS location,
           c.split AS split,
           collect(distinct d.device_id) AS devices,
           collect(distinct ip.ip_address) AS ips,
           collect(distinct co.coupon_id) AS coupons,
           referrer.customer_id AS referrer_id,
           collect(distinct referred.customer_id) AS referred_ids,
           count(distinct t) AS transaction_count
    """
    with driver.session() as session:
        result = session.run(query, {"customer_id": customer_id})
        return result.single()

def get_customers_sharing_device(device_id):
    """Retrieve pairs of customers sharing a specific device."""
    driver = get_driver()
    query = """
    MATCH (c1:Customer)-[:USES_DEVICE]->(d:Device {device_id: $device_id})<-[:USES_DEVICE]-(c2:Customer)
    WHERE c1.customer_id < c2.customer_id
    RETURN c1.customer_id AS customer_1, c2.customer_id AS customer_2
    """
    with driver.session() as session:
        result = session.run(query, {"device_id": device_id})
        return [dict(record) for record in result]

def get_customers_sharing_ip(ip_address):
    """Retrieve pairs of customers sharing a specific IP address."""
    driver = get_driver()
    query = """
    MATCH (c1:Customer)-[:USES_IP]->(ip:IP {ip_address: $ip_address})<-[:USES_IP]-(c2:Customer)
    WHERE c1.customer_id < c2.customer_id
    RETURN c1.customer_id AS customer_1, c2.customer_id AS customer_2
    """
    with driver.session() as session:
        result = session.run(query, {"ip_address": ip_address})
        return [dict(record) for record in result]

def get_customers_using_coupon(coupon_id):
    """Retrieve pairs of customers who used the same coupon."""
    driver = get_driver()
    query = """
    MATCH (c1:Customer)-[:USED_COUPON]->(co:Coupon {coupon_id: $coupon_id})<-[:USED_COUPON]-(c2:Customer)
    WHERE c1.customer_id < c2.customer_id
    RETURN c1.customer_id AS customer_1, c2.customer_id AS customer_2
    """
    with driver.session() as session:
        result = session.run(query, {"coupon_id": coupon_id})
        return [dict(record) for record in result]

def get_referrals(customer_id):
    """Retrieve immediate referral relationships for a customer."""
    driver = get_driver()
    query = """
    MATCH (referrer:Customer)-[r:REFERRED]->(referred:Customer)
    WHERE referrer.customer_id = $customer_id OR referred.customer_id = $customer_id
    RETURN referrer.customer_id AS referrer_id, referred.customer_id AS referred_id, r.timestamp AS timestamp
    """
    with driver.session() as session:
        result = session.run(query, {"customer_id": customer_id})
        return [dict(record) for record in result]

def get_highly_connected_referral_components(limit=5):
    """Retrieve customers with unusually high referral out-degree (hubs)."""
    driver = get_driver()
    query = """
    MATCH (referrer:Customer)-[:REFERRED]->(referred:Customer)
    RETURN referrer.customer_id AS referrer_id, count(referred) AS referral_count
    ORDER BY referral_count DESC
    LIMIT $limit
    """
    with driver.session() as session:
        result = session.run(query, {"limit": limit})
        return [dict(record) for record in result]

def get_customers_with_multiple_connections(limit=5):
    """Retrieve pairs of customers sharing both device and coupon infrastructure."""
    driver = get_driver()
    query = """
    MATCH (c1:Customer)-[:USES_DEVICE]->(d:Device)<-[:USES_DEVICE]-(c2:Customer)
    MATCH (c1)-[:USED_COUPON]->(co:Coupon)<-[:USED_COUPON]-(c2)
    WHERE c1.customer_id < c2.customer_id
    RETURN c1.customer_id AS customer_1, c2.customer_id AS customer_2, d.device_id AS shared_device, co.coupon_id AS shared_coupon
    LIMIT $limit
    """
    with driver.session() as session:
        result = session.run(query, {"limit": limit})
        return [dict(record) for record in result]

def get_temporally_correlated_transactions(threshold_seconds=60, limit=5):
    """Find transactions from device-sharing customers occurring within a tight time window."""
    driver = get_driver()
    query = """
    MATCH (c1:Customer)-[:MADE]->(t1:Transaction)
    MATCH (c2:Customer)-[:MADE]->(t2:Transaction)
    MATCH (c1)-[:USES_DEVICE]->(d:Device)<-[:USES_DEVICE]-(c2)
    WHERE c1.customer_id < c2.customer_id
      AND abs(duration.inSeconds(datetime(replace(t1.timestamp, ' ', 'T')), datetime(replace(t2.timestamp, ' ', 'T'))).seconds) <= $threshold_seconds
    RETURN c1.customer_id AS customer_1, 
           c2.customer_id AS customer_2, 
           t1.transaction_id AS tx_1, 
           t2.transaction_id AS tx_2, 
           t1.timestamp AS time_1, 
           t2.timestamp AS time_2
    LIMIT $limit
    """
    with driver.session() as session:
        result = session.run(query, {"threshold_seconds": threshold_seconds, "limit": limit})
        return [dict(record) for record in result]

def get_suspicious_clusters_by_structure(limit=5):
    """Retrieve referral pairs who also share both device and IP infrastructure."""
    driver = get_driver()
    query = """
    MATCH (c1:Customer)-[:REFERRED]->(c2:Customer)
    MATCH (c1)-[:USES_DEVICE]->(d:Device)<-[:USES_DEVICE]-(c2)
    MATCH (c1)-[:USES_IP]->(ip:IP)<-[:USES_IP]-(c2)
    RETURN c1.customer_id AS customer_1, c2.customer_id AS customer_2, d.device_id AS shared_device, ip.ip_address AS shared_ip
    LIMIT $limit
    """
    with driver.session() as session:
        result = session.run(query, {"limit": limit})
        return [dict(record) for record in result]

def inspect_customer(customer_id):
    """Print a clean layout of a single customer's neighborhood."""
    res = get_customer_neighborhood(customer_id)
    if not res:
        print(f"Customer {customer_id} not found in the database.")
        return
        
    print(f"\n==========================================")
    print(f"Customer: {res['customer_id']}")
    print(f"==========================================")
    print(f"Account Created: {res['account_created_at']}")
    print(f"Location:        {res['location']}")
    print(f"Split:           {res['split']}")
    
    print("\nDevices:")
    for d in res['devices']:
        print(f"  - {d}")
        
    print("\nIPs:")
    for ip in res['ips']:
        print(f"  - {ip}")
        
    print("\nCoupons:")
    for co in res['coupons']:
        print(f"  - {co}")
        
    print("\nReferrals:")
    if res['referrer_id']:
        print(f"  Referrer: {res['referrer_id']}")
    else:
        print("  Referrer: None")
    if res['referred_ids']:
        print(f"  Referred ({len(res['referred_ids'])} customers):")
        for ref in res['referred_ids'][:5]:
            print(f"    - {ref}")
        if len(res['referred_ids']) > 5:
            print("    - ...")
    else:
        print("  Referred: None")
        
    print(f"\nTransactions: {res['transaction_count']} total")
    print(f"==========================================\n")

def print_multi_customer_components():
    """Print examples of highly connected structural patterns in the graph."""
    print("\n--- Highly Connected Referral Hubs (Referrals count) ---")
    hubs = get_highly_connected_referral_components(3)
    for h in hubs:
        print(f"  Customer {h['referrer_id']} referred {h['referral_count']} other customers.")
        
    print("\n--- Multi-signal sharing (Device + Coupon) ---")
    shares = get_customers_with_multiple_connections(3)
    for s in shares:
        print(f"  Customer {s['customer_1']} and {s['customer_2']} shared device {s['shared_device']} and coupon {s['shared_coupon']}.")
        
    print("\n--- Suspicious-looking Clusters (Referral + Shared Device + Shared IP) ---")
    clusters = get_suspicious_clusters_by_structure(3)
    for c in clusters:
        print(f"  Referral pair ({c['customer_1']} -> {c['customer_2']}) shares device {c['shared_device']} and IP {c['shared_ip']}.")
        
    print("\n--- Temporally Correlated Transactions (<= 60s, same device) ---")
    txs = get_temporally_correlated_transactions(60, 3)
    for t in txs:
        print(f"  Customers ({t['customer_1']}, {t['customer_2']}) transacted at [{t['time_1']}] and [{t['time_2']}] (Diff <= 60s) sharing device.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query Neo4j Graph for investigation.")
    parser.add_argument("--inspect-customer", type=str, default=None, help="Customer ID to inspect")
    parser.add_argument("--inspect-components", action="store_true", help="Print examples of multi-customer components")
    args = parser.parse_args()
    
    if args.inspect_customer:
        inspect_customer(args.inspect_customer)
    elif args.inspect_components:
        print_multi_customer_components()
    else:
        # Default helper print
        inspect_customer("C_00042")
        print_multi_customer_components()
        
    close_driver()
