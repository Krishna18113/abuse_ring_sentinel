from typing import List
from app.analysis.schemas import SampleDatasetItem

SAMPLE_PROMO_RING_CSV = """customer_id,transaction_id,amount,timestamp,device_id,ip_address,coupon_code,referrer_id
M_1001,TX_M_001,1500.00,2026-03-01 10:00:00,D_RING_99,192.168.10.50,DISCOUNT_50,
M_1002,TX_M_002,1490.00,2026-03-01 10:01:15,D_RING_99,192.168.10.50,DISCOUNT_50,M_1001
M_1003,TX_M_003,1510.00,2026-03-01 10:02:40,D_RING_99,192.168.10.50,DISCOUNT_50,M_1001
M_1004,TX_M_004,1505.00,2026-03-01 10:03:10,D_RING_99,192.168.10.50,DISCOUNT_50,M_1002
M_1005,TX_M_005,1495.00,2026-03-01 10:04:05,D_RING_99,192.168.10.50,DISCOUNT_50,M_1002
M_1006,TX_M_006,1800.00,2026-03-01 10:05:22,D_RING_88,192.168.10.50,DISCOUNT_50,M_1003
M_1007,TX_M_007,1790.00,2026-03-01 10:06:18,D_RING_88,192.168.10.50,DISCOUNT_50,M_1003
M_1008,TX_M_008,1810.00,2026-03-01 10:07:05,D_RING_88,192.168.10.50,DISCOUNT_50,M_1004
M_1009,TX_M_009,1499.00,2026-03-01 10:08:12,D_RING_88,192.168.10.50,DISCOUNT_50,M_1004
M_1010,TX_M_010,1502.00,2026-03-01 10:09:00,D_RING_88,192.168.10.50,DISCOUNT_50,M_1005"""

SAMPLE_ORGANIC_JSON = """[
  {"customer_id": "M_2001", "transaction_id": "TX_ORG_101", "amount": 450.00, "timestamp": "2026-03-01 09:15:00", "device_id": "DEV_ORG_11", "ip_address": "49.204.12.1", "coupon_code": null, "referrer_id": null},
  {"customer_id": "M_2002", "transaction_id": "TX_ORG_102", "amount": 1250.00, "timestamp": "2026-03-01 11:20:00", "device_id": "DEV_ORG_22", "ip_address": "103.21.55.9", "coupon_code": "SPRING10", "referrer_id": null},
  {"customer_id": "M_2003", "transaction_id": "TX_ORG_103", "amount": 890.00, "timestamp": "2026-03-01 13:45:00", "device_id": "DEV_ORG_33", "ip_address": "157.34.88.14", "coupon_code": null, "referrer_id": null},
  {"customer_id": "M_2004", "transaction_id": "TX_ORG_104", "amount": 2300.00, "timestamp": "2026-03-01 15:10:00", "device_id": "DEV_ORG_44", "ip_address": "182.72.19.82", "coupon_code": "WELCOME", "referrer_id": null},
  {"customer_id": "M_2005", "transaction_id": "TX_ORG_105", "amount": 320.00, "timestamp": "2026-03-01 17:30:00", "device_id": "DEV_ORG_55", "ip_address": "122.161.4.33", "coupon_code": null, "referrer_id": null}
]"""

SAMPLE_HOSTILE_LEAKAGE_CSV = """customer_id,transaction_id,amount,timestamp,device_id,ip_address,is_abuse,ring_id
M_HOSTILE_01,TX_H_001,500.00,2026-03-01 12:00:00,DEV_H1,1.1.1.1,1,RING_ALPHA
M_HOSTILE_02,TX_H_002,600.00,2026-03-01 12:05:00,DEV_H1,1.1.1.1,1,RING_ALPHA"""

def get_sample_datasets() -> List[SampleDatasetItem]:
    return [
        SampleDatasetItem(
            dataset_id="promo_ring_batch",
            name="Batch A: Multi-Account Promo Abuse Ring",
            description="10 customer accounts sharing 2 device fingerprints, a single IP gateway, and a single coupon code.",
            file_format="csv",
            record_count=10,
            content=SAMPLE_PROMO_RING_CSV,
        ),
        SampleDatasetItem(
            dataset_id="organic_retail_batch",
            name="Batch B: Clean Organic E-Commerce Retail",
            description="5 verified consumer accounts with dedicated device hardware, unique public IPs, and spaced timestamps.",
            file_format="json",
            record_count=5,
            content=SAMPLE_ORGANIC_JSON,
        ),
        SampleDatasetItem(
            dataset_id="hostile_leakage_test",
            name="Security Test: Forbidden Ground-Truth Column Injection",
            description="Test file attempting to inject target labels (is_abuse, ring_id) to verify rejection by security policy.",
            file_format="csv",
            record_count=2,
            content=SAMPLE_HOSTILE_LEAKAGE_CSV,
        ),
    ]
