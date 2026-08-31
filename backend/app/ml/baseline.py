import joblib
from sklearn.ensemble import HistGradientBoostingClassifier

class TabularBaselineModel:
    """Non-graph GBDT baseline model using HistGradientBoostingClassifier."""
    
    def __init__(self, random_state=42):
        self.model = HistGradientBoostingClassifier(
            class_weight="balanced",
            random_state=random_state,
            max_iter=100,
            learning_rate=0.1,
            max_depth=5
        )
        self.feature_cols = [
            "account_age_days", "transaction_count", "total_transaction_amount",
            "average_transaction_amount", "median_transaction_amount", "transaction_amount_std",
            "coupon_usage_count", "unique_coupons_used", "referrals_made", "was_referred",
            "device_customer_count", "ip_customer_count", "active_days",
            "average_transactions_per_active_day", "night_transaction_ratio",
            "device_degree", "ip_degree", "coupon_degree", "referral_in_degree", "referral_out_degree"
        ]
        
    def fit(self, df_train):
        """Train the model on customer features."""
        X_train = df_train[self.feature_cols].values
        y_train = df_train["label"].values
        self.model.fit(X_train, y_train)
        
    def predict_proba(self, df_eval):
        """Predict probability of fraud for evaluation customer records."""
        X_eval = df_eval[self.feature_cols].values
        # Probabilities for class 1 (fraud)
        return self.model.predict_proba(X_eval)[:, 1]
        
    def save(self, filepath):
        """Save the trained model to disk."""
        joblib.dump(self.model, filepath)
        print(f"Saved baseline GBDT model to {filepath}")
        
    def load(self, filepath):
        """Load a trained model from disk."""
        self.model = joblib.load(filepath)
        print(f"Loaded baseline GBDT model from {filepath}")
