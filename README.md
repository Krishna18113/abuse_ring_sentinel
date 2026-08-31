# Abuse Ring Sentinel

Abuse Ring Sentinel is a defense-only fraud and abuse detection system designed to detect coordinated promotional and referral abuse rings where multiple accounts coordinate to exploit a merchant.

---

## Technical Stack

- **Backend**: Python, FastAPI, PostgreSQL, Neo4j, PyTorch, PyTorch Geometric, NetworkX
- **Frontend**: React, TypeScript, Vite, Tailwind CSS, Recharts, React Flow / Cytoscape.js
- **Environment**: Docker & Docker Compose

---

## Getting Started

### Prerequisites

- Python 3.10+
- Docker & Docker Compose
- Virtual Environment (recommended)

Install python dependencies:
```bash
python -m pip install pandas numpy neo4j
```

---

## Phase 1: Synthetic Data Generation

The synthetic generator creates realistic transactions, referrals, devices, IPs, and coupons. It assigns complete fraud rings to specific temporal splits (Train/Val/Test) while allowing legitimate customers to span longitudinally across the year.

### Run Generation
```bash
python -m app.data.generate --seed 42
```
This script saves CSV files under `backend/data/generated/` and runs checks to ensure scale, temporal order, and referential integrity.

---

## Phase 2: Neo4j Graph Database

The synthetic dataset is converted into a heterogeneous graph inside Neo4j, representing customers, transactions, devices, IPs, coupons, and referral relationships.

### Graph Schema

```text
       (Device) <──── :USES_DEVICE ──── (Customer) ──── :USES_IP ────> (IP)
                                           │   │
                                           │   └──── :REFERRED ────> (Customer)
                                           │
                                         :MADE
                                           │
                                           ▼
                                     (Transaction)
                                           │
                                    :APPLIED_COUPON
                                           │
                                           ▼
  (Customer) ──────── :USED_COUPON ─────> (Coupon)
```

> [!WARNING]
> **Ground Truth Isolation**: To prevent temporal leakage and target leakage, ground truth labels (`is_abuse`, `ring_id`, `abuse_type`) are **NOT** stored inside Neo4j on the nodes or relationships. They are maintained separately in `ground_truth.csv` for downstream model training and evaluation.

---

### Step 1: Start Neo4j
Spin up the Neo4j Community Edition container:
```bash
docker-compose up -d
```
The database console is available at [http://localhost:7474](http://localhost:7474) (Username: `neo4j`, Password: `testpassword123`).

### Step 2: Environment Variables
Configure environment variables if you use custom credentials (defaults are set for local Docker setup):
```text
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=testpassword123
```

### Step 3: Ingest Data
Run the batch ingestion script to create indexes, load nodes, and establish relationships in batches of 5,000 using parameterized Cypher `UNWIND` queries:
```bash
python -m app.graph.ingest --data-dir backend/data/generated/
```

### Step 4: Validate Graph
Verify node/relationship counts, referential integrity, lack of duplicates, and chronological ordering:
```bash
python -m app.graph.validate
```

### Step 5: Inspect Graph Neighborhoods
Query neighborhoods and print examples of suspicious multi-customer components:
```bash
python -m app.graph.queries
```

---

## Expected Scale and Count Parity

| Category | Node/Label | Expected Approximate Count | Relationship / Meaning |
| :--- | :--- | :--- | :--- |
| **Nodes** | `Customer` | 50,000 | Individual merchant user accounts |
| | `Transaction` | ~300,000 | Purchase transactions |
| | `Device` | ~35,000 | Device IDs used to access accounts |
| | `IP` | ~40,000 | IP addresses |
| | `Coupon` | 50 | Campaign discount coupons |
| **Edges** | `MADE` | ~300,000 | `(Customer)-[:MADE]->(Transaction)` |
| | `USES_DEVICE` | 50,000 | `(Customer)-[:USES_DEVICE]->(Device)` |
| | `USES_IP` | 50,000 | `(Customer)-[:USES_IP]->(IP)` |
| | `REFERRED` | 30,000–50,000 | `(Customer)-[:REFERRED]->(Customer)` (timestamped) |
| | `USED_COUPON` | ~58,000 (unique) | `(Customer)-[:USED_COUPON]->(Coupon)` |
| | `APPLIED_COUPON` | ~64,000 | `(Transaction)-[:APPLIED_COUPON]->(Coupon)` |

---

## Example Cypher Queries

### 1. Customer Neighborhood
Retrieve all direct connections of a single customer:
```cypher
MATCH (c:Customer {customer_id: "C_00042"})
OPTIONAL MATCH (c)-[:USES_DEVICE]->(d:Device)
OPTIONAL MATCH (c)-[:USES_IP]->(ip:IP)
OPTIONAL MATCH (c)-[:USED_COUPON]->(co:Coupon)
OPTIONAL MATCH (referrer:Customer)-[:REFERRED]->(c)
OPTIONAL MATCH (c)-[:REFERRED]->(referred:Customer)
RETURN c, d, ip, co, referrer, referred
```

### 2. Multi-Signal Share
Find pairs of customers sharing both a device and a coupon:
```cypher
MATCH (c1:Customer)-[:USES_DEVICE]->(d:Device)<-[:USES_DEVICE]-(c2:Customer)
MATCH (c1)-[:USED_COUPON]->(co:Coupon)<-[:USED_COUPON]-(c2)
WHERE c1.customer_id < c2.customer_id
RETURN c1.customer_id, c2.customer_id, d.device_id, co.coupon_id
```

### 3. Temporal Coordination
Find customers sharing a device whose transactions occurred within 60 seconds of each other:
```cypher
MATCH (c1:Customer)-[:MADE]->(t1:Transaction)
MATCH (c2:Customer)-[:MADE]->(t2:Transaction)
MATCH (c1)-[:USES_DEVICE]->(d:Device)<-[:USES_DEVICE]-(c2)
WHERE c1.customer_id < c2.customer_id
  AND abs(duration.inSeconds(datetime(replace(t1.timestamp, ' ', 'T')), datetime(replace(t2.timestamp, ' ', 'T'))).seconds) <= 60
RETURN c1.customer_id, c2.customer_id, t1.timestamp, t2.timestamp
```

---

## Phase 3: Graph ML Pipeline

Builds a complete binary node-classification pipeline predicting whether a customer is associated with coordinated promotional/referral abuse.

### Running ML Pipeline

#### 1. Train GBDT Baseline and PyG GraphSAGE
Runs temporal leakage tests, extracts features, trains both models, performs validation threshold optimization search, and saves model parameters:
```bash
python -m app.ml.train --epochs 50 --hidden-dim 64 --lr 0.005
```

#### 2. Evaluate Models
Computes performance metrics (Precision, Recall, F1, PR-AUC, ROC-AUC), counts false positives/negatives, applies configured business costs, and outputs a comparative report:
```bash
python -m app.ml.evaluate
```

### Save Artifacts
All models and metrics are saved to `backend/artifacts/`:
- `baseline_model.joblib`: GBDT baseline parameters
- `gnn_model.pt`: GraphSAGE state dictionary
- `training_config.json`: Hyperparameters and optimal operating thresholds
- `predictions.csv`: Model probabilities on validation and test sets
- `metrics.json`: Standardized metric outputs

