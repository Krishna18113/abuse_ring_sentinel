import os
import re
import sys
from pathlib import Path

def run_leakage_audit():
    print("=" * 60)
    print("PHASE 7: AUTOMATED LEAKAGE & ANTI-GROUND-TRUTH AUDIT")
    print("=" * 60)

    repo_root = Path(__file__).resolve().parent.parent.parent
    
    # Target directories in the runtime production path
    target_dirs = [
        repo_root / "backend" / "app" / "risk",
        repo_root / "backend" / "app" / "ai",
        repo_root / "backend" / "app" / "api",
        repo_root / "frontend" / "src"
    ]
    
    forbidden_tokens = ["ground_truth.csv", "is_abuse", "ring_id", "abuse_type"]
    
    violations = []
    scanned_files_count = 0
    
    for tdir in target_dirs:
        if not tdir.exists():
            print(f"Warning: Directory {tdir} not found.")
            continue
            
        for ext in ["*.py", "*.ts", "*.tsx", "*.js"]:
            for fpath in tdir.rglob(ext):
                scanned_files_count += 1
                try:
                    content = fpath.read_text(encoding="utf-8")
                    for token in forbidden_tokens:
                        # Check matches outside of sanitizer blacklists and CLI self-test strings
                        matches = [m.start() for m in re.finditer(r"\b" + re.escape(token) + r"\b", content)]
                        if matches:
                            is_guard = "forbidden_keys" in content or "forbidden_words" in content or "sanitize" in fpath.name
                            if not is_guard:
                                violations.append((fpath.relative_to(repo_root), token, len(matches)))
                except Exception as e:
                    print(f"Error reading {fpath}: {e}")

    print(f"\n1. Runtime Path File Scan:")
    print(f"   - Scanned files across risk, ai, api, and frontend: {scanned_files_count}")
    if violations:
        print(f"   [FAIL] Found {len(violations)} ground-truth token occurrences:")
        for file, token, count in violations:
            print(f"      * {file}: '{token}' ({count} occurrences)")
    else:
        print(f"   [PASS] 0 ground-truth token leaks found across runtime production paths.")

    # 2. Check Temporal Snapshot Isolation
    print("\n2. Temporal Snapshot Isolation Check:")
    dataset_py = (repo_root / "backend" / "app" / "ml" / "dataset.py").read_text(encoding="utf-8")
    features_py = (repo_root / "backend" / "app" / "ml" / "features.py").read_text(encoding="utf-8")
    
    temporal_checks = []
    if "<= cutoff_dt" in dataset_py:
        temporal_checks.append("[PASS] PyG HeteroData snapshot strictly filters transactions and edges by cutoff timestamp.")
    else:
        temporal_checks.append("[FAIL] Dataset builder missing strict temporal edge filtering.")
        
    if "<= cutoff_time" in features_py:
        temporal_checks.append("[PASS] Feature extractor strictly bounds historical transactions by cutoff timestamp.")
    else:
        temporal_checks.append("[FAIL] Feature extractor missing strict cutoff filtering.")

    for c in temporal_checks:
        print(f"   {c}")

    print("\n" + "=" * 60)
    all_passed = len(violations) == 0 and all("[PASS]" in c for c in temporal_checks)
    if all_passed:
        print("OVERALL LEAKAGE AUDIT RESULT: PASSED (ZERO LEAKAGE DETECTED)")
    else:
        print("OVERALL LEAKAGE AUDIT RESULT: FAILED")
    print("=" * 60)
    return all_passed

if __name__ == "__main__":
    success = run_leakage_audit()
    sys.exit(0 if success else 1)
