# Merchant Dataset Analysis Architecture & Integration Guide

This document defines the architectural boundary, validation lifecycle, and isolation model for the **Merchant Dataset Analysis Workspace** in **Abuse Ring Sentinel**.

---

## 1. Architectural Concept

Instead of simulating artificial real-time model retraining on single isolated transactions, **Abuse Ring Sentinel** provides a dedicated **Merchant Dataset Analysis Workspace**. 

This allows external merchants (e-commerce platforms, payment aggregators, fintech merchants) to provide batches of customer profiles and checkout transaction records for:
1. **Schema validation & compatibility checking** against Sentinel's graph representation.
2. **Entity extraction**: Identifying unique customer accounts, hardware devices, network IP gateways, promotional coupons, and referral links.
3. **Graph topology analysis**: Detecting multi-account device sharing, IP clustering density, and synchronized burst cadences.
4. **Inductive risk evaluation**: Running graph-grounded investigation pipelines in an isolated session workspace.

```text
External Merchant Batch (CSV / JSON / JSONL)
                    │
                    ▼  POST /api/analysis/upload
     [Strict Validation & Anti-Leakage Guard]
    (Rejects forbidden target labels: is_abuse, ring_id)
                    │
                    ▼
       [Session Workspace Isolation]
    (Stores parsed records in standalone session namespace)
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
[Entity Extraction]    [Schema Compatibility Analysis]
- Customer accounts    - Mandatory: customer_id, tx_id, amount, ts
- Device fingerprints  - Optional: device_id, ip_address, coupon
- IP gateways          - Data quality checks & topology warnings
- Promo coupons
        └───────────┬───────────┘
                    │
                    ▼
   [Dataset Validation Dossier Response]
   - Summary statistics & volume
   - Device reuse ratio warnings
   - Record preview table
   - Graph readiness certification
```

---

## 2. Strict Session Isolation & Safety

> [!IMPORTANT]
> **Complete Workspace Isolation**: Uploaded merchant datasets are processed exclusively within standalone session namespaces. They **never** overwrite, mutate, or contaminate the core reference Neo4j graph dataset or the seeded demonstration profiles (`C_00003`, `C_46046`).

* **Reference Dataset (`C_00003`, `C_46046`)**: Remains 100% deterministic, frozen, and available on the primary operations dashboard.
* **Uploaded Merchant Datasets**: Live in temporary, isolated session contexts (`session_id = UUID4`).

---

## 3. Honest Machine Learning & Inference Boundaries

To maintain rigorous scientific and engineering honesty:

1. **No Fake Real-Time Retraining**: The GNN model is **not** retrained online when a dataset is uploaded.
2. **Schema Compatibility Precondition**: The pre-trained heterogeneous GraphSAGE model was trained on Sentinel's defined feature and schema space. Arbitrary merchant datasets cannot be scored without first undergoing schema validation and inductive feature normalization.
3. **The 4-Stage Lifecycle**:
   * **Stage 1: Schema Normalization**: Mapping merchant field names to Sentinel's standard entity schema (`Customer`, `Device`, `IP`, `Coupon`, `Referral`).
   * **Stage 2: Graph Projection**: Projecting bipartite and multi-partite relationships into an isolated Neo4j session graph or in-memory PyG `HeteroData` structure.
   * **Stage 3: Inductive Feature Extraction**: Computing historical behavior metrics (burst rates, night transaction ratios, device sharing counts) using the strict temporal feature pipeline.
   * **Stage 4: Inductive Inference**: Passing the extracted subgraph into the frozen GraphSAGE model to generate calibrated coordination probabilities.

---

## 4. Security & Anti-Leakage Policy

The upload validation layer strictly enforces Sentinel's anti-leakage policy:

* **Forbidden Attributes**: Any dataset containing ground-truth or target labels (`is_abuse`, `ring_id`, `abuse_type`, `split`, `label`, `ground_truth`) is **immediately rejected** with a security error.
* **Operational Integrity**: Merchants must only provide observable operational events (who purchased, what device was used, which IP connected, what coupon was applied). Target labels belong solely to offline benchmark evaluations.

---

## 5. API Endpoints

### `POST /api/analysis/upload`
Accepts a file (`multipart/form-data`) in CSV, JSON, or JSONL format. Returns a `DatasetValidationResult` with entity summary, warnings, and preview rows.

### `POST /api/analysis/validate-payload`
Accepts a JSON payload containing raw transaction records for direct API testing.

### `GET /api/analysis/sample-datasets`
Returns curated test datasets for instant 1-click demonstration during hackathon evaluations:
* **Batch A**: Multi-account promotional ring (10 customers, 2 shared devices, 1 IP).
* **Batch B**: Organic clean e-commerce retail batch (5 customers, dedicated hardware).
* **Security Test**: Hostile upload containing forbidden target labels to demonstrate automated rejection.
