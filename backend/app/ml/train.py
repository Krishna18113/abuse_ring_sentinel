import os
import json
import argparse
import joblib
import pandas as pd
import numpy as np
import torch

from app.ml.utils import (
    seed_everything,
    calculate_costs,
    BASE_DIR,
    DATA_DIR,
    ARTIFACTS_DIR,
    FP_COST,
    FN_COST
)
from app.ml.features import run_leakage_test
from app.ml.dataset import get_temporal_datasets
from app.ml.baseline import TabularBaselineModel
from app.ml.gnn import HeteroGraphSAGE

def train_pipeline(args):
    # Set seed
    seed_everything(args.seed)
    
    # 1. Execute Temporal Leakage Test
    run_leakage_test(DATA_DIR, "2025-09-13 12:00:00", "train")
    
    # 2. Load Datasets
    print("Loading datasets and compiling graph snapshots...")
    datasets = get_temporal_datasets(DATA_DIR)
    train_data, train_df = datasets["train"]
    val_data, val_df = datasets["val"]
    test_data, test_df = datasets["test"]
    
    print(f"Dataset compiled. Customers in splits: "
          f"Train={len(train_df[train_df['split']=='train'])}, "
          f"Val={len(val_df[val_df['split']=='val'])}, "
          f"Test={len(test_df[test_df['split']=='test'])}")
    
    # Save the fitted scaler
    scaler_path = os.path.join(ARTIFACTS_DIR, "scaler.joblib")
    # Fetch the scaler that was created/fitted in build_heterodata_snapshot
    from app.ml.dataset import build_heterodata_snapshot
    # The scaler is returned as the third element of build_heterodata_snapshot, 
    # and we already loaded it implicitly inside get_temporal_datasets.
    # To save the scaler fitted during train, we can fetch it. Let's do it by rebuilding or capturing:
    _, _, fitted_scaler = build_heterodata_snapshot(DATA_DIR, "2025-09-13 12:00:00", "train")
    joblib.dump(fitted_scaler, scaler_path)
    
    # -------------------------------------------------------------
    # Train Tabular GBDT Baseline
    # -------------------------------------------------------------
    print("\n----------------------------------------")
    print("Training Tabular GBDT Baseline Model...")
    print("----------------------------------------")
    
    # Baseline uses only training customers
    df_train_only = train_df[train_df["split"] == "train"]
    baseline_model = TabularBaselineModel(random_state=args.seed)
    baseline_model.fit(df_train_only)
    
    baseline_model_path = os.path.join(ARTIFACTS_DIR, "baseline_model.joblib")
    baseline_model.save(baseline_model_path)
    
    # Predict validation probabilities
    df_val_only = val_df[val_df["split"] == "val"].copy()
    val_baseline_probs = baseline_model.predict_proba(df_val_only)
    df_val_only["baseline_prob"] = val_baseline_probs
    
    # -------------------------------------------------------------
    # Train GraphSAGE GNN
    # -------------------------------------------------------------
    print("\n----------------------------------------")
    print("Training PyTorch Geometric GraphSAGE...")
    print("----------------------------------------")
    
    metadata = train_data.metadata()
    model = HeteroGraphSAGE(
        metadata=metadata,
        hidden_channels=args.hidden_dim,
        out_channels=2,
        dropout=args.dropout
    )
    
    # Compute class weights for cross-entropy to handle imbalance
    train_labels = train_data["customer"].y[train_data["customer"].train_mask]
    count_0 = (train_labels == 0).sum().item()
    count_1 = (train_labels == 1).sum().item()
    
    # Standard class weighting
    weight = torch.tensor([1.0, float(count_0) / count_1], dtype=torch.float32)
    print(f"Class imbalance weights: Legit={weight[0]:.2f}, Abuse={weight[1]:.2f}")
    
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr, weight_decay=1e-4)
    criterion = torch.nn.CrossEntropyLoss(weight=weight)
    
    model.train()
    for epoch in range(args.epochs):
        optimizer.zero_grad()
        # Forward pass on train graph snapshot
        logits, _ = model(train_data.x_dict, train_data.edge_index_dict)
        
        # Loss calculated strictly on training nodes mask
        loss = criterion(
            logits[train_data["customer"].train_mask],
            train_data["customer"].y[train_data["customer"].train_mask]
        )
        loss.backward()
        optimizer.step()
        
        if (epoch + 1) % 10 == 0 or epoch == 0:
            # Eval train accuracy
            preds = logits[train_data["customer"].train_mask].argmax(dim=-1)
            acc = (preds == train_labels).float().mean().item()
            print(f"  Epoch {epoch+1:02d}/{args.epochs} | Loss: {loss.item():.4f} | Train Acc: {acc:.2%}")
            
    # Save GNN model weights
    gnn_model_path = os.path.join(ARTIFACTS_DIR, "gnn_model.pt")
    torch.save(model.state_dict(), gnn_model_path)
    print(f"Saved GraphSAGE model state to {gnn_model_path}")
    
    # Predict validation probabilities
    model.eval()
    with torch.no_grad():
        val_logits, _ = model(val_data.x_dict, val_data.edge_index_dict)
        # Apply softmax to get probabilities
        val_probs = torch.softmax(val_logits, dim=-1)[:, 1].numpy()
        
    # Map back to val customers
    val_cust_ids = val_data["customer"].customer_ids
    df_val_gnn_probs = pd.DataFrame({
        "customer_id": val_cust_ids,
        "gnn_prob": val_probs
    })
    
    df_val_only = df_val_only.merge(df_val_gnn_probs, on="customer_id", how="left")
    
    # -------------------------------------------------------------
    # Operating Threshold Search (Validation Set Cost Optimization)
    # -------------------------------------------------------------
    print("\n----------------------------------------")
    print("Selecting Optimal Operating Thresholds...")
    print("----------------------------------------")
    
    thresholds = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    y_val = df_val_only["label"].values
    
    # Baseline threshold optimization
    best_baseline_thresh = 0.5
    min_baseline_cost = float("inf")
    
    # GNN threshold optimization
    best_gnn_thresh = 0.5
    min_gnn_cost = float("inf")
    
    print(f"Val Costs: FP cost = INR {FP_COST:,.2f}, FN cost = INR {FN_COST:,.2f}")
    
    for t in thresholds:
        # Baseline
        base_preds = (df_val_only["baseline_prob"] >= t).astype(int)
        base_fps = ((base_preds == 1) & (y_val == 0)).sum()
        base_fns = ((base_preds == 0) & (y_val == 1)).sum()
        base_cost = calculate_costs(base_fps, base_fns)["total_cost"]
        
        if base_cost < min_baseline_cost:
            min_baseline_cost = base_cost
            best_baseline_thresh = t
            
        # GNN
        gnn_preds = (df_val_only["gnn_prob"] >= t).astype(int)
        gnn_fps = ((gnn_preds == 1) & (y_val == 0)).sum()
        gnn_fns = ((gnn_preds == 0) & (y_val == 1)).sum()
        gnn_cost = calculate_costs(gnn_fps, gnn_fns)["total_cost"]
        
        if gnn_cost < min_gnn_cost:
            min_gnn_cost = gnn_cost
            best_gnn_thresh = t
            
        print(f"  Threshold {t:.2f} | Baseline Cost: INR {base_cost:,.2f} | GNN Cost: INR {gnn_cost:,.2f}")
        
    print(f"\n  Selected Tabular Baseline Threshold: {best_baseline_thresh:.2f} (Min Cost: INR {min_baseline_cost:,.2f})")
    print(f"  Selected GraphSAGE Threshold:        {best_gnn_thresh:.2f} (Min Cost: INR {min_gnn_cost:,.2f})")
    
    # Save training configuration details
    config_path = os.path.join(ARTIFACTS_DIR, "training_config.json")
    config = {
        "random_seed": args.seed,
        "epochs": args.epochs,
        "learning_rate": args.lr,
        "hidden_dim": args.hidden_dim,
        "dropout": args.dropout,
        "baseline_threshold": best_baseline_thresh,
        "gnn_threshold": best_gnn_thresh,
        "fp_cost": FP_COST,
        "fn_cost": FN_COST
    }
    
    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)
    print(f"Saved training configuration to {config_path}")
    
    # -------------------------------------------------------------
    # Predict Test Probabilities
    # -------------------------------------------------------------
    print("\nGenerating Test Predictions...")
    
    # Baseline
    df_test_only = test_df[test_df["split"] == "test"].copy()
    test_baseline_probs = baseline_model.predict_proba(df_test_only)
    df_test_only["baseline_prob"] = test_baseline_probs
    
    # GNN
    with torch.no_grad():
        test_logits, _ = model(test_data.x_dict, test_data.edge_index_dict)
        test_probs = torch.softmax(test_logits, dim=-1)[:, 1].numpy()
        
    df_test_gnn_probs = pd.DataFrame({
        "customer_id": test_data["customer"].customer_ids,
        "gnn_prob": test_probs
    })
    
    df_test_only = df_test_only.merge(df_test_gnn_probs, on="customer_id", how="left")
    
    # -------------------------------------------------------------
    # Save Predictions CSV
    # -------------------------------------------------------------
    # Combine predictions
    predictions_path = os.path.join(ARTIFACTS_DIR, "predictions.csv")
    
    # Merge validation and test predictions
    df_val_preds = df_val_only[["customer_id", "split", "label", "baseline_prob", "gnn_prob"]]
    df_test_preds = df_test_only[["customer_id", "split", "label", "baseline_prob", "gnn_prob"]]
    
    df_all_preds = pd.concat([df_val_preds, df_test_preds], ignore_index=True)
    df_all_preds.to_csv(predictions_path, index=False)
    print(f"Saved prediction outputs to {predictions_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Baseline and GNN models.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--epochs", type=int, default=50, help="GNN training epochs")
    parser.add_argument("--lr", type=float, default=0.005, help="GNN learning rate")
    parser.add_argument("--hidden-dim", type=int, default=64, help="GNN hidden dimension")
    parser.add_argument("--dropout", type=float, default=0.3, help="GNN dropout rate")
    args = parser.parse_args()
    
    train_pipeline(args)
