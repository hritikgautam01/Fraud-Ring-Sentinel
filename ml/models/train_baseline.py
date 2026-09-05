"""
Sentinel — Coordinated Payment Abuse Intelligence
Baseline ML Model: Transaction-Level Random Forest Classifier

Purpose:
Trains a baseline Machine Learning model (Random Forest Classifier) to predict
whether an individual transaction is fraudulent based on single-transaction features.

Note:
This baseline operates purely on transaction-level features (amount, account age,
velocity metrics, device/card counts). It does NOT perform graph analysis,
multi-account ring detection, or LLM-based investigation.
"""

import os
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

# ==============================================================================
# 1. LOAD DATASET
# ==============================================================================
# Dynamically locate dataset path relative to script location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
DATA_PATH = os.path.join(PROJECT_ROOT, "ml", "data", "raw", "transactions.csv")

print(f"Loading transaction dataset from: {DATA_PATH}")
df = pd.read_csv(DATA_PATH)
print(f"Dataset successfully loaded. Total shape: {df.shape[0]} rows, {df.shape[1]} columns.\n")


# ==============================================================================
# 2. SELECT INPUT FEATURES & TARGET VARIABLE
# ==============================================================================
# WHY: We select numerical transaction behavioral features.
# EXCLUSIONS:
# - ID columns (transaction_id, user_id, device_id, ip_id, card_id, merchant_id) 
#   are excluded to prevent overfitting on arbitrary synthetic identifiers.
# - fraud_scenario is excluded as it is evaluation metadata (causes data leakage if included!).
# - is_fraud is our ground truth target label.

features = [
    "amount",
    "account_age_days",
    "transactions_last_hour",
    "transactions_last_day",
    "failed_transactions",
    "unique_devices",
    "unique_cards"
]

target = "is_fraud"

# 3. Create X (input features) and y (target label)
X = df[features]
y = df[target]

print(f"Input features selected ({len(features)}): {features}")
print(f"Target variable: {target}\n")


# ==============================================================================
# 4. SPLIT INTO TRAINING & TESTING SETS
# ==============================================================================
# WHY: We split data into 80% training (to teach the model) and 20% testing
# (to evaluate how well the model generalizes to unseen transactions).
# 'stratify=y' ensures both train and test sets have the exact same 90:10 ratio of legit:fraud.
# 'random_state=42' ensures full reproducibility.

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print(f"Training set size: {len(X_train)} samples")
print(f"Testing set size:  {len(X_test)} samples\n")


# ==============================================================================
# 5. INITIALIZE & TRAIN THE RANDOM FOREST MODEL
# ==============================================================================
# WHY: Random Forest is an ensemble of decision trees. It handles non-linear
# feature interactions well, is resilient to outliers, and provides feature importance scores.

model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)

print("Training Random Forest Classifier baseline model...")
model.fit(X_train, y_train)
print("Training complete!\n")


# ==============================================================================
# 6. MAKE PREDICTIONS ON UNSEEN TEST DATA
# ==============================================================================
predictions = model.predict(X_test)


# ==============================================================================
# 7. EVALUATE MODEL PERFORMANCE
# ==============================================================================
print("=" * 60)
print("CLASSIFICATION EVALUATION REPORT")
print("=" * 60)
print(classification_report(y_test, predictions, target_names=["Legitimate (0)", "Fraud (1)"]))

# Confusion Matrix Breakdown
cm = confusion_matrix(y_test, predictions)
tn, fp, fn, tp = cm.ravel()

legit_test_count = sum(y_test == 0)
fraud_test_count = sum(y_test == 1)
fraud_predicted_count = sum(predictions == 1)
fraud_correctly_detected = tp

print("=" * 60)
print("DETAILED TRANSACTION METRICS BREAKDOWN")
print("=" * 60)
print(f"  • Total Legitimate transactions in test set : {legit_test_count}")
print(f"  • Total Fraud transactions in test set      : {fraud_test_count}")
print(f"  • Total Fraud transactions predicted        : {fraud_predicted_count}")
print(f"  • Fraud transactions correctly detected (TP): {fraud_correctly_detected}")
print(f"  • False Positives (Legit flagged as fraud)  : {fp}")
print(f"  • False Negatives (Fraud missed by model)  : {fn}\n")

print("Confusion Matrix:")
print(f"                Predicted Legit  Predicted Fraud")
print(f"Actual Legit :       {tn:5d}            {fp:5d}")
print(f"Actual Fraud :       {fn:5d}            {tp:5d}\n")


# ==============================================================================
# 8. FEATURE IMPORTANCE RANKING (EXPLAINABILITY)
# ==============================================================================
# WHY: Feature importance shows which transaction characteristics the Random Forest
# relied on most heavily to distinguish legitimate transactions from fraud.

importances = model.feature_importances_
feature_importance_tuples = sorted(zip(features, importances), key=lambda x: x[1], reverse=True)

print("=" * 60)
print("FEATURE IMPORTANCE RANKING (Most Important -> Least Important)")
print("=" * 60)
for rank, (feat_name, score) in enumerate(feature_importance_tuples, start=1):
    print(f"  {rank}. {feat_name:25s}: {score * 100:6.2f}% (score: {score:.4f})")
print("=" * 60)