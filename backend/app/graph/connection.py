import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load environment variables from .env file
load_dotenv()

# Credentials loaded from env variables with standard local docker fallbacks
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "testpassword123")

_driver = None

def get_driver():
    """Get or initialize the Neo4j driver connection pool."""
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    return _driver

def close_driver():
    """Safely close the Neo4j driver connection pool."""
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None
