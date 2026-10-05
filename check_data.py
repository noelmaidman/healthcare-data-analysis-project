import os
import pandas as pd

PROCESSED_DIR = os.path.join("data", "processed")

# Load tables
df_patients = pd.read_parquet(os.path.join(PROCESSED_DIR, "patients.parquet"))
df_encounters = pd.read_parquet(os.path.join(PROCESSED_DIR, "encounters.parquet"))
df_conditions = pd.read_parquet(os.path.join(PROCESSED_DIR, "conditions.parquet"))

print("=== 1. Key Integrity Check ===")
patient_ids = set(df_patients["patient_id"])
orphan_encounters = df_encounters[~df_encounters["patient_id"].isin(patient_ids)]
orphan_conditions = df_conditions[~df_conditions["patient_id"].isin(patient_ids)]
print(f"Orphan encounters: {len(orphan_encounters)}")
print(f"Orphan conditions: {len(orphan_conditions)}")

print("\n=== 2. Inpatient Stays vs Emergency Visits ===")
print(df_encounters["encounter_class"].value_counts())

print("\n=== 3. Top 5 Documented Conditions ===")
print(df_conditions["condition_description"].value_counts().head(5))