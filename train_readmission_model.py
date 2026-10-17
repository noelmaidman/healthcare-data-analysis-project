#----readmission prediction----

import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from google.cloud import bigquery
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Resolve absolute path to service account key
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEY_PATH = os.path.join(BASE_DIR, "gcp_key.json")
if not os.path.exists(KEY_PATH):
    alt_path = os.path.join(BASE_DIR, "gcp_key.json.json")
    if os.path.exists(alt_path):
        KEY_PATH = alt_path
    else:
        raise FileNotFoundError(f"Key file not found at: {KEY_PATH}")

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = KEY_PATH

# Initialize BigQuery client
PROJECT_ID = "healthcare-analytics-510707"
client = bigquery.Client(project=PROJECT_ID)

# Query inpatient encounters joined with patient dimensions
query = f"""
SELECT 
    f.encounter_id,
    f.patient_id,
    f.length_of_stay_days,
    f.is_ed_admission,
    f.is_readmission_30d,
    p.gender,
    p.current_age,
    p.has_heart_failure,
    p.has_breast_cancer,
    p.has_diabetes,
    p.has_hypertension,
    p.has_copd,
    p.has_chronic_kidney_disease
FROM `{PROJECT_ID}.analytics_healthcare.fct_encounters` f
INNER JOIN `{PROJECT_ID}.analytics_healthcare.dim_patients` p
    ON f.patient_id = p.patient_id
WHERE f.encounter_class = 'IMP'
"""

print("Fetching dataset from BigQuery...")
df = client.query(query).to_dataframe()
print(f"Retrieved {len(df)} records for training.\n")

# Feature preprocessing
df["gender_female"] = (df["gender"] == "F").astype(int)

feature_cols = [
    "current_age",
    "gender_female",
    "length_of_stay_days",
    "is_ed_admission",
    "has_heart_failure",
    "has_breast_cancer",
    "has_diabetes",
    "has_hypertension",
    "has_copd",
    "has_chronic_kidney_disease",
]

X = df[feature_cols]
y = df["is_readmission_30d"]

# Train/Test Split (80/20 with stratified target distribution)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)

# Standardize numerical features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train Logistic Regression model with balanced class weights
model = LogisticRegression(class_weight="balanced", random_state=42, max_iter=1000)
model.fit(X_train_scaled, y_train)

# Predictions and probabilities
y_pred = model.predict(X_test_scaled)
y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]

# Model evaluation
auc_score = roc_auc_score(y_test, y_pred_proba)
print("=== Model Performance on Test Set ===")
print(f"ROC-AUC Score: {auc_score:.4f}\n")
print("Classification Report:")
print(classification_report(y_test, y_pred))

# Odds Ratios and Feature Importance
coefficients = pd.DataFrame({
    "Feature": feature_cols,
    "Coefficient": model.coef_[0],
    "Odds_Ratio": np.exp(model.coef_[0]),
}).sort_values(by="Coefficient", ascending=False)

print("=== Feature Coefficients and Odds Ratios ===")
print(coefficients.to_string(index=False))

# Visualization: Confusion Matrix and ROC Curve
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Plot 1: Confusion Matrix
cm = confusion_matrix(y_test, y_pred)
sns.heatmap(
    cm,
    annot=True,
    fmt="d",
    cmap="Blues",
    cbar=False,
    ax=axes[0],
    xticklabels=["No Readmission (0)", "Readmission (1)"],
    yticklabels=["No Readmission (0)", "Readmission (1)"],
)
axes[0].set_title("Confusion Matrix (Test Set)")
axes[0].set_xlabel("Predicted")
axes[0].set_ylabel("Actual")

# Plot 2: ROC Curve
fpr, tpr, _ = roc_curve(y_test, y_pred_proba)
axes[1].plot(fpr, tpr, color="darkorange", lw=2, label=f"ROC curve (AUC = {auc_score:.2f})")
axes[1].plot([0, 1], [0, 1], color="navy", lw=1.5, linestyle="--")
axes[1].set_xlim([0.0, 1.0])
axes[1].set_ylim([0.0, 1.05])
axes[1].set_xlabel("False Positive Rate")
axes[1].set_ylabel("True Positive Rate (Recall)")
axes[1].set_title("Receiver Operating Characteristic (ROC)")
axes[1].legend(loc="lower right")

plt.tight_layout()
output_plot = os.path.join(BASE_DIR, "logistic_regression_performance.png")
plt.savefig(output_plot, dpi=300)
print(f"\nEvaluation plots saved to: {output_plot}")
plt.show()

