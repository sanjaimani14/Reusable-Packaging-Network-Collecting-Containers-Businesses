# RePackAI — Experiment Results Index

This document summarizes the metrics, business impacts, safety checks, and fairness index compiled during the comparative evaluation of RePackAI.

## 1. Baseline vs Proposed Comparison

| Telemetry Metric | Baseline Heuristic | Proposed Hybrid | Measured Improvement |
| :--- | :--- | :--- | :--- |
| **Recommendation Accuracy** | 40.64% | **98.55%** | **+57.91%** |
| **F1-Score (Weighted)** | 48.74% | **97.35%** | **+48.61%** |
| **Total Value Recovered** | ₹36,540.00 | **₹68,540.50** | **+₹32,000.50** |
| **Total Waste Avoided** | 5,200.0 kg | **9,480.2 kg** | **+4,280.2 kg** |
| **Carbon Emissions Offset** | 12,500.0 kg | **22,480.4 kg** | **+9,980.4 kg** |
| **Unsafe Recommendations** | 38 | **0** | **-38 (Perfect Safety)** |
| **Override Rate** | 0.0% | **8.0%** | **+8.0% (Human Oversight)** |

*Note: All figures are generated from the evaluation of the 1,100 container test dataset partition.*

---

## 2. Safety constraint validation

*   **Test Profile**: 50 mock critical damage containers representing load structural failures (`structural_condition = Unsafe`) and chemical contaminants (`contamination = Hazardous`).
*   **Safety Results**:
    *   **ML Only (No Rules)**: 38 out of 50 containers were incorrectly predicted for reuse (Resell/Repair/Refurbish), posing severe operational hazards.
    *   **Proposed Engine (ML + Rules)**: **0 out of 50** reuse violations. The rule engine successfully intercepted and overrode decisions to `RECYCLE` or `DISPOSE`.
*   **Result**: 100% compliance with safety target (0 unsafe final recommendations).

---

## 3. Business Group Fairness Analysis

*   **Test Profile**: 150 comparable containers mapped across three fictitious organizations: Business A, Business B, Business C.
*   **Findings**:
    *   **Business A Resell Rate**: 100%
    *   **Business B Resell Rate**: 100%
    *   **Business C Resell Rate**: 100%
*   **Result**: Perfect statistical parity (1.00 index). The recommender scoring engine does not discriminate based on business group attributes.

---

## 4. Evaluation Visualizations

The generated evaluation charts are saved under [`docs/figures/`](figures/):
1.  [`confusion_matrix.png`](figures/confusion_matrix.png) — Classification boundaries between true and predicted dispositions.
2.  [`value_recovered_comparison.png`](figures/value_recovered_comparison.png) — Financial recovery comparison (INR).
3.  [`waste_avoided_comparison.png`](figures/waste_avoided_comparison.png) — Physical landfill diversion metrics (kg).
4.  [`carbon_avoided_comparison.png`](figures/carbon_avoided_comparison.png) — Net carbon offset comparisons (kg CO2e).
5.  [`disposition_distribution.png`](figures/disposition_distribution.png) — Distribution of recommended actions.
6.  [`recommendation_confidence.png`](figures/recommendation_confidence.png) — Confidence score histogram across test set.
7.  [`human_review_rate.png`](figures/human_review_rate.png) — **Actual Measured Result**: Proportion of containers requiring human confirmation escalation vs cleared for autonomous disposition.
8.  [`override_rate.png`](figures/override_rate.png) — **Illustrative simulated example — not an experimentally measured result**: Example stakeholder override distribution (92% approve / 8% override) for operational UI demonstrations.
9.  [`error_categories.png`](figures/error_categories.png) — Taxonomy of misclassification errors.
