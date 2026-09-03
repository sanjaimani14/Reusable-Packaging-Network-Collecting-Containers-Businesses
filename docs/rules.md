# RePackAI — Rules Reference

Deterministic business rules are executed at the start of the recommendation process. These rules are fully transparent, customizable, and cannot be bypassed by the machine learning classification models.

## Detailed Rule Catalog

| Rule Name | Checked Fields | Trigger Condition | Severity | Prohibited Actions | Explanation / Rationale |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Safety Constraint** | `structural_condition`, `safety_risk` | `structural_condition == "Unsafe"` or `safety_risk == "High"` | **CRITICAL** | `RESELL`, `REPAIR`, `REFURBISH` | Prevent unsafe containers from re-entering circulation to protect operators and client staff. |
| **Contamination Constraint** | `contamination` | `contamination == "Hazardous"` | **CRITICAL** | `RESELL`, `REPAIR`, `REFURBISH`, `RECYCLE` | Hazardous contamination requires immediate disposal under regulated containment. Recycled material would be toxic. |
| **Recycling Constraint** | `recyclable`, `contamination` | `recyclable == False` or `contamination == "Hazardous"` | **WARNING** | `RECYCLE` | Prevents the system from suggesting recycling for materials (like specific treated plastics/wood) that cannot be processed. |
| **Completeness Constraint** | `inspection_completeness` | `inspection_completeness < 0.8` | **WARNING** | None (forces escalation) | Automatically marks recommendations with missing critical inspection values for manual operator review. |

## Custom Rule Customization

Rules are implemented as pure Python code in the [RuleEngine](file:///g:/project/coe%20project/repackai/backend/app/rules/engine.py) helper, ensuring they can be unit-tested without database overhead.

Any action marked as prohibited will have its composite recommendation score set to $-1.0$.
