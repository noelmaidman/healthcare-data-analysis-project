# Healthcare Data Analysis Project

End-to-end analysis of synthetic patient data: FHIR bundles → parquet tables → BigQuery star schema → readmission analysis and a predictive model.

The data is [Synthea](https://synthetichealth.github.io/synthea/) synthetic FHIR R4 (`synthea_sample_data_fhir_r4_nov2021.zip`), so no real patient information is involved.

## Pipeline

```
Synthea FHIR JSON  ──►  src/parse_fhir.py  ──►  data/processed/*.parquet
                                                        │
                                                 check_data.py (validation)
                                                        │
                                          BigQuery: analytics_healthcare
                                          ├─ fct_encounters  (fact)
                                          └─ dim_patients    (dimension)
                                                        │
                          ┌─────────────────────────────┴───────────────┐
                 analyze_encounters.py                      train_readmission_model.py
                 (LOS and readmission charts)               (logistic regression)
```

## Project structure

| Path | Purpose |
|------|---------|
| `src/parse_fhir.py` | Parses FHIR patient bundles into `patients`, `encounters` and `conditions` parquet tables in `data/processed/` |
| `check_data.py` | Validates the parsed tables: orphan keys, encounter class counts, top conditions |
| `analyze_encounters.py` | Queries BigQuery and produces the length-of-stay and readmission charts |
| `train_readmission_model.py` | Trains and evaluates a 30-day readmission classifier |
| `data/` | Raw and processed data (git-ignored) |
| `dbt/`, `sql/`, `notebooks/`, `dashboard/`, `docs/` | Placeholder folders, currently empty |
| `Healthcare Data Analyst Project Plan.pdf` | Original project plan |

## Analyses

- **Length of stay by age group** (`los_by_age_group.png`): boxplots of inpatient stay length across `<18`, `18-35`, `36-50`, `51-65` and `65+`.
- **30-day readmission rate by chronic condition** (`readmission_rates_by_condition.png`): heart failure, breast cancer, diabetes, hypertension and COPD, compared against the overall rate.
- **Readmission model** (`logistic_regression_performance.png`): logistic regression with balanced class weights, using age, gender, length of stay, ED admission and six chronic-condition flags (the five above plus chronic kidney disease). It uses an 80/20 stratified split and reports ROC-AUC, a classification report, odds ratios, a confusion matrix and an ROC curve.

## Setup

Requires Python 3 and, for the analysis scripts, a Google Cloud project with the BigQuery tables above.

```powershell
python -m venv venv
venv\Scripts\activate
pip install pandas pyarrow matplotlib seaborn scikit-learn numpy google-cloud-bigquery db-dtypes
```

There is no `requirements.txt` yet, so the package list above is inferred from the imports.

### 1. Parse the data

Unzip the Synthea archive into `data/fhir/` so the JSON bundles sit in `data/fhir/` (or `data/fhir/fhir/`), then run from the project root:

```powershell
python src/parse_fhir.py
python check_data.py
```

### 2. Run the analyses

The scripts read a GCP service-account key from `gcp_key.json` in the project root (`gcp_key.json.json` is also accepted). Keys are git-ignored (`*.json`); never commit them.

```powershell
python analyze_encounters.py
python train_readmission_model.py
```

Both scripts use the BigQuery project `healthcare-analytics-510707` and expect the `analytics_healthcare.fct_encounters` and `analytics_healthcare.dim_patients` tables to exist. Change `PROJECT_ID` in each script to use your own project.

## Notes

- The scripts that build `fct_encounters` and `dim_patients` (derived fields such as `age_group`, `length_of_stay_days`, `is_readmission_30d` and the `has_*` flags) are not in this repository yet. The `dbt/` and `sql/` folders are the intended home for them.
- `length_of_stay_days` is also a model feature, so check for leakage and interpret the odds ratios with care.
