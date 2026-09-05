import os
import json
import joblib
import pandas as pd

from app.ml.utils import ARTIFACTS_DIR, DATA_DIR

class RiskScorer:
    """Production service layer to retrieve GraphSAGE risk probabilities for customers."""
    
    def __init__(self, data_dir=DATA_DIR, artifacts_dir=ARTIFACTS_DIR):
        self.data_dir = data_dir
        self.artifacts_dir = artifacts_dir
        
        # 1. Load configuration and model state
        config_path = os.path.join(self.artifacts_dir, "training_config.json")
        scaler_path = os.path.join(self.artifacts_dir, "scaler.joblib")
        model_path = os.path.join(self.artifacts_dir, "gnn_model.pt")
        
        if not os.path.exists(config_path) or not os.path.exists(model_path) or not os.path.exists(scaler_path):
            raise FileNotFoundError("Missing GNN model artifacts. Please run Phase 3 training first.")
            
        with open(config_path, "r") as f:
            self.config = json.load(f)
            
        self.decision_threshold = self.config.get("baseline_threshold", 0.60) # Decoupled operational threshold (frozen at 0.60)
        self.hidden_dim = self.config.get("hidden_dim", 64)
        self.dropout = self.config.get("dropout", 0.3)
        
        # Load scaler
        self.scaler = joblib.load(scaler_path)
        
        # Check if pre-cached probabilities exist
        cached_probs_path = os.path.join(self.artifacts_dir, "customer_probabilities.joblib")
        if os.path.exists(cached_probs_path):
            self.predictions = joblib.load(cached_probs_path)
        else:
            import torch
            from app.ml.gnn import HeteroGraphSAGE
            from app.ml.dataset import build_heterodata_snapshot

            # 2. Build the G_test snapshot graph
            # For evaluation/production, we evaluate customers up to the latest date
            test_cutoff = "2025-12-31 23:59:59"
            test_data, _, _ = build_heterodata_snapshot(
                self.data_dir, test_cutoff, "test", scaler=self.scaler
            )
            
            # 3. Instantiate GNN and load weights
            metadata = test_data.metadata()
            self.model = HeteroGraphSAGE(
                metadata=metadata,
                hidden_channels=self.hidden_dim,
                out_channels=2,
                dropout=self.dropout
            )
            self.model.load_state_dict(torch.load(model_path))
            self.model.eval()
            
            # 4. Precompute GNN predictions to guarantee sub-millisecond scoring lookups
            with torch.no_grad():
                logits, _ = self.model(test_data.x_dict, test_data.edge_index_dict)
                probs = torch.softmax(logits, dim=-1)[:, 1].numpy()
                
            self.predictions = {}
            for c_id, prob in zip(test_data["customer"].customer_ids, probs):
                self.predictions[c_id] = float(prob)
            joblib.dump(self.predictions, cached_probs_path)
            
        # 5. Presentation-only risk level boundaries (configurable)
        # Separate from the 0.60 GBDT/GNN decision boundary
        self.risk_level_boundaries = {
            "LOW": 0.30,      # < 0.30 is LOW
            "MEDIUM": 0.70,   # 0.30 <= prob < 0.70 is MEDIUM
            "HIGH": 1.0       # >= 0.70 is HIGH
        }
        
    def get_risk_score(self, customer_id: str) -> dict:
        """Exposes raw probability, operational review indicator, and presentation level."""
        if customer_id not in self.predictions:
            # Cold-start or unknown customer
            return {
                "risk_probability": 0.0,
                "risk_level": "LOW",
                "review_required": False
            }
            
        prob = self.predictions[customer_id]
        
        # 1. Decision threshold check
        review_required = prob >= 0.60
        
        # 2. Presentation risk level mapping
        if prob < self.risk_level_boundaries["LOW"]:
            level = "LOW"
        elif prob < self.risk_level_boundaries["MEDIUM"]:
            level = "MEDIUM"
        else:
            level = "HIGH"
            
        return {
            "risk_probability": round(prob, 4),
            "risk_level": level,
            "review_required": review_required
        }
