import os
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from google.cloud import bigquery

# Resolve the absolute path to the project root directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEY_PATH = os.path.join(BASE_DIR, "gcp_key.json")

# Verify key file existence
if not os.path.exists(KEY_PATH):
    # Check if Windows appended an extra .json extension
    alt_path = os.path.join(BASE_DIR, "gcp_key.json.json")
    if os.path.exists(alt_path):
        KEY_PATH = alt_path
    else:
        raise FileNotFoundError(f"Key file not found at: {KEY_PATH}")

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = KEY_PATH

# Initialize BigQuery client
PROJECT_ID = "healthcare-analytics-510707"
client = bigquery.Client(project=PROJECT_ID)

# Star Schema query: joining fact table with dimension table for inpatient encounters
query = f"""
SELECT 
    f.encounter_id,
    f.patient_id,
    f.encounter_class,
    f.length_of_stay_days,
    f.is_readmission_30d,
    f.is_ed_admission,
    p.gender,
    p.current_age,
    p.age_group,
    p.has_heart_failure,
    p.has_breast_cancer,
    p.has_diabetes,
    p.has_hypertension,
    p.has_copd
FROM `{PROJECT_ID}.analytics_healthcare.fct_encounters` f
INNER JOIN `{PROJECT_ID}.analytics_healthcare.dim_patients` p
    ON f.patient_id = p.patient_id
WHERE f.encounter_class = 'IMP'
"""

# Fetch data from BigQuery into pandas DataFrame
print("Querying data from BigQuery...")
df_inpatient = client.query(query).to_dataframe()
print(f"Data retrieved successfully! Total inpatient records: {len(df_inpatient)}\n")

# Display first 5 rows
print(
    df_inpatient[
        [
            "encounter_id",
            "age_group",
            "length_of_stay_days",
            "is_readmission_30d",
        ]
    ].head()
)
# Define chronological order for age categories
age_order = ["<18", "18-35", "36-50", "51-65", "65+"]

# Plot: Length of stay by age group with explicit ordering
plt.figure(figsize=(10, 6))
sns.boxplot(
    data=df_inpatient,
    x="age_group",
    y="length_of_stay_days",
    order=age_order,
    palette="Set2",
)
plt.title("Length of Stay (Days) by Age Group - Inpatient Admissions")
plt.xlabel("Age Group")
plt.ylabel("Length of Stay (Days)")
plt.ylim(0, 15)
plt.tight_layout()
# Save the plot to an image file in the project folder
plt.savefig("los_by_age_group.png", dpi=300)
plt.show()


# -------------------------------------------------------------
# Analysis 2: 30-Day Readmission Rate by Chronic Condition
# -------------------------------------------------------------

# Dictionary mapping condition column names to display labels
conditions = {
    "has_heart_failure": "Heart Failure",
    "has_breast_cancer": "Breast Cancer",
    "has_diabetes": "Diabetes",
    "has_hypertension": "Hypertension",
    "has_copd": "COPD",
}

# Calculate readmission metrics per chronic condition using existing df_inpatient
metrics = []
for col, label in conditions.items():
    subset = df_inpatient[df_inpatient[col] == 1]
    total_encounters = len(subset)
    readmissions = subset["is_readmission_30d"].sum()
    rate = (readmissions / total_encounters * 100) if total_encounters > 0 else 0

    metrics.append(
        {
            "Condition": label,
            "Total Admissions": total_encounters,
            "Readmissions": int(readmissions),
            "Readmission Rate (%)": round(rate, 2),
        }
    )

# Baseline: overall inpatient readmission rate
overall_admissions = len(df_inpatient)
overall_readmissions = df_inpatient["is_readmission_30d"].sum()
overall_rate = round((overall_readmissions / overall_admissions) * 100, 2)

df_metrics = pd.DataFrame(metrics).sort_values(
    by="Readmission Rate (%)", ascending=False
)
print("\n=== Readmission Rate Summary by Chronic Condition ===")
print(df_metrics.to_string(index=False))
print(f"\nOverall Readmission Rate: {overall_rate}%\n")

# Plot: 30-Day Readmission Rate by Chronic Condition
plt.figure(figsize=(10, 6))
barplot = sns.barplot(
    data=df_metrics,
    x="Condition",
    y="Readmission Rate (%)",
    palette="Blues_r",
    hue="Condition",
    legend=False,
)

# Reference line for overall average readmission rate
plt.axhline(
    overall_rate,
    color="crimson",
    linestyle="--",
    linewidth=1.5,
    label=f"Overall Avg ({overall_rate}%)",
)

# Add percentage labels above bars
for p in barplot.patches:
    height = p.get_height()
    if height > 0:
        barplot.annotate(
            f"{height:.1f}%",
            (p.get_x() + p.get_width() / 2.0, height),
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
            xytext=(0, 4),
            textcoords="offset points",
        )

plt.title(
    "30-Day Inpatient Readmission Rate by Chronic Condition",
    fontsize=14,
    pad=15,
)
plt.xlabel("Chronic Condition", fontsize=12)
plt.ylabel("Readmission Rate (%)", fontsize=12)
plt.ylim(0, max(df_metrics["Readmission Rate (%)"].max() * 1.15, 30))
plt.xticks(rotation=20, ha="right")
plt.legend(loc="upper right")
plt.tight_layout()

# Save the plot
plt.savefig("readmission_rates_by_condition.png", dpi=300)
print("Plot saved successfully to: readmission_rates_by_condition.png")

plt.show()