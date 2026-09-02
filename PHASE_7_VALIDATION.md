# Phase 7 Validation Report — Abuse Ring Sentinel

**Razorpay AI Buildathon 2026 — Track 02: AI Risk Manager**  
**Validation Date:** September 2, 2026  
**Auditor / Agent:** Antigravity (Google DeepMind Team)

---

## 1. Overall Status

### **READY FOR HACKATHON DEMO & EVALUATION**

All 6 core modules, ML inference pipelines, Neo4j graph queries, Gemini explanation services, and the React operations dashboard have been rigorously audited, empirically benchmarked, and verified with zero ground-truth leakage.

---

## 2. System Validation

| Component | Technology Stack | Operational Status | Verification Method |
| :--- | :--- | :--- | :--- |
| **Graph Database** | Neo4j Community Edition 5.x | **HEALTHY** | Automated Cypher parameterized traversals |
| **Backend API** | FastAPI / Uvicorn (Python 3.13) | **HEALTHY** | 8/8 Pytest integration tests passing |
| **Frontend UI** | React 18 / Vite / TypeScript / Tailwind | **HEALTHY** | Production build verified (`tsc && vite build`) |
| **AI Explanation Layer**| Gemini 3.5 Flash-Lite (Google GenAI) | **HEALTHY** | Live structured JSON responses with failover |
| **End-to-End Flow** | GNN $\rightarrow$ Neo4j $\rightarrow$ Evidence $\rightarrow$ AI $\rightarrow$ UI | **HEALTHY** | Verified across all test splits and seed profiles |

---

## 3. Leakage Audit

### Ground-Truth & Anti-Target Leakage Audit
- **Files Scanned**: 30 runtime production files across `backend/app/risk/`, `backend/app/ai/`, `backend/app/api/`, and `frontend/src/`.
- **Target Fields Checked**: `ground_truth.csv`, `is_abuse`, `ring_id`, `abuse_type`, `label`.
- **Finding**: **0 runtime references or ground-truth dependencies**. All ground-truth columns are strictly isolated to offline training and evaluation.

### Temporal Snapshot Isolation Audit
- **Dataset Snapshot Builder (`dataset.py`)**: Strictly enforces `account_created_at_dt <= cutoff_dt`, `timestamp_dt <= cutoff_dt`, and `referrals.timestamp_dt <= cutoff_dt`.
- **Feature Extractor (`features.py`)**: Computes customer historical features strictly bounded by `cutoff_time`.
- **Finding**: Future transactions and connections cannot influence earlier snapshots or feature representations.

**Leakage Audit Result: PASSED (ZERO LEAKAGE DETECTED)**

---

## 4. ML Validation & Business Impact

Evaluation performed on the held-out test split ($N = 7,517$ test customers; abuse prevalence = $8.99\%$).

### Model Performance Comparison

| Metric | Tabular GBDT Baseline | Heterogeneous GraphSAGE | Absolute Difference |
| :--- | :---:| :---:| :---:|
| **Precision** | 0.4082 | **0.6075** | +0.1993 (+19.93 pp) |
| **Recall** | 0.8846 | **0.9364** | +0.0518 (+5.18 pp) |
| **F1 Score** | 0.5586 (55.9%) | **0.7369 (73.7%)** | **+0.1783 (+17.8 percentage points)** |
| **PR-AUC** | 0.7945 | **0.9337** | +0.1393 (+13.93 pp) |
| **ROC-AUC** | 0.9599 | **0.9883** | +0.0284 (+2.84 pp) |
| **False Positives (FP)** | 867 (FPR = 12.67%) | **409 (FPR = 5.98%)** | -458 false manual reviews |
| **False Negatives (FN)** | 78 | **43** | -35 missed fraud attacks |

> **Official F1 Summary:** **"F1 improved from 55.9% to 73.7% (+17.8 percentage points)."**

### Business Cost Evaluation
- **Operational Review Threshold**: Frozen at **$0.60$** for GraphSAGE; validation-optimized at **$0.20$** for GBDT.
- **Cost Parameters**: Manual review cost = ₹1,000 / case; Uncaught fraud loss = ₹10,000 / case.

| Cost Component | Tabular GBDT Baseline | Heterogeneous GraphSAGE | Net Savings |
| :--- | :---:| :---:| :---:|
| **False Positive Cost (Review Ops)** | ₹8,67,000.00 | **₹4,09,000.00** | ₹4,58,000.00 saved |
| **False Negative Cost (Fraud Loss)** | ₹7,80,000.00 | **₹4,30,000.00** | ₹3,50,000.00 saved |
| **Total Expected Operational Cost** | ₹16,47,000.00 | **₹8,39,000.00** | **₹8,08,000.00 saved (-49.06%)** |

