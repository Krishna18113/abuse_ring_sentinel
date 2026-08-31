from app.graph.connection import get_driver

def run_query(query, parameters=None):
    """Utility helper to execute a Cypher query with parameters."""
    driver = get_driver()
    with driver.session() as session:
        result = session.run(query, parameters or {})
        return [record.data() for record in result]

def query_shared_devices(customer_id: str):
    """Find other customers sharing the same device as the target customer."""
    query = """
    MATCH (c:Customer {customer_id: $customer_id})-[:USES_DEVICE]->(d:Device)
    MATCH (other:Customer)-[:USES_DEVICE]->(d)
    WHERE c <> other
    OPTIONAL MATCH (other)-[:MADE]->(t:Transaction)
    RETURN d.device_id AS device_id, 
           count(distinct other.customer_id) AS customer_count,
           collect(distinct other.customer_id) AS connected_customers,
           count(distinct t.transaction_id) AS transaction_count
    """
    return run_query(query, {"customer_id": customer_id})

def query_shared_ips(customer_id: str):
    """Find other customers sharing the same IP as the target customer."""
    query = """
    MATCH (c:Customer {customer_id: $customer_id})-[:USES_IP]->(ip:IP)
    MATCH (other:Customer)-[:USES_IP]->(ip)
    WHERE c <> other
    OPTIONAL MATCH (other)-[:MADE]->(t:Transaction)
    RETURN ip.ip_address AS ip_address, 
           count(distinct other.customer_id) AS customer_count,
           collect(distinct other.customer_id) AS connected_customers,
           count(distinct t.transaction_id) AS transaction_count
    """
    return run_query(query, {"customer_id": customer_id})

def query_coupon_coordination(customer_id: str):
    """Find coupons used by the customer and other customers using them, checking infrastructure overlaps."""
    query = """
    MATCH (c:Customer {customer_id: $customer_id})-[:USED_COUPON]->(co:Coupon)
    MATCH (other:Customer)-[:USED_COUPON]->(co)
    WHERE c <> other
    OPTIONAL MATCH (c)-[:USES_DEVICE]->(d:Device)<-[:USES_DEVICE]-(other)
    OPTIONAL MATCH (c)-[:USES_IP]->(ip:IP)<-[:USES_IP]-(other)
    RETURN co.coupon_id AS coupon_id,
           count(distinct other.customer_id) AS customer_count,
           collect(distinct other.customer_id) AS connected_customers,
           count(distinct d) AS shared_device_count,
           count(distinct ip) AS shared_ip_count
    """
    return run_query(query, {"customer_id": customer_id})

def query_referrals(customer_id: str):
    """Investigate referral in-degree, out-degree, and component size (bounded depth 1..3)."""
    # 1. Incoming referral
    query_in = """
    MATCH (referrer:Customer)-[:REFERRED]->(c:Customer {customer_id: $customer_id})
    RETURN referrer.customer_id AS referrer_id
    """
    res_in = run_query(query_in, {"customer_id": customer_id})
    referrer_id = res_in[0]["referrer_id"] if res_in else None
    
    # 2. Outgoing referrals
    query_out = """
    MATCH (c:Customer {customer_id: $customer_id})-[:REFERRED]->(referred:Customer)
    RETURN collect(referred.customer_id) AS referred_ids
    """
    res_out = run_query(query_out, {"customer_id": customer_id})
    referred_ids = res_out[0]["referred_ids"] if res_out else []
    
    # 3. Referral component size (bounded to 3 hops)
    query_size = """
    MATCH (c:Customer {customer_id: $customer_id})
    OPTIONAL MATCH path = (c)-[:REFERRED*1..3]-(other:Customer)
    RETURN count(distinct other.customer_id) + 1 AS referral_component_size
    """
    res_size = run_query(query_size, {"customer_id": customer_id})
    comp_size = res_size[0]["referral_component_size"] if res_size else 1
    
    return {
        "referrer_id": referrer_id,
        "referred_ids": referred_ids,
        "referral_in_degree": 1 if referrer_id else 0,
        "referral_out_degree": len(referred_ids),
        "referral_component_size": comp_size
    }

def query_multi_signal_connections(customer_id: str):
    """Find other customers connected to the target customer through multiple signals."""
    query = """
    MATCH (c:Customer {customer_id: $customer_id})
    OPTIONAL MATCH (c)-[:USES_DEVICE]->(d:Device)<-[:USES_DEVICE]-(other:Customer)
    WITH c, other, collect(distinct d.device_id) AS shared_devices
    OPTIONAL MATCH (c)-[:USES_IP]->(ip:IP)<-[:USES_IP]-(other)
    WITH c, other, shared_devices, collect(distinct ip.ip_address) AS shared_ips
    OPTIONAL MATCH (c)-[:REFERRED]-(other)
    WITH c, other, shared_devices, shared_ips, count(distinct other) > 0 AS has_referral
    OPTIONAL MATCH (c)-[:USED_COUPON]->(co:Coupon)<-[:USED_COUPON]-(other)
    WITH c, other, shared_devices, shared_ips, has_referral, collect(distinct co.coupon_id) AS shared_coupons
    WHERE other IS NOT NULL AND other <> c
    RETURN other.customer_id AS connected_customer,
           shared_devices,
           shared_ips,
           has_referral,
           shared_coupons
    """
    return run_query(query, {"customer_id": customer_id})

def query_temporal_coordination(customer_id: str):
    """Find transaction timing overlaps among infrastructure-sharing connected customers within 15 mins."""
    query = """
    MATCH (c:Customer {customer_id: $customer_id})-[:MADE]->(t1:Transaction)
    MATCH (c)-[:USES_DEVICE|USES_IP]->(infra)<-[:USES_DEVICE|USES_IP]-(other:Customer)
    WHERE c <> other
    MATCH (other)-[:MADE]->(t2:Transaction)
    WITH other, t1, t2,
         abs(duration.inSeconds(datetime(replace(t1.timestamp, ' ', 'T')), datetime(replace(t2.timestamp, ' ', 'T'))).seconds) AS time_diff
    WHERE time_diff <= 900
    RETURN other.customer_id AS connected_customer,
           t1.transaction_id AS target_tx_id,
           t1.timestamp AS target_tx_time,
           t1.amount AS target_tx_amount,
           t2.transaction_id AS other_tx_id,
           t2.timestamp AS other_tx_time,
           t2.amount AS other_tx_amount,
           time_diff
    """
    return run_query(query, {"customer_id": customer_id})

def query_basic_behavior(customer_id: str):
    """Query basic behavior metrics (transactions, amounts, coupons, referrals, created_at) from Neo4j."""
    query = """
    MATCH (c:Customer {customer_id: $customer_id})
    OPTIONAL MATCH (c)-[:MADE]->(t:Transaction)
    OPTIONAL MATCH (c)-[:USED_COUPON]->(co:Coupon)
    OPTIONAL MATCH (c)-[:REFERRED]->(referred:Customer)
    RETURN c.account_created_at AS account_created_at,
           count(distinct t) AS transaction_count,
           coalesce(sum(t.amount), 0.0) AS total_amount,
           coalesce(avg(t.amount), 0.0) AS avg_amount,
           count(distinct co) AS coupon_usage_count,
           count(distinct referred) AS referrals_made
    """
    res = run_query(query, {"customer_id": customer_id})
    if res:
        return res[0]
    return {
        "account_created_at": "Active",
        "transaction_count": 0,
        "total_amount": 0.0,
        "avg_amount": 0.0,
        "coupon_usage_count": 0,
        "referrals_made": 0
    }
