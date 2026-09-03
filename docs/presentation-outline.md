# RePackAI — Presentation Outline & Slide Deck Structure

This presentation outline covers 12 highly structured slides to present the RePackAI platform to operational leads and stakeholders.

---

### Slide 1: Title & Vision
*   **Slide Title**: RePackAI — Intelligent Packaging Disposition Recommender
*   **Sub-title**: Balancing Financial Recovery, Environmental Offset, and Operational Safety.
*   **Speaker Notes**: Welcome stakeholders. Today we present RePackAI, a platform to classify returned industrial containers using hybrid AI and safety rules.

---

### Slide 2: The Core Problem
*   **Slide Title**: The Reusable Packaging Classification Gap
*   **Key Points**:
    *    intake terminals collect containers without structured classifications.
    *   No dynamic checks: containers are routed arbitrarily to resell, repair, recycling, or landfills.
    *   Lost recovery margins (scrap metal sold as general waste) and high safety risks.

---

### Slide 3: Pain Points of Manual Routing
*   **Slide Title**: Pain Points & Operational Constraints
*   **Key Points**:
    *   **Financial Leakage**: Inability to calculate net value (resale value vs repair costs) on site.
    *   **Regulatory Penalties**: Hazardous containers accidentally recirculated.
    *   **Uptime Losses**: Lack of offline capability at shipping docks.

---

### Slide 4: The Proposed Solution
*   **Slide Title**: Proposed Solution: RePackAI
*   **Key Points**:
    *   A hybrid decision-support system running locally on warehouse tablets.
    *   Combines deterministic safety rules, net calculations, and ML classifier predictions.
    *   Promotes human-in-the-loop validation for high-impact decisions.

---

### Slide 5: Field Operations Workflow
*   **Slide Title**: End-to-End Field Workflow
*   **Visuals**: Flow diagram mapping returned containers intake $\rightarrow$ sensor readings $\rightarrow$ AI scoring $\rightarrow$ manager approval gates $\rightarrow$ audit trail commits.
*   **Offline Handling**: Demonstrates store-and-forward branching.

---

### Slide 6: System Architecture
*   **Slide Title**: Modular Clean Architecture
*   **Key Points**:
    *   **Backend**: Python FastAPI with SQLAlchemy models.
    *   **Frontend**: React (TypeScript) SPA served with Nginx.
    *   **Rule Engine & ML**: Decoupled validator libraries (scikit-learn + pandas).

---

### Slide 7: AI + Rules Engine
*   **Slide Title**: Redundant Safety Boundaries
*   **Key Points**:
    *   Rules are executed **first** (safety, bio-hazards, non-recyclables).
    *   Prohibited actions are blocked from search space (score set to -1.0).
    *   ML classifier (Random Forest) recommends historical mappings on allowed options.

---

### Slide 8: Enterprise Dashboard
*   **Slide Title**: Live Operations Telemetry Dashboard
*   **Key Points**:
    *   Real-time aggregation of value recovered (₹), waste diverted (kg), and carbon offset (kg CO2).
    *   Interactive charts (Recharts) for disposition distribution and net values.

---

### Slide 9: Explainability & Overrides
*   **Slide Title**: Explainable AI & Human Oversight
*   **Key Points**:
    *   **Why this Recommendation?** panel translates metrics into human-readable checks.
    *   Alternatives comparison matrix displays net value and offset of all 5 pathways.
    *   Mandatory justification log for overrides.

---

### Slide 10: Baseline vs Proposed Results
*   **Slide Title**: Performance Evaluation Results
*   **Metrics Table**:
    *   **Accuracy Boost**: 40.64% (Baseline) $\rightarrow$ 98.55% (Proposed).
    *   **Recovered Margin**: +₹32,000.50 (+87% increase).
    *   **Waste Diverted**: 9,480 kg vs 5,200 kg.

---

### Slide 11: Failure Resilience & Offline Caching
*   **Slide Title**: Fault Tolerance & Offline Store-and-Forward
*   **Key Points**:
    *   Automatic offline detection banner.
    *   LocalStorage caching prevents data losses.
    *   Safe manual overrides block rule-violating selections.

---

### Slide 12: Business Impact & Future Scope
*   **Slide Title**: Impact Summary & Future Scope
*   **Key Points**:
    *   **Carbon offset**: +22.4 metric tons CO2 saved.
    *   **Future Scope**: Automated barcode scanning and batch pallet evaluations.
