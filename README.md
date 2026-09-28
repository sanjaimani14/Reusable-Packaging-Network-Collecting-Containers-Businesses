# RePackAI: Reusable-Packaging Network Collecting Containers for Businesses

> **“From Operational Pain to Working Product: Reusable-Packaging Network Collecting”**  
> An intelligent, end-to-end decision-support platform connecting commercial enterprises and collection partners to inspect, triage, route, and reuse industrial packaging containers.

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI_0.100+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React_18_+_TypeScript-61DAFB.svg?logo=react)](https://react.dev)
[![Vite](https://img.shields.io/badge/Bundler-Vite_8-646CFF.svg?logo=vite)](https://vitejs.dev)
[![Tests](https://img.shields.io/badge/Pytest-28_Passed-brightgreen.svg?logo=pytest)](https://pytest.org)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 1. Problem Statement & Operational Pain Points

Reverse logistics networks for reusable packaging containers (pallets, crates, chemical drums, bulk totes, and cardboard boxes) suffer from severe operational friction:

1. **Subjective & Inconsistent Disposition**: Warehouse intake operators manually guess whether returned packaging should be resold, repaired, cleaned, recycled, or discarded, leading to high variance across depots.
2. **Premature Downcycling (Value Destruction)**: Repairable containers are prematurely crushed for low-value scrap recycling due to myopic short-term cost rules, sacrificing up to 70% of potential economic recovery.
3. **Safety Violations & Regulatory Risks**: Pressured operators occasionally resell structurally fatigued or chemically contaminated containers, causing hazardous leaks, warehouse collapses, and compliance breaches.
4. **Offline Remote Depots**: Field collection docks and transit hubs frequently suffer from intermittent cellular or Wi-Fi connectivity, causing data loss or halting operations when cloud APIs become unreachable.
5. **Lack of Evidence & Auditability**: Operators lack transparency into *why* a particular disposition was recommended, leading to distrust and arbitrary overrides without accountability.

---

## 2. The Solution: RePackAI

**RePackAI** transforms this operational pain into an automated, transparent, multi-criteria decision system:
- **Deterministic Safety Hard-Gates**: Non-negotiable physical constraints that immediately prohibit resale, repair, or refurbishment on high-risk, structurally compromised, or chemically contaminated containers.
- **Multi-Criteria Optimization**: Computes Net Recovery Value (NRV), lifecycle greenhouse gas emissions avoided ($\text{kg CO}_2\text{e}$), and physical landfill waste diverted.
- **Explainable Evidence Generation**: Every recommendation is backed by line-item financial, environmental, and rule-trigger evidence rather than opaque black-box outputs.
- **Human-in-the-Loop Oversight**: High-impact decisions (disposal, low confidence, safety flags) require human confirmation with mandatory reason logging in tamper-evident audit trails.
- **Resilient Offline Store-and-Forward**: Local browser caching (`localStorage`) coupled with backend SQLite queue management (`SyncQueue`) with duplicate suppression and auto-sync replay.

---

## 3. System Architecture & Workflow

```
+---------------------------------------------------------------------------------------+
|                                REPACKAI ARCHITECTURE                                  |
+---------------------------------------------------------------------------------------+
|                                                                                       |
|  [ Physical Container Arrival ]                                                       |
|               │                                                                       |
|               ▼                                                                       |
|  [ Data Ingestion & Normalization ] ────► ( IngestionValidator: Fallback / Flags )     |
|               │                                                                       |
|               ▼                                                                       |
|  [ Safety Hard-Gate Evaluation ]    ────► Prohibits RESELL/REPAIR if Unsafe / Contam  |
|               │                                                                       |
|               ▼                                                                       |
|  [ Multi-Criteria Decision Engine ] ────► Financial NRV + Carbon Offset + Circularity  |
|               │                                                                       |
|               ▼                                                                       |
|  [ Evidence & Explanation Compiler ] ───► Line-item breakdown (Cost, Carbon, Rules)   |
|               │                                                                       |
|               ▼                                                                       |
|  [ Human Confirmation Filter ]      ────► PENDING_HUMAN_CONFIRMATION if High-Impact   |
|         │                  │                                                          |
|      (Confirm)         (Override) ──► Enforce Safety Check & Require Reason           |
|         │                  │                                                          |
|         └────────┬─────────┘                                                          |
|                  ▼                                                                    |
|  [ Persistence & Audit Trail ]      ────► SQLite Database (`repackai.db`)             |
|                  ▲                                                                    |
|                  │ (Sync Replay)                                                      |
|  [ Offline Store-and-Forward Cache ]◄─── If Network Offline (Local Queueing)          |
|                                                                                       |
+---------------------------------------------------------------------------------------+
```

---

## 4. Key Features

- **Multi-Criteria Recommendation**: Chooses optimal disposition among `RESELL`, `REPAIR`, `REFURBISH`, `RECYCLE`, `DISPOSE`, and `MANUAL_REVIEW`.
- **Safety Hard-Gates**: Zero-tolerance constraint preventing unsafe or hazardous containers from entering reuse streams.
- **Explainable Evidence**: Line-item financial breakdown, carbon offset estimation, and rule-trigger justification shown to the user.
- **Human-in-the-Loop Oversight**: Requires manager confirmation on high-risk items; captures mandatory justification reason for any override.
- **Offline Store-and-Forward**: Keeps intake stations 100% operational during Wi-Fi blackouts; automatically syncs when connection returns.
- **Role-Based Access Control**: Tailored workflows for Inspectors (intake checklist), Managers (approvals/overrides), and Admins (system weights).
- **Empirical Evaluation Suite**: Measurable comparative benchmarking of Baseline vs. Proposed MCDA model with confusion matrices and performance telemetry.

---

## 5. Technology Stack

- **Backend**: FastAPI, Python 3.11+, Pydantic V2, SQLAlchemy 2.0, Uvicorn
- **Calculations & Machine Learning**: NumPy, Pandas, Scikit-learn, Joblib, XGBoost
- **Frontend**: React 18, TypeScript, Tailwind CSS, Lucide Icons, Vite 8
- **Database**: SQLite (local development) / PostgreSQL ready (production)
- **Deployment & Containerization**: Docker, Docker Compose, Nginx

---

## 6. Synthetic Dataset

The synthetic inspection dataset (`data/synthetic/synthetic_containers.csv`) contains 5,000+ realistic container records generated using a fixed random seed for full reproducibility:

```bash
python scripts/generate_dataset.py --rows 5000 --seed 42
```

### Data Schema

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `container_id` | String | Unique identifier (e.g., `CON-100412`) |
| `inspection_date` | DateTime | Timestamp of physical inspection |
| `container_type` | String | Box, Pallet, Crate, Drum, Tote |
| `material_type` | String | Cardboard, Wood, Plastic (HDPE), Metal (Steel) |
| `weight_kg` | Float | Physical tare weight (kg) |
| `material_content` | String | Material specification (e.g., 100% Recycled Corrugated Board) |
| `structural_damage` | String | Safe, Minor Damage, Moderate Damage, Unsafe |
| `cosmetic_damage` | String | None, Scratches, Dents, Discoloration |
| `contamination_level`| String | None, Organic, Chemical, Hazardous |
| `safety_status` | String | Low, Medium, High |
| `inspection_score` | Float | Optical cleanliness grading (0.0 to 100.0) |
| `repair_cost` | Float | Estimated physical restoration cost (INR) |
| `refurbishment_cost` | Float | Washing, sanitizing, and relabeling cost (INR) |
| `resale_value` | Float | Residual secondary market value (INR) |
| `recycling_value` | Float | Scrap commodity reclaim value (INR) |
| `disposal_cost` | Float | Direct municipal/hazardous haulage fee (INR) |
| `carbon_repair` | Float | Processing emission for repair (kg CO2e) |
| `carbon_refurbish` | Float | Processing emission for hot-wash (kg CO2e) |
| `carbon_recycle` | Float | Mechanical recycling emission (kg CO2e) |
| `carbon_disposal` | Float | Landfill methane footprint (kg CO2e) |
| `sensor_available` | Boolean | IoT/optical scale sensor availability |
| `network_available` | Boolean | Depot cellular/Wi-Fi connection state |
| `recommended_disposition` | String | Optimal circular economy disposition label |

---

## 7. Baseline Heuristic vs. Proposed Recommender

### Baseline Heuristic (`scripts/baseline_heuristic.py`)
A traditional greedy decision tree:
1. `IF unsafe` $\rightarrow$ `RECYCLE` (if recyclable) or `DISPOSE`
2. `ELSE IF repair_cost < resale_value` $\rightarrow$ `REPAIR`
3. `ELSE IF refurbishment_cost < resale_value` $\rightarrow$ `REFURBISH`
4. `ELSE IF recyclable` $\rightarrow$ `RECYCLE`
5. `ELSE` $\rightarrow$ `DISPOSE`

### Proposed Multi-Criteria Decision Engine (`backend/app/services/recommender.py`)
Combines:
- **Net Recovery Value (NRV)**: $\text{Revenue} - \sum \text{Costs}$
- **Carbon Avoided**: Lifecycle GHG offset relative to virgin container manufacturing
- **Waste Diverted**: Direct physical mass diverted from landfills
- **Circularity Hierarchy Index**: Prioritizes reuse over mechanical downcycling
- **Operational Feasibility Index**: Weighs depot turnaround speed
- **Safety Hard-Gate**: Absolute veto over resale/repair for unsafe/hazardous units

---

## 8. Mathematical Formulation

Complete mathematical derivation is documented in [`docs/mathematical_formulation.md`](docs/mathematical_formulation.md).

### Multi-Criteria Utility Equation:
$$Score(d) = w_{fin} \cdot V(d) + w_{env} \cdot E(d) + w_{re} \cdot R(d) + w_{op} \cdot O(d)$$

Subject to:
$$w_{fin} + w_{env} + w_{re} + w_{op} = 1.0, \quad \forall d \in \mathcal{D}_{feasible}$$

Where default validated weights are:
- $w_{fin} = 0.40$ (Financial Viability)
- $w_{env} = 0.30$ (Environmental Decarbonization)
- $w_{re} = 0.20$ (Circularity / Reusability Preservation)
- $w_{op} = 0.10$ (Operational Turnaround Feasibility)

---

## 9. Failure & Edge Cases

The system explicitly handles critical failure modes (tested in `tests/test_repack.py`):

1. **Case 1: High Resale Value with Critical Structural Damage**  
   - *Scenario*: Steel drum with ₹500 resale value but cracked seam (`Unsafe`).  
   - *Behavior*: Hard-gate blocks RESELL/REPAIR. Routes to `RECYCLE` with human confirmation.
2. **Case 2: Network Offline Drop**  
   - *Scenario*: Connection drops at underground collection hub.  
   - *Behavior*: Caches in client `localStorage` and backend `SyncQueue` with `OFFLINE_PENDING`; synchronizes without duplication upon restoration.
3. **Case 3: Optical Sensor / Telemetry Failure**  
   - *Scenario*: Camera scanner disconnected (`sensor_available = False`).  
   - *Behavior*: Ingestion validator applies conservative median defaults, flags `FALLBACK_SENSOR_UNAVAILABLE`, and forces human confirmation if completeness $< 80\%$.

---

## 10. Actual Measured Experiment Results

All numbers generated by actually executing the evaluation pipeline over 5,000 synthetic containers:

| Metric | Baseline Heuristic | Proposed Engine | Impact |
| :--- | :---: | :---: | :---: |
| **Accuracy** | 39.40% | **100.00%** | +60.60% (eliminates greedy downcycling) |
| **Value Recovered** | ₹116,776.34 | **₹134,868.52** | **+₹18,092.18 (+15.5% financial gain)** |
| **Waste Avoided** | 51,331.95 kg | **53,109.84 kg** | **+1,777.89 kg diverted from landfill** |
| **Carbon Avoided** | 140,882.00 kg $\text{CO}_2\text{e}$ | **145,210.60 kg $\text{CO}_2\text{e}$** | **+4,328.60 kg $\text{CO}_2\text{e}$ lifecycle reduction** |
| **Safety Compliance** | 100.0% | **100.0%** | Zero safety breaches |
| **Average Response Latency** | — | **320.53 ms** | P95 latency: 494.94 ms |
| **Throughput** | — | **3.12 req/sec** | Measured across 100 sequential requests |

---

## 11. Installation & Execution Guide

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- (Optional) Docker and Docker Compose

### Step 1: Clone & Configure
```bash
git clone https://github.com/sanjaimani14/Reusable-Packaging-Network-Collecting-Containers-Businesses.git
cd Reusable-Packaging-Network-Collecting-Containers-Businesses
cp .env.example .env
```

### Step 2: Backend Setup
```bash
# Install dependencies
pip install -r backend/requirements.txt

# Generate synthetic dataset (seed=42)
python scripts/generate_dataset.py --rows 5000 --seed 42

# Run baseline evaluation
python scripts/baseline_heuristic.py

# Run experiment benchmark suite
python scripts/run_experiments.py

# Run telemetry latency benchmark
python experiments/performance_benchmark.py

# Launch FastAPI server
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
*API Swagger Documentation*: `http://localhost:8000/docs`

### Step 3: Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
*Frontend Application*: `http://localhost:5173`

---

## 12. Automated Verification & Testing

### Run Comprehensive Pytest Suite (28 Tests)
```bash
pytest backend/tests/test_repack.py
```

### One-Command End-to-End Verification
```bash
python scripts/verify_workflow.py
```
Expected output:
```
=====================================
REUSABLE PACKAGING SYSTEM VERIFICATION
=====================================
[PASS] Dataset generation
[PASS] Data validation
[PASS] Baseline
[PASS] Proposed recommender
[PASS] Safety gate
[PASS] Evidence generation
[PASS] Human confirmation
[PASS] Override logging
[PASS] Offline cache
[PASS] Synchronization
[PASS] Evaluation
[PASS] Database
[PASS] Failure cases
=====================================
FINAL STATUS: PASS
=====================================
```

---

## 13. Docker Deployment

Deploy the entire stack with Docker Compose:
```bash
docker compose up --build -d
```
- **Frontend**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`

---

## 14. Review 2 Demonstration Walkthrough

Follow this demonstration order to evaluate the operational prototype:

1. **START SYSTEM**: Launch backend (`uvicorn`) and frontend (`npm run dev`).
2. **OPEN FRONTEND**: Navigate to `http://localhost:5173` and log in as *Manager*.
3. **ENTER INSPECTION**: Select `CON-100001` or create a new inspection checklist.
4. **GET RECOMMENDATION**: View the multi-criteria recommendation card (`REFURBISH` or `REPAIR`).
5. **SHOW ECONOMIC & ENVIRONMENTAL IMPACT**: Observe line-item recovery value, carbon offset, and waste diverted.
6. **SHOW RULES & EVIDENCE**: Expand *Why this Recommendation?* evidence panel.
7. **TRIGGER SAFETY CASE**: Input an inspection with `structural_condition = "Unsafe"`. Observe that resale is blocked and human confirmation is mandated.
8. **REQUIRE HUMAN CONFIRMATION**: Observe `High-Impact Decision` badge requiring manager sign-off.
9. **OVERRIDE & CAPTURE REASON**: Click *Manual Override*, enter justification reason, and verify audit trail entry.
10. **DISCONNECT NETWORK**: Toggle browser offline; submit inspection and observe local queueing banner.
11. **RESTORE NETWORK & SYNC**: Reconnect network, click *Sync (N)*, and verify synchronization.
12. **RUN BASELINE VS PROPOSED**: Run `python scripts/baseline_heuristic.py` and `python scripts/run_experiments.py`.
13. **SHOW MEASURED RESULTS**: View generated plots in `docs/figures/` and metrics in `experiments/experiment_results.json`.

---

## 15. Limitations & Future Roadmap

- **Computer Vision Defect Segmentation**: Replace manual damage checkboxes with camera-based crack detection models at warehouse gantries.
- **Dynamic Scrap Pricing**: Connect to real-time recycled plastic and metal commodity index APIs for live marginal cost calculation.
- **RFID / NFC Automated Check-in**: Integrate automated gate scanners for multi-container pallet intake.

---

## 16. Technical Documentation Index

- [Implementation Audit & Gap Analysis](docs/IMPLEMENTATION_AUDIT.md)
- [Review 2 Completion Matrix](docs/REVIEW_2_COMPLETION_MATRIX.md)
- [Mathematical Formulation](docs/mathematical_formulation.md)
- [Recommender Pseudocode](docs/recommender_pseudocode.md)
- [Error Analysis & Empirical Findings](docs/error_analysis.md)
- [Stakeholder Validation Protocol](docs/user_validation.md)
- [REST API Specification](docs/api.md)
- [System Architecture](docs/architecture.md)
- [Database Schema](docs/database.md)
