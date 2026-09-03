# RePackAI — Machine Learning Classification Model

To support operators with data-driven predictions, RePackAI contains a classification pipeline predicting the likely final disposition of container inspections.

## Features

The model uses both numerical and categorical properties compiled during the physical inspection:

### Categorical Features
*   `container_type` (Box, Pallet, Crate, Drum, Tote)
*   `material` (Cardboard, Wood, Plastic, Metal)
*   `damage_level` (None, Low, Medium, High, Critical)
*   `structural_condition` (Safe, Minor Damage, Moderate Damage, Unsafe)
*   `contamination` (None, Organic, Chemical, Hazardous)
*   `safety_risk` (Low, Medium, High)
*   `location` (Inspection depot)

### Numerical Features
*   `weight_kg`
*   `age_months`
*   `usage_count`
*   `cleanliness_score`
*   `repair_cost`
*   `refurbishment_cost`
*   `resale_value`
*   `recycling_value`
*   `disposal_cost`
*   `carbon_repair`, `carbon_refurbish`, `carbon_resell`, `carbon_recycle`, `carbon_dispose`

## Pipeline Architecture

1.  **Imputation**:
    *   Median values for missing numerical metrics (`cleanliness_score`).
    *   Most frequent value for missing categorical attributes (`damage_level`).
2.  **Encoder**:
    *   One-Hot Encoding for categorical features.
3.  **Classifier**:
    *   `RandomForestClassifier` (100 estimators, max depth 12).

## Performance Comparison (Phase 1)

| Model | Test Accuracy | Note |
| :--- | :--- | :--- |
| **Rule-Based Heuristic (Baseline)** | 38.36% | Simplistic mappings based on damage level alone. |
| **Random Forest Classifier (Intelligent)** | 97.73% | High accuracy, predicting complex multi-factor dispositions. |

## Model Storage

The trained Scikit-learn Pipeline is saved as a joblib object under:
*   `models/repack_model.joblib`
