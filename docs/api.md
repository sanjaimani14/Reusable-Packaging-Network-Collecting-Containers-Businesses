# RePackAI — REST API Reference

RePackAI exposes clean, versioned REST endpoints under the `/api` prefix, with `/health` endpoints exposed for service status.

## Base Endpoints

### Health check
*   **Method**: `GET`
*   **Path**: `/health` (and `/api/health`)
*   **Response**:
    ```json
    {
      "status": "healthy",
      "database": "connected",
      "timestamp": "2026-08-24T08:00:00.000000"
    }
    ```

---

## Containers API

### Register a Container
*   **Method**: `POST`
*   **Path**: `/api/containers`
*   **Request Body**:
    ```json
    {
      "id": "CON-10001",
      "container_type": "Pallet",
      "material": "Wood",
      "weight_kg": 22.5,
      "age_months": 18,
      "usage_count": 52,
      "recyclable": true
    }
    ```
*   **Response**: Returns the container object, marking status as `synced` (or `pending_sync` if registration ID starts with "OFFLINE").

### Retrieve Container
*   **Method**: `GET`
*   **Path**: `/api/containers/{id}`

---

## Inspections API

### Submit an Inspection Checklist
*   **Method**: `POST`
*   **Path**: `/api/inspections`
*   **Request Body**:
    ```json
    {
      "container_id": "CON-10001",
      "damage_level": "Medium",
      "structural_condition": "Minor Damage",
      "cleanliness_score": 85.0,
      "contamination": "None",
      "safety_risk": "Low",
      "sensor_available": true,
      "network_available": true,
      "location": "Warehouse A",
      "inspection_completeness": 1.0
    }
    ```

---

## Recommendations API

### Generate Recommender Disposition
*   **Method**: `POST`
*   **Path**: `/api/recommendations`
*   **Request Body**:
    ```json
    {
      "container_id": "CON-10001",
      "inspection_id": 1
    }
    ```
*   **Response**: Returns recommendation scores, triggered rules, and details:
    ```json
    {
      "id": 1,
      "container_id": "CON-10001",
      "inspection_id": 1,
      "recommended_action": "REPAIR",
      "confidence": 0.85,
      "score": 0.72,
      "financial_score": 0.85,
      "environmental_score": 0.70,
      "reusability_score": 0.80,
      "operational_score": 0.40,
      "rules_triggered_json": "[]",
      "explanation": "Expected Net Value: ₹30.00. Carbon Avoided: 15.20 kg.",
      "status": "PENDING",
      "requires_human_confirmation": false
    }
    ```

### Approve Recommendation
*   **Method**: `POST`
*   **Path**: `/api/recommendations/{id}/approve`
*   **Request Body**:
    ```json
    {
      "reviewer_id": 1
    }
    ```

### Override Recommendation (Human-in-the-Loop)
*   **Method**: `POST`
*   **Path**: `/api/recommendations/{id}/override`
*   **Request Body**:
    ```json
    {
      "override_action": "RECYCLE",
      "override_reason": "Metal recycling is highly prioritized today.",
      "reviewer_id": 1
    }
    ```
*   **Note**: Safety rules cannot be overridden (e.g. attempting to override an unsafe structural condition container to `RESELL` will return `HTTP 400 Bad Request`).

---

## System Configuration & Audit API

### View Active Rules
*   **Method**: `GET`
*   **Path**: `/api/rules`

### View Audit Logs
*   **Method**: `GET`
*   **Path**: `/api/audit-logs`

### View Analytics Dashboard
*   **Method**: `GET`
*   **Path**: `/api/analytics`
*   **Response**:
    ```json
    {
      "total_processed": 120,
      "total_financial_recovery": 2450.50,
      "total_waste_avoided_kg": 642.0,
      "total_carbon_saved_kg": 1520.40,
      "actions_distribution": {
        "RESELL": 80,
        "REPAIR": 25,
        "RECYCLE": 15
      },
      "override_rate": 0.0833
    }
    ```
