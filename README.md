# Reusable Packaging Network: Collecting Containers for Businesses (RePackAI)

A sustainable platform that connects businesses and collection partners to collect, track, clean, and reuse packaging containers. It helps reduce single-use plastic waste, supports circular economy practices, and enables efficient reusable-packaging management.

RePackAI is an end-to-end decision-support system designed to classify returned reusable shipping containers (Boxes, Pallets, Crates, Drums, and Totes) into optimal disposition pathways: **Resell**, **Repair**, **Refurbish**, **Recycle**, or **Dispose**. 

The system uses a hybrid recommendation engine combining deterministic business rules (safety, bio-hazard, and recycling checks), real physical math calculations (net recovery values and carbon footprint offsets), and machine learning predictions (Random Forest classification).

---

## 1. Directory Structure

```
.
├── backend/                        # FastAPI App
│   ├── app/                        # Main router, config, schemas, models
│   ├── tests/                      # Pytest suite
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                       # React TypeScript SPA
│   ├── src/                        # Component layouts, pages, API services
│   ├── Dockerfile
│   └── package.json
├── data/synthetic/                 # Synthetic dataset CSV (5,500 records)
├── models/                         # Saved joblib RandomForest model
├── scripts/                        # generate_dataset.py, train_model.py, seed_database.py
├── docs/                           # Diagrams, final reports, presentation outlines
├── docker-compose.yml              # Production Compose
├── .env.example
└── README.md
```

---

## 2. Docker Quick Deployment (Recommended)

Deploy the entire stack (FastAPI Backend + SQLite + Nginx-React Frontend) with a single command:
```bash
docker-compose up --build -d
```
*   **Frontend Dashboard**: Housed at `http://localhost:3000`
*   **Backend REST API**: Housed at `http://localhost:8000`

---

## 3. Manual Local Installation

### A. Backend Setup
1.  **Dependencies**:
    ```bash
    cd backend
    pip install -r requirements.txt
    ```
2.  **Configuration**:
    Copy environment variables:
    ```bash
    cp .env.example .env
    ```
3.  **Intake Dataset Generation**:
    Create the synthetic dataset (5,500 rows):
    ```bash
    python scripts/generate_dataset.py
    ```
4.  **Database Seeding**:
    Initialize the SQLite database (`repackai.db`) and seed master rules:
    ```bash
    python scripts/seed_database.py
    ```
5.  **Model Training**:
    Train both baseline heuristic and Random Forest classifiers:
    ```bash
    python scripts/train_model.py
    ```
6.  **Run Pytest Suite**:
    Verify calculations and rules:
    ```bash
    pytest
    ```
7.  **Start Dev Server**:
    Launch FastAPI locally:
    ```bash
    uvicorn app.main:app --reload --port 8000
    ```

### B. Frontend Setup
1.  **Dependencies**:
    ```bash
    cd frontend
    npm install
    ```
2.  **Configuration**:
    Ensure the backend host is declared:
    ```bash
    export VITE_API_URL=http://localhost:8000
    ```
3.  **Start Dev Server**:
    Launch Vite React dashboard:
    ```bash
    npm run dev
    ```
    The application will mount at `http://localhost:5173`.

4.  **Production Compilation**:
    Test production compilation and bundler packaging:
    ```bash
    npm run build
    ```

---

## 4. Verification Scenario Runs

### A. Run Benchmarks Telemetry
Logs Average and P95 latency statistics over a batch of 100 sequential requests to the recommendation engine:
```bash
python experiments/performance_benchmark.py
```

### B. Run Experiment Evaluations
Runs the baseline vs proposed evaluations and saves confusion matrices and distribution plots:
```bash
python scripts/run_experiments.py
```
Outputs:
*   Evaluation results file: `experiments/experiment_results.json`
*   Evaluation plots: `docs/figures/`
