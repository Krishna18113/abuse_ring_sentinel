import os
import random
import numpy as np
import torch

# Base directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data", "generated")
ARTIFACTS_DIR = os.path.join(BASE_DIR, "artifacts")

os.makedirs(ARTIFACTS_DIR, exist_ok=True)

# Configurable Business Cost Model
# Default merchant values (configurable via env variables)
FP_COST = float(os.getenv("MERCHANT_FP_COST", "1000.0"))   # Friction on legitimate users
FN_COST = float(os.getenv("MERCHANT_FN_COST", "10000.0"))  # Cost of undetected fraud chargeback

def seed_everything(seed=42):
    """Seed all generators to ensure reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

def calculate_costs(fps, fns, fp_cost=FP_COST, fn_cost=FN_COST):
    """Calculate FP cost, FN cost, and total expected error cost."""
    total_fp_cost = fps * fp_cost
    total_fn_cost = fns * fn_cost
    total_cost = total_fp_cost + total_fn_cost
    return {
        "fp_cost": total_fp_cost,
        "fn_cost": total_fn_cost,
        "total_cost": total_cost
    }
