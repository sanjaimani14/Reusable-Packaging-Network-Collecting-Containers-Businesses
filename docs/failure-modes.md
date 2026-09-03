# RePackAI — Failure Modes & Fallback Foundations

This document specifies the fault tolerance and exception validation mechanisms implemented in RePackAI to handle network dropouts, sensor failures, missing checklist data, and override validation.

## 1. Network Failure & Offline Support (`network_available = False`)

*   **Behavior**: When network connectivity is lost on site, inspectors must be able to log container properties and inspection outcomes.
*   **Implementation**:
    *   Containers can be created and marked with status `pending_sync`.
    *   Inspections can be created with flag `network_available = False`.
    *   The API records these items in the database and pushes serialized payloads to the `SyncQueue` with status `PENDING`.
    *   Once connection returns, calling `POST /api/sync` runs `SyncService.sync_pending_queue(db)` to process all pending items, updates local records, and sets sync queue items to `SYNCED`.

## 2. Sensor Failure (`sensor_available = False`)

*   **Behavior**: Handheld scale or scanner sensors might fail to submit values (e.g. weight, dimensions).
*   **Implementation**:
    *   Operators are allowed to submit inspections with `sensor_available = False`.
    *   Sensors are bypassed, prompting inspectors to input weight and counts manually.
    *   Completed fields are flagged, and calculations process the manually typed properties.

## 3. Missing Data Imputations

*   **Behavior**: Incomplete inspection checklists (missing cleanliness scores, damage level classifications).
*   **Implementation**:
    *   **ML Pipeline**: Handles missing values gracefully during training and inference by using a `SimpleImputer` (using `median` strategy for numeric fields and `most_frequent` strategy for categorical fields).
    *   **Rule Engine**: Detects checklist completeness. If `inspection_completeness < 0.8` or critical values are missing, it flags the recommendation for escalation (`recommended_action = MANUAL_REVIEW` and `requires_human_confirmation = True`).

## 4. Illegal Manual Overrides

*   **Behavior**: An operator tries to manually override a recommendation to an action that violates critical safety regulations (e.g., trying to resell or repair a structurally unsafe, high-risk container).
*   **Implementation**:
    *   The `POST /api/recommendations/{id}/override` endpoint evaluates the Rule Engine against the inspection data.
    *   If the requested `override_action` is in the list of prohibited actions returned by the rule engine, the API returns a `HTTP 400 Bad Request` specifying the rule violated and blocks the override.
