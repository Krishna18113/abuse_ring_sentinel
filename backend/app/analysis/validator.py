import csv
import io
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Optional, Set

from app.analysis.schemas import (
    DatasetValidationResult,
    DatasetSummary,
    SchemaAnalysis,
)

# In-memory session registry for isolated merchant dataset analysis
_SESSION_REGISTRY: Dict[str, Dict[str, Any]] = {}

FORBIDDEN_GROUND_TRUTH_COLUMNS: Set[str] = {
    "is_abuse",
    "ring_id",
    "abuse_type",
    "split",
    "label",
    "ground_truth",
}

EXPECTED_FIELDS: Set[str] = {
    "customer_id",
    "transaction_id",
    "amount",
    "timestamp",
}

OPTIONAL_FIELDS: Set[str] = {
    "device_id",
    "ip_address",
    "coupon_code",
    "referrer_id",
}

def get_session_data(session_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves validated merchant dataset for an isolated session."""
    return _SESSION_REGISTRY.get(session_id)

def parse_file_content(content_bytes: bytes, filename: str) -> Tuple[List[Dict[str, Any]], str, List[str]]:
    """
    Parses uploaded file content (CSV, JSON, or JSONL) into a list of normalized row dictionaries.
    """
    errors: List[str] = []
    text = content_bytes.decode("utf-8", errors="replace").strip()
    
    file_format = "unknown"
    lower_fn = filename.lower()
    
    if lower_fn.endswith(".csv"):
        file_format = "csv"
    elif lower_fn.endswith(".jsonl") or lower_fn.endswith(".ndjson"):
        file_format = "jsonl"
    elif lower_fn.endswith(".json"):
        file_format = "json"
    elif text.startswith("[") or (text.startswith("{") and "transactions" in text):
        file_format = "json"
    elif "\n" in text and "," in text.splitlines()[0]:
        file_format = "csv"
    else:
        file_format = "jsonl"

    records: List[Dict[str, Any]] = []

    try:
        if file_format == "csv":
            reader = csv.DictReader(io.StringIO(text))
            for row_idx, row in enumerate(reader):
                cleaned_row = {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items() if k}
                records.append(cleaned_row)
                if row_idx >= 5000:
                    break
        elif file_format == "json":
            data = json.loads(text)
            if isinstance(data, list):
                records = [r for r in data if isinstance(r, dict)]
            elif isinstance(data, dict):
                for key in ["transactions", "records", "data", "events"]:
                    if key in data and isinstance(data[key], list):
                        records = [r for r in data[key] if isinstance(r, dict)]
                        break
                if not records:
                    records = [data]
        else: # jsonl
            for line_idx, line in enumerate(text.splitlines()):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if isinstance(obj, dict):
                        records.append(obj)
                except Exception as e:
                    errors.append(f"JSONL parse error on line {line_idx + 1}: {str(e)}")
                if line_idx >= 5000:
                    break
    except Exception as e:
        errors.append(f"Failed to parse file format ({file_format}): {str(e)}")

    return records, file_format, errors

def validate_merchant_dataset(
    records: List[Dict[str, Any]],
    filename: str,
    file_format: str,
    initial_errors: Optional[List[str]] = None
) -> DatasetValidationResult:
    """
    Strictly validates records against Sentinel's merchant schema, checks for ground-truth leakage,
    extracts graph entity summary, and stores in an isolated session.
    """
    errors: List[str] = list(initial_errors or [])
    warnings: List[str] = []

    if not records:
        errors.append("Dataset contains 0 valid transaction records.")
        return DatasetValidationResult(
            session_id=str(uuid.uuid4()),
            filename=filename,
            file_format=file_format,
            valid=False,
            summary=DatasetSummary(),
            schema_analysis=SchemaAnalysis(),
            errors=errors,
            warnings=warnings,
            preview_rows=[],
            ready_for_graph_analysis=False,
            architectural_boundary_notes="Dataset empty or unparseable. Validation halted.",
        )

    # 1. Anti-Leakage & Ground-Truth Security Guard
    all_keys: Set[str] = set()
    for r in records[:50]:
        all_keys.update(r.keys())

    detected_forbidden = all_keys.intersection(FORBIDDEN_GROUND_TRUTH_COLUMNS)
    if detected_forbidden:
        err_msg = (
            f"Security Policy Violation: Dataset contains forbidden ground-truth fields: {sorted(list(detected_forbidden))}. "
            "Merchant datasets must only provide operational checkout events, not target labels."
        )
        errors.append(err_msg)
        return DatasetValidationResult(
            session_id=str(uuid.uuid4()),
            filename=filename,
            file_format=file_format,
            valid=False,
            summary=DatasetSummary(),
            schema_analysis=SchemaAnalysis(detected_fields=list(all_keys)),
            errors=errors,
            warnings=warnings,
            preview_rows=[],
            ready_for_graph_analysis=False,
            architectural_boundary_notes="Upload rejected. Ground-truth target labels cannot be injected into graph workspaces.",
        )

    # 2. Schema Compatibility Analysis
    missing_required = EXPECTED_FIELDS - all_keys
    if missing_required:
        errors.append(f"Missing mandatory schema fields: {sorted(list(missing_required))}. Required: customer_id, transaction_id, amount, timestamp.")

    missing_optional = OPTIONAL_FIELDS - all_keys
    unrecognized = all_keys - (EXPECTED_FIELDS | OPTIONAL_FIELDS)

    if "device_id" not in all_keys:
        warnings.append("Missing 'device_id' field: Device sharing graph analysis will be disabled for this dataset.")
    if "ip_address" not in all_keys:
        warnings.append("Missing 'ip_address' field: Network IP clustering graph analysis will be disabled for this dataset.")

    # 3. Entity Statistics & Data Quality Checks
    customers: Set[str] = set()
    transactions: Set[str] = set()
    devices: Set[str] = set()
    ips: Set[str] = set()
    coupons: Set[str] = set()
    referrals_count = 0
    total_amount = 0.0

    invalid_amount_rows = 0
    invalid_timestamp_rows = 0

    cleaned_records: List[Dict[str, Any]] = []

    for idx, r in enumerate(records):
        cid = str(r.get("customer_id") or "").strip()
        txid = str(r.get("transaction_id") or "").strip()
        
        if cid:
            customers.add(cid)
        if txid:
            transactions.add(txid)

        # Parse Amount
        raw_amt = r.get("amount")
        try:
            amt = float(raw_amt)
            if amt <= 0:
                invalid_amount_rows += 1
            else:
                total_amount += amt
        except (ValueError, TypeError):
            invalid_amount_rows += 1

        # Parse Timestamp
        raw_ts = r.get("timestamp")
        if raw_ts:
            # Check basic datetime format
            ts_str = str(raw_ts).strip()
            if len(ts_str) < 10:
                invalid_timestamp_rows += 1

        # Optional Entities
        dev = str(r.get("device_id") or "").strip()
        if dev and dev.lower() not in {"null", "none", "nan", ""}:
            devices.add(dev)

        ip = str(r.get("ip_address") or "").strip()
        if ip and ip.lower() not in {"null", "none", "nan", ""}:
            ips.add(ip)

        cp = str(r.get("coupon_code") or "").strip()
        if cp and cp.lower() not in {"null", "none", "nan", ""}:
            coupons.add(cp)

        ref = str(r.get("referrer_id") or "").strip()
        if ref and ref.lower() not in {"null", "none", "nan", ""}:
            referrals_count += 1

        cleaned_records.append(r)

    if invalid_amount_rows > 0:
        errors.append(f"Found {invalid_amount_rows} rows with invalid or non-positive transaction amounts.")

    if invalid_timestamp_rows > 0:
        warnings.append(f"Found {invalid_timestamp_rows} rows with non-standard timestamp formats.")

    # Check entity sharing density
    if len(customers) > 0 and len(devices) > 0:
        device_sharing_ratio = len(customers) / len(devices)
        if device_sharing_ratio >= 1.8:
            warnings.append(f"High Device Reuse Density: {len(customers)} customers across {len(devices)} unique devices (ratio {device_sharing_ratio:.1f}x). Strong indicator of coordinated device ring topology.")

    if len(customers) > 0 and len(ips) > 0:
        ip_sharing_ratio = len(customers) / len(ips)
        if ip_sharing_ratio >= 2.5:
            warnings.append(f"Elevated Network Gateway Sharing: {len(customers)} customers across {len(ips)} IP addresses (ratio {ip_sharing_ratio:.1f}x).")

    is_valid = len(errors) == 0

    session_id = str(uuid.uuid4())
    if is_valid:
        _SESSION_REGISTRY[session_id] = {
            "session_id": session_id,
            "filename": filename,
            "file_format": file_format,
            "record_count": len(cleaned_records),
            "records": cleaned_records,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        }

    summary = DatasetSummary(
        customer_count=len(customers),
        transaction_count=len(transactions) or len(records),
        unique_devices_count=len(devices),
        unique_ips_count=len(ips),
        unique_coupons_count=len(coupons),
        referrals_count=referrals_count,
        total_volume_inr=round(total_amount, 2),
    )

    schema_analysis = SchemaAnalysis(
        detected_fields=sorted(list(all_keys)),
        missing_optional_fields=sorted(list(missing_optional)),
        unrecognized_fields=sorted(list(unrecognized)),
    )

    boundary_notes = (
        "Dataset schema validated and isolated in session workspace. "
        "The uploaded merchant records are stored in a standalone session namespace and do NOT alter the production seeded demonstration profiles (C_00003, C_46046)."
    )

    return DatasetValidationResult(
        session_id=session_id,
        filename=filename,
        file_format=file_format,
        valid=is_valid,
        summary=summary,
        schema_analysis=schema_analysis,
        errors=errors,
        warnings=warnings,
        preview_rows=cleaned_records[:5],
        ready_for_graph_analysis=is_valid,
        architectural_boundary_notes=boundary_notes,
    )
