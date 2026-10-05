import os
import json
import glob
import pandas as pd

# Update directory path according to your structure
FHIR_DIR = os.path.join("data", "fhir")
if not glob.glob(os.path.join(FHIR_DIR, "*.json")):
    FHIR_DIR = os.path.join("data", "fhir", "fhir")

OUTPUT_DIR = os.path.join("data", "processed")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def clean_id(raw_id: str) -> str:
    """Strips FHIR reference prefixes such as 'urn:uuid:'."""
    if not raw_id:
        return None
    return raw_id.replace("urn:uuid:", "").strip()


def parse_patient(resource: dict) -> dict:
    """Extracts demographic fields from Patient resource."""
    patient_id = clean_id(resource.get("id"))
    gender = resource.get("gender")
    birth_date = resource.get("birthDate")
    deceased_date = resource.get("deceasedDateTime")

    addresses = resource.get("address", [])
    city = addresses[0].get("city") if addresses else None
    state = addresses[0].get("state") if addresses else None

    return {
        "patient_id": patient_id,
        "gender": gender,
        "birth_date": birth_date,
        "deceased_date": deceased_date,
        "city": city,
        "state": state,
    }


def parse_encounter(resource: dict) -> dict:
    """Extracts encounter metadata and duration."""
    encounter_id = clean_id(resource.get("id"))
    subject_ref = resource.get("subject", {}).get("reference")
    patient_id = clean_id(subject_ref)
    encounter_class = resource.get("class", {}).get("code")

    period = resource.get("period", {})
    start_time = period.get("start")
    end_time = period.get("end")

    reason_code = None
    reason_display = None
    reasons = resource.get("reasonCode", [])
    if reasons and "coding" in reasons[0] and reasons[0]["coding"]:
        reason_code = reasons[0]["coding"][0].get("code")
        reason_display = reasons[0]["coding"][0].get("display")

    return {
        "encounter_id": encounter_id,
        "patient_id": patient_id,
        "encounter_class": encounter_class,
        "start_time": start_time,
        "end_time": end_time,
        "reason_code": reason_code,
        "reason_display": reason_display,
    }


def parse_condition(resource: dict) -> dict:
    """
    Extracts diagnosis data, clinical status, and SNOMED codes.
    """
    condition_id = clean_id(resource.get("id"))
    patient_id = clean_id(resource.get("subject", {}).get("reference"))
    encounter_id = clean_id(resource.get("encounter", {}).get("reference"))

    clinical_status = (
        resource.get("clinicalStatus", {})
        .get("coding", [{}])[0]
        .get("code")
    )

    code_coding = resource.get("code", {}).get("coding", [{}])[0]
    snomed_code = code_coding.get("code")
    condition_description = code_coding.get("display")

    onset_date = resource.get("onsetDateTime")
    recorded_date = resource.get("recordedDate")

    return {
        "condition_id": condition_id,
        "patient_id": patient_id,
        "encounter_id": encounter_id,
        "clinical_status": clinical_status,
        "snomed_code": snomed_code,
        "condition_description": condition_description,
        "onset_date": onset_date,
        "recorded_date": recorded_date,
    }


def parse_observation(resource: dict) -> dict:
    """
    Extracts lab measurements and vital signs (LOINC coded).
    """
    obs_id = clean_id(resource.get("id"))
    patient_id = clean_id(resource.get("subject", {}).get("reference"))
    encounter_id = clean_id(resource.get("encounter", {}).get("reference"))

    code_info = resource.get("code", {}).get("coding", [{}])[0]
    loinc_code = code_info.get("code")
    test_name = code_info.get("display")

    effective_date = resource.get("effectiveDateTime")

    # Value extraction (numeric quantity vs code)
    val_quantity = resource.get("valueQuantity", {})
    numeric_value = val_quantity.get("value")
    unit = val_quantity.get("unit")

    return {
        "observation_id": obs_id,
        "patient_id": patient_id,
        "encounter_id": encounter_id,
        "loinc_code": loinc_code,
        "test_name": test_name,
        "effective_date": effective_date,
        "numeric_value": numeric_value,
        "unit": unit,
    }


def run_parsing():
    json_files = glob.glob(os.path.join(FHIR_DIR, "*.json"))
    print(f"Parsing {len(json_files)} FHIR JSON bundles...")

    patients = []
    encounters = []
    conditions = []
    observations = []

    for filepath in json_files:
        with open(filepath, "r", encoding="utf-8") as f:
            try:
                bundle = json.load(f)
            except Exception as e:
                continue

        for entry in bundle.get("entry", []):
            res = entry.get("resource", {})
            rtype = res.get("resourceType")

            if rtype == "Patient":
                patients.append(parse_patient(res))
            elif rtype == "Encounter":
                encounters.append(parse_encounter(res))
            elif rtype == "Condition":
                conditions.append(parse_condition(res))
            elif rtype == "Observation":
                observations.append(parse_observation(res))

    df_patients = pd.DataFrame(patients)
    df_encounters = pd.DataFrame(encounters)
    df_conditions = pd.DataFrame(conditions)
    df_observations = pd.DataFrame(observations)

    # Standardize dates
    df_patients["birth_date"] = pd.to_datetime(df_patients["birth_date"], errors="coerce")
    df_encounters["start_time"] = pd.to_datetime(df_encounters["start_time"], errors="coerce", utc=True)
    df_encounters["end_time"] = pd.to_datetime(df_encounters["end_time"], errors="coerce", utc=True)

    # Save to Parquet
    df_patients.to_parquet(os.path.join(OUTPUT_DIR, "patients.parquet"), index=False)
    df_encounters.to_parquet(os.path.join(OUTPUT_DIR, "encounters.parquet"), index=False)
    df_conditions.to_parquet(os.path.join(OUTPUT_DIR, "conditions.parquet"), index=False)
    df_observations.to_parquet(os.path.join(OUTPUT_DIR, "observations.parquet"), index=False)

    print("\n--- Pipeline Parsing Summary ---")
    print(f"Patients:     {len(df_patients):,}")
    print(f"Encounters:   {len(df_encounters):,}")
    print(f"Conditions:   {len(df_conditions):,}")
    print(f"Observations: {len(df_observations):,}")


if __name__ == "__main__":
    run_parsing()