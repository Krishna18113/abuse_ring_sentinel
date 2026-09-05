# 🚀 Cloud Migration Plan: Docker Neo4j → Neo4j AuraDB & Full-Stack Cloud Deployment

> **Project**: Abuse Ring Sentinel  
> **Target Cloud Topology**:  
> * **Database**: Neo4j AuraDB (Cloud Instance `7425fc66`)  
> * **Backend API**: Render Web Service (`FastAPI` + `Uvicorn`)  
> * **Frontend**: Vercel (`React 18` + `Vite` SPA)  
> * **Safety Guarantee**: Non-destructive. The local Docker Neo4j database remains completely untouched.

---

## 1. Technical Audit & Repository Inspection Findings

Before planning the migration, a comprehensive audit of the repository was conducted:

| Audit Question | Repository Finding |
| :--- | :--- |
| **1. Docker Neo4j Configuration** | Configured in `docker-compose.yml` using `neo4j:community`, listening on ports `7474` (HTTP) and `7687` (Bolt). Volumes: `neo4j_data`, `neo4j_import`, `neo4j_logs`. Default auth: `neo4j/testpassword123`. |
| **2. Database Initialization** | Initialized via `backend/app/graph/schema.py` (5 uniqueness constraints) and populated via `backend/app/graph/ingest.py` using parameterized Cypher `UNWIND` batches (size: 5,000). |
| **3. Data Generation Scripts** | `backend/app/data/generate.py` and `backend/app/data/behavior.py` generate all 50,000 customers, 303,161 transactions, 35k devices, 40k IPs, 50 coupons, and referral chains. |
| **4. Deterministic Reproducibility** | **100% Deterministic**. `generate.py` accepts `--seed 42` (default) with fixed `random.seed(42)` and `np.random.seed(42)`. Pre-generated CSVs are also present in `backend/data/generated/`. |
| **5. Existing Dump/Export Scripts** | No custom dump scripts. Migration is cleanest via Python driver batch ingestion (`ingest.py`) or Aura Web Console dump upload. |
| **6. Neo4j Version** | Docker uses Neo4j 5.x Community. Python driver is `neo4j==6.3.0`. Neo4j Aura runs Neo4j 5.x Enterprise. **100% Cypher dialect and schema compatibility.** |
| **7. Connection Environment Variables** | Controlled by `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD` in `backend/app/graph/connection.py`. |
| **8. Backend Neo4j Dependencies** | Used for runtime graph traversals (`app/risk/queries.py`, `app/risk/investigator.py`, `app/api/routes.py`). Note: Dashboard summary, risk queue probabilities, and the **Merchant Analysis Workspace** run in-memory and do not depend on Neo4j. |
| **9. Local-Only Docker Dependencies** | **None**. Zero usage of APOC, GDS, or local `LOAD CSV` paths. All Cypher queries use standard OpenCypher (`MATCH`, `MERGE`, `WHERE`, `duration.inSeconds`, `datetime`). |
| **10. Safest Migration Method** | Parameterized direct batch ingestion via Python driver into Neo4j Aura using existing `ingest.py` and verification with `validate.py`. |

---

## A. Current Neo4j Architecture

```
                                  LOCAL DOCKER ENVIRONMENT
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ Docker Container: abuse_ring_sentinel_neo4j (neo4j:community)                          │
│ Bolt: bolt://localhost:7687 • HTTP: http://localhost:7474                              │
│ Authentication: neo4j / testpassword123                                                │
└──────────────────────────────────────────┬─────────────────────────────────────────────┘
                                           │
                        ┌──────────────────┴──────────────────┐
                        ▼                                     ▼
        ┌───────────────────────────────┐     ┌────────────────────────────────┐
        │ Schema Constraints (schema.py)│     │ Batch Ingestion (ingest.py)    │
        │ 5 Unique Constraints          │     │ UNWIND batches (5,000 rows)    │
        └───────────────────────────────┘     └────────────────────────────────┘
```

