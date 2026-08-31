from app.graph.connection import get_driver

def create_constraints():
    """Ensure Neo4j uniqueness constraints and indexes are established."""
    driver = get_driver()
    with driver.session() as session:
        # Constraints in Neo4j guarantee both indexing and uniqueness
        print("Ensuring unique constraints exist...")
        
        session.run(
            "CREATE CONSTRAINT customer_id_unique IF NOT EXISTS "
            "FOR (c:Customer) REQUIRE c.customer_id IS UNIQUE"
        )
        
        session.run(
            "CREATE CONSTRAINT transaction_id_unique IF NOT EXISTS "
            "FOR (t:Transaction) REQUIRE t.transaction_id IS UNIQUE"
        )
        
        session.run(
            "CREATE CONSTRAINT device_id_unique IF NOT EXISTS "
            "FOR (d:Device) REQUIRE d.device_id IS UNIQUE"
        )
        
        session.run(
            "CREATE CONSTRAINT ip_address_unique IF NOT EXISTS "
            "FOR (i:IP) REQUIRE i.ip_address IS UNIQUE"
        )
        
        session.run(
            "CREATE CONSTRAINT coupon_id_unique IF NOT EXISTS "
            "FOR (co:Coupon) REQUIRE co.coupon_id IS UNIQUE"
        )
        
        print("Constraints initialized successfully.")

if __name__ == "__main__":
    create_constraints()
