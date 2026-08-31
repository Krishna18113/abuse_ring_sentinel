import os
import json
import pandas as pd
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    average_precision_score,
    roc_auc_score,
    confusion_matrix
)
from app.ml.utils import calculate_costs, ARTIFACTS_DIR

def run_evaluation():
    # Load config and prediction outputs
    config_path = os.path.join(ARTIFACTS_DIR, "training_config.json")
    predictions_path = os.path.join(ARTIFACTS_DIR, "predictions.csv")
    
    if not os.path.exists(config_path) or not os.path.exists(predictions_path):
        print("ERROR: Missing config or predictions files. Run training first.")
        return
        
    with open(config_path, "r") as f:
        config = json.load(f)
        
    df_preds = pd.read_csv(predictions_path)
    
    # Filter strictly to the test set to evaluate future generalization
    df_test = df_preds[df_preds["split"] == "test"].copy()
    
    if df_test.empty:
        print("ERROR: Test predictions are empty!")
        return
        
    y_true = df_test["label"].values
    
    # Retrieve thresholds
    base_thresh = config["baseline_threshold"]
    gnn_thresh = config["gnn_threshold"]
    fp_cost = config["fp_cost"]
    fn_cost = config["fn_cost"]
    
    # -------------------------------------------------------------
    # Calculate baseline metrics
    # -------------------------------------------------------------
    base_probs = df_test["baseline_prob"].values
    base_preds = (base_probs >= base_thresh).astype(int)
    
    tn_b, fp_b, fn_b, tp_b = confusion_matrix(y_true, base_preds).ravel()
    fpr_b = fp_b / (fp_b + tn_b) if (fp_b + tn_b) > 0 else 0.0
    
    base_prec = precision_score(y_true, base_preds)
    base_rec = recall_score(y_true, base_preds)
    base_f1 = f1_score(y_true, base_preds)
    base_pr_auc = average_precision_score(y_true, base_probs)
    base_roc_auc = roc_auc_score(y_true, base_probs)
    
    base_costs = calculate_costs(fp_b, fn_b, fp_cost, fn_cost)
    
    # -------------------------------------------------------------
    # Calculate GNN metrics
    # -------------------------------------------------------------
    gnn_probs = df_test["gnn_prob"].values
    gnn_preds = (gnn_probs >= gnn_thresh).astype(int)
    
    tn_g, fp_g, fn_g, tp_g = confusion_matrix(y_true, gnn_preds).ravel()
    fpr_g = fp_g / (fp_g + tn_g) if (fp_g + tn_g) > 0 else 0.0
    
    gnn_prec = precision_score(y_true, gnn_preds)
    gnn_rec = recall_score(y_true, gnn_preds)
    gnn_f1 = f1_score(y_true, gnn_preds)
    gnn_pr_auc = average_precision_score(y_true, gnn_probs)
    gnn_roc_auc = roc_auc_score(y_true, gnn_probs)
    
    gnn_costs = calculate_costs(fp_g, fn_g, fp_cost, fn_cost)
    
    # -------------------------------------------------------------
    # Calculate comparison improvements
    # -------------------------------------------------------------
    f1_diff = gnn_f1 - base_f1
    pr_auc_diff = gnn_pr_auc - base_pr_auc
    rec_diff = gnn_rec - base_rec
    prec_diff = gnn_prec - base_prec
    cost_diff = base_costs["total_cost"] - gnn_costs["total_cost"]
    
    # -------------------------------------------------------------
    # Save metrics JSON
    # -------------------------------------------------------------
    metrics_summary = {
        "tabular_baseline": {
            "precision": float(base_prec),
            "recall": float(base_rec),
            "f1": float(base_f1),
            "pr_auc": float(base_pr_auc),
            "roc_auc": float(base_roc_auc),
            "false_positives": int(fp_b),
            "false_negatives": int(fn_b),
            "false_positive_rate": float(fpr_b),
            "fp_cost": float(base_costs["fp_cost"]),
            "fn_cost": float(base_costs["fn_cost"]),
            "total_cost": float(base_costs["total_cost"])
        },
        "graph_sage": {
            "precision": float(gnn_prec),
            "recall": float(gnn_rec),
            "f1": float(gnn_f1),
            "pr_auc": float(gnn_pr_auc),
            "roc_auc": float(gnn_roc_auc),
            "false_positives": int(fp_g),
            "false_negatives": int(fn_g),
            "false_positive_rate": float(fpr_g),
            "fp_cost": float(gnn_costs["fp_cost"]),
            "fn_cost": float(gnn_costs["fn_cost"]),
            "total_cost": float(gnn_costs["total_cost"])
        },
        "improvements": {
            "f1": float(f1_diff),
            "pr_auc": float(pr_auc_diff),
            "recall": float(rec_diff),
            "precision": float(prec_diff),
            "cost_saving": float(cost_diff)
        }
    }
    
    metrics_summary_path = os.path.join(ARTIFACTS_DIR, "metrics.json")
    with open(metrics_summary_path, "w") as f:
        json.dump(metrics_summary, f, indent=4)
        
    # -------------------------------------------------------------
    # Print Comparative Report
    # -------------------------------------------------------------
    prevalence = y_true.sum() / len(y_true)
    
    print("\n=== Abuse Ring Sentinel — Phase 3 ===")
    print(f"\nDataset scale (Test split size): {len(y_true)} customers")
    print(f"Abuse prevalence in test split:  {prevalence:.2%}")
    print(f"Validation threshold selected:  Baseline={base_thresh:.2f}, GraphSAGE={gnn_thresh:.2f}")
    
    print("\n----------------------------------------")
    print("TABULAR BASELINE (GBDT)")
    print("----------------------------------------")
    print(f"Precision:           {base_prec:.4f}")
    print(f"Recall:              {base_rec:.4f}")
    print(f"F1:                  {base_f1:.4f}")
    print(f"PR-AUC:              {base_pr_auc:.4f}")
    print(f"ROC-AUC:             {base_roc_auc:.4f}")
    print(f"False Positives:     {fp_b} (FPR = {fpr_b:.4%})")
    print(f"False Negatives:     {fn_b}")
    print(f"Expected FP Cost:    INR {base_costs['fp_cost']:,.2f}")
    print(f"Expected FN Cost:    INR {base_costs['fn_cost']:,.2f}")
    print(f"Total Expected Cost: INR {base_costs['total_cost']:,.2f}")
    
    print("\n----------------------------------------")
    print("GRAPH SAGE (GNN)")
    print("----------------------------------------")
    print(f"Precision:           {gnn_prec:.4f}")
    print(f"Recall:              {gnn_rec:.4f}")
    print(f"F1:                  {gnn_f1:.4f}")
    print(f"PR-AUC:              {gnn_pr_auc:.4f}")
    print(f"ROC-AUC:             {gnn_roc_auc:.4f}")
    print(f"False Positives:     {fp_g} (FPR = {fpr_g:.4%})")
    print(f"False Negatives:     {fn_g}")
    print(f"Expected FP Cost:    INR {gnn_costs['fp_cost']:,.2f}")
    print(f"Expected FN Cost:    INR {gnn_costs['fn_cost']:,.2f}")
    print(f"Total Expected Cost: INR {gnn_costs['total_cost']:,.2f}")
    
    print("\n----------------------------------------")
    print("COMPARISON (GNN vs GBDT)")
    print("----------------------------------------")
    print(f"F1 Improvement:       {f1_diff:+.4f}")
    print(f"PR-AUC Improvement:   {pr_auc_diff:+.4f}")
    print(f"Recall Improvement:   {rec_diff:+.4f}")
    print(f"Precision Improvement: {prec_diff:+.4f}")
    print(f"Business Cost Saving:  INR {cost_diff:,.2f} ({cost_diff/base_costs['total_cost']:+.2%} error cost reduction)")
    print("----------------------------------------")
    print("Overall: COMPLETE\n")

if __name__ == "__main__":
    run_evaluation()