### Existing Graph Entities and Counts in Reference Dataset:
* **`:Customer` Nodes**: 50,000
* **`:Transaction` Nodes**: 303,161
* **`:Device` Nodes**: ~35,000
* **`:IP` Nodes**: ~40,000
* **`:Coupon` Nodes**: 50
* **Relationships**:
  * `(Customer)-[:USES_DEVICE]->(Device)`: 50,000
  * `(Customer)-[:USES_IP]->(IP)`: 50,000
  * `(Customer)-[:MADE]->(Transaction)`: 303,161
  * `(Transaction)-[:APPLIED_COUPON]->(Coupon)`: ~30,000
  * `(Customer)-[:USED_COUPON]->(Coupon)`: ~25,000
  * `(Customer)-[:REFERRED]->(Customer)`: ~10,000

---

## B. Docker → Aura Migration Method

We recommend **Method 1 (Direct Parameterized Python Ingestion)** because it requires zero Docker downtime, respects Aura's transaction memory limits via chunking, and automatically validates data integrity.

```
                  MIGRATION PIPELINE (NON-DESTRUCTIVE)
┌────────────────────────────────┐
│ backend/data/generated/        │
│ customers.csv (50k)            │
│ transactions.csv (303k)        │
│ coupons.csv, referrals.csv     │
└───────────────┬────────────────┘
                │
                │ Reads CSVs via pandas
                ▼
┌────────────────────────────────┐
│ app.graph.ingest (Python)      │ ──► Connects via TLS (neo4j+s://)
└───────────────┬────────────────┘     Executes parameterized UNWIND batches
                │
                ▼
┌────────────────────────────────┐
│ Neo4j AuraDB (Instance 7425fc66)│
│ neo4j+s://7425fc66.databases...│
└───────────────┬────────────────┘
                │
                ▼
┌────────────────────────────────┐
│ app.graph.validate (Python)    │ ──► Runs 6-stage validation suite
│ Validates counts & integrity   │     Confirming 100% graph match
└────────────────────────────────┘
```

### Migration Execution Steps:

1. **Keep Local Docker Intact**:
   Do not stop or remove `abuse_ring_sentinel_neo4j`. It remains your local fallback.

2. **Run Schema Constraints Creation on AuraDB**:
   Target the Aura instance by temporarily passing its credentials in the terminal:
   ```powershell
   $env:NEO4J_URI="neo4j+s://7425fc66.databases.neo4j.io"
   $env:NEO4J_USERNAME="neo4j"
   $env:NEO4J_PASSWORD="UU7O5VhmEyd2p1LPJjUnKKqghXBYeujajpy3b2PrKEc"

   cd backend
   python -m app.graph.schema
   ```

3. **Ingest the Reference Dataset into AuraDB**:
   Execute the batch ingestion pipeline (takes ~3–5 minutes over broadband):
   ```powershell
   python -m app.graph.ingest --data-dir data/generated
   ```

4. **Run Verification on AuraDB**:
   ```powershell
   python -m app.graph.validate --data-dir data/generated
   ```

---

## C. Exact Data That Must Exist in Aura

To guarantee that the **frozen GraphSAGE model**, **seeded accounts (`C_00003`, `C_46046`)**, and **evidence engine** produce exact results:

### 1. Seeded Demo Accounts (Must Match Exactly)
* **`C_46046` (High-Risk Abuse Ring)**:
  * Must be connected to `Device` **`D32830`** (which must also be linked to accounts `C_45128`, `C_46076`, `C_46066`, `C_44934`, `C_40721`, `C_37143`, `C_36954`, `C_33125`, `C_29399`).
  * Must be connected to `IP` **`172.26.132.41`**.
  * Must be connected to `Coupon` **`COUPON_43`**.
  * Must have transaction timestamps synchronized within 60s of peer accounts.
* **`C_00003` (Low-Risk Organic Customer)**:
  * Must connect to private device and IP with zero multi-account sharing.
  * Must connect to legitimate organic referral edges.

### 2. Constraints:
* `customer_id_unique` on `(:Customer {customer_id})`
* `transaction_id_unique` on `(:Transaction {transaction_id})`
* `device_id_unique` on `(:Device {device_id})`
* `ip_address_unique` on `(:IP {ip_address})`
* `coupon_id_unique` on `(:Coupon {coupon_id})`

---

## D. Required Environment Variables

### 1. Render (Backend Deployment)
Configure these in **Render Dashboard** → **Web Service** → **Environment**:

