import os
import argparse
import numpy as np
import pandas as pd
from app.graph.connection import get_driver, close_driver
from app.graph.schema import create_constraints

def run_query_in_batches(session, query, data_list, batch_size=5000, description=""):
    """Execute a cypher query in batches on a list of dictionary parameters."""
    total = len(data_list)
    print(f"Ingesting {description}: {total} rows total...")
    
    for i in range(0, total, batch_size):
        batch = data_list[i : i + batch_size]
        # Replace numpy NaN with None for Cypher compatibility
        cleaned_batch = []
        for row in batch:
            cleaned_row = {}
            for k, v in row.items():
                if pd.isna(v):
                    cleaned_row[k] = None
                else:
                    # Convert numpy ints/floats to python native types
                    if isinstance(v, (np.integer, np.int64)):
                        cleaned_row[k] = int(v)
                    elif isinstance(v, (np.floating, np.float64)):
                        cleaned_row[k] = float(v)
                    else:
                        cleaned_row[k] = v
            cleaned_batch.append(cleaned_row)
            
        session.run(query, {"batch": cleaned_batch})
        progress = min(i + batch_size, total)
        print(f"  Processed {progress}/{total}...")

def ingest_data(data_dir):
    """Orchestrate dataset ingestion into Neo4j Community Edition."""
    print(f"Reading dataset from {data_dir}...")
    
    df_customers = pd.read_csv(os.path.join(data_dir, "customers.csv"))
    df_transactions = pd.read_csv(os.path.join(data_dir, "transactions.csv"))
    df_referrals = pd.read_csv(os.path.join(data_dir, "referrals.csv"))
    df_coupons = pd.read_csv(os.path.join(data_dir, "coupons.csv"))
    
    driver = get_driver()
    
    # 1. Establish Schema Constraints
    create_constraints()
    
    with driver.session() as session:
        # Clear existing database for idempotency / fresh run if desired, or skip.
        # MERGE operations make ingestion safe to rerun, but we can also do a quick log.
        print("Starting batch ingestion...")
        
        # 2. Ingest Coupons
        coupons_list = df_coupons.to_dict("records")
        coupon_query = """
        UNWIND $batch AS row
        MERGE (co:Coupon {coupon_id: row.coupon_id})
        SET co.discount_percentage = toInteger(row.discount_percentage),
            co.campaign_id = row.campaign_id,
            co.valid_from = row.valid_from,
            co.valid_until = row.valid_until
        """
        run_query_in_batches(session, coupon_query, coupons_list, description="Coupon nodes")
        
        # 3. Ingest Customers
        customers_list = df_customers.to_dict("records")
        customer_query = """
        UNWIND $batch AS row
        MERGE (c:Customer {customer_id: row.customer_id})
        SET c.account_created_at = row.account_created_at,
            c.location = row.location,
            c.device_id = row.device_id,
            c.ip_address = row.ip_address,
            c.split = row.split
        """
        run_query_in_batches(session, customer_query, customers_list, description="Customer nodes")
        
        # 4. Ingest Devices & link them to Customers
        device_query = """
        UNWIND $batch AS row
        MATCH (c:Customer {customer_id: row.customer_id})
        MERGE (d:Device {device_id: row.device_id})
        MERGE (c)-[:USES_DEVICE]->(d)
        """
        run_query_in_batches(session, device_query, customers_list, description="Device nodes & USES_DEVICE relationships")
        
        # 5. Ingest IPs & link them to Customers
        ip_query = """
        UNWIND $batch AS row
        MATCH (c:Customer {customer_id: row.customer_id})
        MERGE (i:IP {ip_address: row.ip_address})
        MERGE (c)-[:USES_IP]->(i)
        """
        run_query_in_batches(session, ip_query, customers_list, description="IP nodes & USES_IP relationships")
        
        # 6. Ingest Transactions
        transactions_list = df_transactions.to_dict("records")
        tx_query = """
        UNWIND $batch AS row
        MERGE (t:Transaction {transaction_id: row.transaction_id})
        SET t.amount = toFloat(row.amount),
            t.timestamp = row.timestamp,
            t.product_id = row.product_id,
            t.payment_method = row.payment_method
        """
        run_query_in_batches(session, tx_query, transactions_list, description="Transaction nodes")
        
        # 7. Link Customers to Transactions (MADE relationship)
        made_query = """
        UNWIND $batch AS row
        MATCH (c:Customer {customer_id: row.customer_id})
        MATCH (t:Transaction {transaction_id: row.transaction_id})
        MERGE (c)-[:MADE]->(t)
        """
        run_query_in_batches(session, made_query, transactions_list, description="MADE relationships")
        
        # 8. Link Transactions & Customers to Coupons (APPLIED_COUPON and USED_COUPON relationships)
        coupon_link_query = """
        UNWIND $batch AS row
        WITH row WHERE row.coupon_id IS NOT NULL AND row.coupon_id <> ""
        MATCH (t:Transaction {transaction_id: row.transaction_id})
        MATCH (co:Coupon {coupon_id: row.coupon_id})
        MERGE (t)-[:APPLIED_COUPON]->(co)
        WITH row, co
        MATCH (c:Customer {customer_id: row.customer_id})
        MERGE (c)-[:USED_COUPON]->(co)
        """
        run_query_in_batches(session, coupon_link_query, transactions_list, description="APPLIED_COUPON & USED_COUPON relationships")
        
        # 9. Ingest Referrals (REFERRED relationship with timestamp)
        referrals_list = df_referrals.to_dict("records")
        referral_query = """
        UNWIND $batch AS row
        MATCH (referrer:Customer {customer_id: row.referrer_id})
        MATCH (referred:Customer {customer_id: row.referred_id})
        MERGE (referrer)-[r:REFERRED]->(referred)
        SET r.timestamp = row.timestamp
        """
        run_query_in_batches(session, referral_query, referrals_list, description="REFERRED relationships")

    print("\nIngestion completed successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest Phase 1 generated CSVs into Neo4j.")
    parser.add_argument("--data-dir", default="backend/data/generated", help="Path to directory containing generated CSVs")
    args = parser.parse_args()
    
    # Resolve relative path if needed
    data_dir = args.data_dir
    if not os.path.isabs(data_dir):
        # Resolve relative to backend/
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        data_dir = os.path.join(base_dir, data_dir)
        
    if os.path.exists(data_dir):
        ingest_data(data_dir)
        
        # Run validations
        from app.graph.validate import run_graph_validation
        run_graph_validation(data_dir)
    else:
        print(f"Data directory {data_dir} does not exist.")
        
    close_driver()