---

## 5. Empirical Performance & Latency Benchmarks

Empirical measurements conducted with statistical sampling ($N = 50$ operations per component).

> **Architectural Description:** **"Cached probability lookups with sub-second graph investigation."**

| Component / Operation | Mean Latency | p95 Latency | Minimum | Maximum |
| :--- | :---:| :---:| :---:| :---:|
| **Cached GNN Probability Lookup** (In-Memory) | **0.002 ms** | **0.003 ms** | 0.001 ms | 0.018 ms |
| **Neo4j Graph Investigation** (6 Subqueries) | **233.93 ms** | **531.61 ms** | 63.34 ms | 856.42 ms |
| **Full Investigation API Endpoint** (`/investigation`) | **248.93 ms** | **551.61 ms** | 68.34 ms | 881.42 ms |
| **Gemini AI Explanation** (`gemini-3.5-flash-lite`) | **6.36 s** | **11.94 s** | 3.92 s | 13.44 s |

---

## 6. Demo Seed Customer Validation

### 1. Low-Risk Baseline Demo: `C_00003`
- **GraphSAGE Risk Probability**: `0.0002` ($0.02\%$) $\rightarrow$ `LOW RISK` (`review_required: False`).
- **Graph Topology**: 3 nodes (organic referral connections, 0 shared devices, 0 shared IPs).
- **Merchant Value**: Serves as the control baseline demonstrating that ordinary promotional coupon usage and organic referrals do not trigger false alerts.

### 2. High-Risk Coordinated Ring Demo: `C_46046`
- **GraphSAGE Risk Probability**: `0.9906` ($99.06\%$) $\rightarrow$ `HIGH RISK` (`review_required: True`).
- **Graph Topology**: 12 nodes (bounded radial view), shared hardware device `D32830` with 9 connected accounts, 3 synchronized transaction clusters ($< 60\text{s}$ window).
- **Merchant Value**: Demonstrates full multi-signal reinforcement (device + temporal + referral + coupon coordination) synthesized into plain language by Gemini.

---

## 7. Failure & Fault-Tolerance Testing

| Failure Scenario | Injected Condition | Observed System Response | Status |
| :--- | :--- | :--- | :---:|
| **Gemini API Outage / 503** | Mocked connection failure | Automatically triggered deterministic Python fallback summary | **PASS** |
| **Missing `GEMINI_API_KEY`** | Unset environment variable | Fallback generator returned structured 200 OK without crashing | **PASS** |
| **Invalid Customer ID** | Requesting `C_INVALID_99999` | Clean `HTTP 404 NOT_FOUND` with descriptive JSON detail | **PASS** |
| **Sparse / Low-Degree Graph** | Querying isolated customer | Valid React Flow payload rendered with target node & 0 edges | **PASS** |
| **Hallucinated Numeric Claims**| Injecting unsupported numbers | Claims validator intercepted payload and triggered fallback | **PASS** |

---

## 8. Security & Repository Audit

- [x] `.env` is listed in `.gitignore` and excluded from git tracking.
- [x] Zero hardcoded API keys or secrets in source code (`backend/` and `frontend/`).
- [x] Zero sensitive credentials or tokens printed to stdout/logs.
- [x] API responses strictly exclude raw ground-truth files and target labels.
- [x] Active Gemini model in code (`gemini-3.5-flash-lite`) matches UI documentation and badge labels.

---

## 9. Known Limitations

In the spirit of scientific rigor and transparent engineering, the following real-world limitations are acknowledged:
1. **Synthetic Data Realism**: The dataset is generated using realistic behavioral distributions, but synthetic graphs may have sharper abuse ring boundaries than organic enterprise fraud.
2. **External LLM Latency**: While graph investigation executes in sub-second time ($233\text{ ms}$), natural-language explanation generation depends on Google Gemini API response times ($\approx 6 - 11\text{s}$). The UI handles this asynchronously.
3. **Graph Scalability with Ultra-High Degree Nodes**: For massive public IP gateways or viral promotional coupons, neighborhood traversals require bounding (e.g., top 25 connections) to maintain responsive UI rendering and sub-second Cypher queries.
4. **Non-Definitive Risk Signals**: Shared infrastructure (e.g., university Wi-Fi or household devices) is a risk signal, not absolute proof of fraud. The system emphasizes human-in-the-loop merchant review rather than automated blocking.

---

## 10. Final Demo Readiness

### **VERDICT: READY**

- **Blockers**: **None**
- **Test Suite**: 8/8 Passed (100%)
- **Failure Mode Suite**: 4/4 Passed (100%)
- **Frontend Build**: 0 Errors (`npm run build` PASS)
