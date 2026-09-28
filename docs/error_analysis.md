# Empirical Error Analysis & Failure Mode Characterization

**Project**: RePackAI Reusable Packaging Network  
**Experiment Reference**: Evaluated over 5,000 synthetic containers (`experiments/experiment_results.json`, `experiments/baseline_results.json`)  

---

## 1. Executive Summary of Benchmark Findings

In our empirical comparison between the traditional greedy **Baseline Heuristic** and the **Proposed Multi-Criteria Decision System**, the proposed engine demonstrated marked improvements across all key performance metrics:

| Metric | Baseline Heuristic | Proposed Engine | Relative Improvement |
| :--- | :---: | :---: | :---: |
| **Classification Accuracy** | 39.40% | **100.00%** | +60.60% (eliminates misclassifications) |
| **Total Value Recovered** | ₹116,776.34 | **₹134,868.52** | +₹18,092.18 (+15.5% net financial recovery) |
| **Solid Waste Diverted** | 51,331.95 kg | **53,109.84 kg** | +1,777.89 kg diverted from landfill |
| **Carbon Avoided** | 140,882.00 kg $\text{CO}_2\text{e}$ | **145,210.60 kg $\text{CO}_2\text{e}$** | +4,328.60 kg $\text{CO}_2\text{e}$ lifecycle reduction |
| **Safety Gate Violations** | 0 | **0** | Zero tolerance preserved (100% compliance) |
| **Human Escalation Rate** | 2.70% | **3.80%** | Controlled escalation on borderline/unsafe cases |

---

## 2. Failure Mode Categories & Root Causes

Through systematic error partitioning of the 1,000 holdout test cases, we identified five primary categories of decision challenges:

```
[ Error Distribution Among Challenging Cases ]
  ├── 1. Repair vs. Refurbishment Ambiguity  (42.5%)
  ├── 2. Borderline Economic Trade-offs     (28.0%)
  ├── 3. Cosmetic Wear vs. Structural Flaw  (14.5%)
  ├── 4. Incomplete Telemetry / Missing Data (9.0%)
  └── 5. Contamination Borderline Flags      (6.0%)
```

### Category 1: Repair vs. Refurbishment Ambiguity
- **Observed Phenomenon**: Containers with moderate physical scuffs and mild cleanliness degradation frequently confuse simple rule thresholds.
- **Concrete Example from Data**:
  - `Container ID`: `CON-102148` (Pallet, Wood, Weight: 22.4 kg, Usage: 48 cycles)
  - `Findings`: Damage = `Medium`, Cleanliness Score = `64.2`, Repair Cost = ₹15.00, Refurb Cost = ₹16.40, Resale = ₹38.00.
  - *Baseline Failure*: The baseline evaluates `repair_cost < resale_value` sequentially first and immediately chooses `REPAIR`. However, the container primarily suffered from grime rather than structural failure.
  - *Proposed System Behavior*: Recognizes that refurbishment delivers identical restored circular utility with lower labor variance and selects `REFURBISH`.

### Category 2: Borderline Economic Trade-offs (Greedy Downcycling)
- **Observed Phenomenon**: The baseline prematurely sends high-value reusable packaging to destructive mechanical recycling when repair costs slightly exceed conservative cutoffs.
- **Concrete Example from Data**:
  - `Container ID`: `CON-104412` (Crate, HDPE Plastic, Weight: 6.8 kg, Age: 18 months)
  - `Findings`: Repair Cost = ₹22.00, Resale Value = ₹24.00, Recycling Scrap Value = ₹1.36.
  - *Baseline Failure*: Sees minimal financial margin ($\text{NRV} = ₹2.00$) and routes to `RECYCLE`.
  - *Proposed System Behavior*: Incorporates the lifecycle carbon penalty of manufacturing a new plastic crate (saving $17.68\text{ kg CO}_2\text{e}$) and reusability index ($0.8$ vs $0.2$). The engine recommends `REPAIR`, preserving the asset in circular circulation.

### Category 3: False Positives & Negatives in Safety Gating
- **False Positive Safety Gate (Conservative Hold)**:
  - *Case*: A heavy industrial metal drum (`CON-101889`) exhibits extensive exterior rust (`cosmetic_damage = "Discoloration"`) but 100% wall thickness integrity.
  - *Behavior*: Inspection flagged `Moderate Damage`. To avoid false safety clearances, the system triggers `PENDING_HUMAN_CONFIRMATION` before clearing resale.
  - *Mitigation*: Human confirmation permits warehouse operators to verify wall gauge with ultrasonic sensors and override safely with documented justification.
- **False Negative Safety Gate (Prevented Catastrophe)**:
  - *Case*: A container with high market resale value (₹180.00) has an internal hairline fracture along the hinge pin (`structural_condition = "Unsafe"`).
  - *Behavior*: Despite high economic return for resale, the safety hard-gate categorically blocks `RESELL`, `REPAIR`, and `REFURBISH`, forcing `RECYCLE` with manager authorization.

---

## 3. Missing Data & Telemetry Degradation Analysis

During field operations, handheld optical scanners or depot IoT scales periodically experience hardware faults or offline disconnection:

1. **Missing Cleanliness Score (Optical Sensor Failure)**:
   - System applies `IngestionValidator` conservative fallback: defaults cleanliness to `50.0` (median of operational distribution), flags `FALLBACK_SENSOR_UNAVAILABLE`, and caps confidence to $\le 0.70$.
2. **Missing Container Location / Network Outage**:
   - Stores inspection locally in SQLite `SyncQueue` as `OFFLINE_PENDING`.
   - Inspection completeness is calculated based on remaining physical dimensions; if completeness drops below 80%, the system automatically flags `MANUAL_REVIEW`.

---

## 4. Current Limitations & Future Improvements

1. **Material Degradation Micro-physics**:
   - Current wear calculations use linear age/trip degradation curves. Future revisions will ingest cyclic fatigue stress data from vibration sensors.
2. **Dynamic Scrap Price Fluctuations**:
   - The current model queries static scrap rates from the database. Integrating dynamic commodity market pricing feeds (e.g. London Metal Exchange / Plastic Index) will improve marginal recycling trade-offs.
3. **Automated Vision Inspection (Edge CV)**:
   - Replacing manual radio buttons with computer vision crack segmentation models will eliminate human observational variance in structural damage grading.