| Variable | Value | Notes |
| :--- | :--- | :--- |
| **`PYTHON_VERSION`** | `3.11.9` | Ensures Python 3.11 runtime. |
| **`NEO4J_URI`** | `neo4j+s://7425fc66.databases.neo4j.io` | Connects Render to your AuraDB cloud instance. |
| **`NEO4J_USERNAME`** | `neo4j` | AuraDB default admin user. |
| **`NEO4J_PASSWORD`** | `UU7O5VhmEyd2p1LPJjUnKKqghXBYeujajpy3b2PrKEc` | AuraDB instance password. |
| **`GEMINI_API_KEY`** | `AIzaSy...` | Your Google Gemini API Key. |
| **`GEMINI_MODEL`** | `gemini-2.5-flash` | Fast, cost-efficient explanation model. |

* **Render Build Command**: `pip install -r requirements.txt`  
* **Render Start Command**: `uvicorn app.api.app:app --host 0.0.0.0 --port $PORT`  
* **Root Directory**: `backend`

### 2. Vercel (Frontend Deployment)
Configure in **Vercel Dashboard** → **Project Settings** → **Environment Variables**:

| Variable | Value | Notes |
| :--- | :--- | :--- |
| **`VITE_API_BASE_URL`** | `https://<your-render-app-name>.onrender.com/api` | Directs frontend API calls to Render backend. |

* **Framework Preset**: `Vite`  
* **Root Directory**: `frontend`  
* **Build Command**: `npm run build`  
* **Output Directory**: `dist`

---

## E. Post-Migration Verification Steps

Run this checklist immediately after data ingestion to confirm 100% operational parity:

### Step 1: Automated Integrity Checks
Execute `backend/app/graph/validate.py` against AuraDB:
* [ ] Customer node count = 50,000
* [ ] Transaction node count = 303,161
* [ ] Device count = 35,000
* [ ] IP count = 40,000
* [ ] Coupon count = 50
* [ ] 0 orphaned transactions or dangling referral links
* [ ] 0 duplicate relationships

### Step 2: Seed Customer Verification Query
Run in Neo4j Aura Query Console:
```cypher
MATCH (c:Customer {customer_id: 'C_46046'})-[:USES_DEVICE]->(d:Device)<-[:USES_DEVICE]-(other:Customer)
RETURN d.device_id, count(distinct other) AS shared_accounts;
```
*Expected Result*: `d.device_id = "D32830"`, `shared_accounts = 9`.

### Step 3: API Endpoint Verification (Render)
* [ ] `GET https://<render-url>/health` → `{"status": "healthy"}`
* [ ] `GET https://<render-url>/api/demo/customers` → Returns `C_00003` and `C_46046`
* [ ] `GET https://<render-url>/api/risk/customers/C_46046/investigation` → Returns 9 shared device accounts and temporal burst signals.
* [ ] `GET https://<render-url>/api/risk/customers/C_46046/graph` → Returns bounded 25-node graph payload.

### Step 4: UI Verification (Vercel)
* [ ] Portfolio Dashboard displays 50k customers and risk distribution.
* [ ] Clicking `C_46046` opens the 3-tier Evidence Graph and AI Risk Decision Summary.
* [ ] Merchant Dataset Analysis Workspace accepts `Batch A` and extracts `D_RING_99` in-memory.

---

## F. Risks and Rollback Procedure

| Risk | Mitigation | Rollback Action |
| :--- | :--- | :--- |
| **AuraDB Ingestion Network Timeout** | `ingest.py` uses 5,000-row `UNWIND` batches. `MERGE` statements are idempotent and can be safely re-run. | Simply rerun `python -m app.graph.ingest --data-dir data/generated`. |
| **Wrong Username on AuraDB** | Neo4j Aura instances typically default to user `neo4j`. If `7425fc66` was entered as username, verify whether `neo4j` is required. | Test connection with `auth=('neo4j', password)` or `auth=('7425fc66', password)`. |
| **Aura Free Tier Node Limit (200k)** | Reference dataset has 50k customers, 35k devices, 40k IPs (total entities ~125k), fitting within 200k limit. | If limit approached, transactions can be filtered to recent 3 months without impacting customer-device-IP topological rings. |
| **Render Cold Starts** | Render free tier sleeps after 15 mins. | Mention 30s wake-up in submission notes, or use a health ping cron. |

### Immediate Rollback to Local Docker
Because the local Docker database is **never touched or modified**:
* To revert locally at any time, simply unset `NEO4J_URI` (or set `NEO4J_URI=bolt://localhost:7687`).
* Your local Docker container continues to run with all original data intact.
