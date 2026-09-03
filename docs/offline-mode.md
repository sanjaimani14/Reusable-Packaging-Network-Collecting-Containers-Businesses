# RePackAI — Offline Mode & Sync Design

RePackAI features a robust offline store-and-forward synchronization queue to guarantee zero data loss during network dropouts at field terminals.

## 1. Local Cache Architecture

When the inspector terminal is offline (`navigator.onLine == false` or `network_available` is toggled off):
1.  **Intercept**: The React application intercepts Container Registration and Inspection Checklist submissions.
2.  **Serialize**: Data payloads are serialized into JSON and cached locally:
    *   `localStorage.getItem('repack_offline_containers')`
    *   `localStorage.getItem('repack_offline_inspections')`
3.  **Visual Alert**: A persistent yellow status banner flashes, and the sync count indicator is updated on the navigation header.

---

## 2. Sync Reconciliation Loop

Once connectivity is restored and the operator clicks **Sync Pending**:
1.  **Replay Container Registrations**: Sends `POST /api/containers` requests sequentially. If the container already exists in the backend DB, the API handles it gracefully without throwing fatal errors.
2.  **Replay Inspections**: Sends `POST /api/inspections` requests. If successful, the records are stored in the database.
3.  **Database Reconciliation**: Calls the backend `/api/sync` queue. The backend processes the items, updates the status of the local models to `synced`, and marks the sync queue entries as `SYNCED`.
4.  **Clear Cache**: On complete replay success, the local client `localStorage` caches are wiped, and a success confirmation is displayed.

---

## 3. Duplicate Prevention Guardrails

*   **Idempotent IDs**: Containers use unique, pre-assigned IDs (e.g. barcode scanning `CON-200001`). Registering an already existing container ID returns a validation exception rather than creating duplicate entries.
*   **Inspection Timestamps**: Inspections are linked to containers and timestamped. Multiple duplicate requests submitted in error are matched against the same container ID and date, preventing duplicate processing in the database.
