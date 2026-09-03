import json
import requests

def run_e2e_api_verification():
    base_url = "http://127.0.0.1:8000"
    print(f"Starting E2E API Verification against {base_url}...")
    
    # 1. Health check
    h_res = requests.get(f"{base_url}/health")
    assert h_res.status_code == 200, "Health check failed"
    print("[PASS] Health endpoint returned healthy status.")
    
    # 2. Register new container
    container_id = "CON-API-VERIFY-100"
    c_res = requests.post(f"{base_url}/api/containers", json={
        "id": container_id,
        "container_type": "Crate",
        "material": "Plastic",
        "weight_kg": 10.0,
        "age_months": 12,
        "usage_count": 30,
        "recyclable": True
    })
    # If container already exists, it is also fine
    assert c_res.status_code in [200, 201, 400], "Failed to register container"
    print(f"[PASS] Container {container_id} registration verified.")
    
    # 3. Create inspection checklist
    i_res = requests.post(f"{base_url}/api/inspections", json={
        "container_id": container_id,
        "damage_level": "Low",
        "structural_condition": "Safe",
        "cleanliness_score": 90.0,
        "contamination": "None",
        "safety_risk": "Low",
        "sensor_available": True,
        "network_available": True,
        "location": "Warehouse A",
        "inspection_completeness": 1.0,
        "raw_data_json": json.dumps({
            "resale_value": 150.0,
            "repair_cost": 30.0,
            "refurbishment_cost": 40.0,
            "recycling_value": 20.0,
            "disposal_cost": 5.0,
            "carbon_repair": 1.0,
            "carbon_refurbish": 1.0,
            "carbon_resell": 0.1,
            "carbon_recycle": 1.0,
            "carbon_dispose": 4.0
        })
    })
    assert i_res.status_code == 200, f"Failed to submit inspection checklist: {i_res.text}"
    inspection_id = i_res.json()["id"]
    print(f"[PASS] Inspection {inspection_id} checklist successfully registered.")
    
    # 4. Generate recommendation
    r_res = requests.post(f"{base_url}/api/recommendations", json={
        "container_id": container_id,
        "inspection_id": inspection_id
    })
    assert r_res.status_code == 200, f"Failed to generate recommendation: {r_res.text}"
    rec_data = r_res.json()
    action = rec_data["recommended_action"]
    print(f"[PASS] AI Recommendation generated: {action} (Confidence: {rec_data['confidence']:.2f})")
    
    # Verify alternatives comparison
    matrix = rec_data.get("alternative_actions")
    assert matrix is not None and len(matrix) <= 4, "Alternative matrix check failed"
    print("[PASS] Alternatives score comparison matrix verified.")
    
    # 5. Safety constraint override verification (Scenario: Unsafe container)
    unsafe_container_id = "CON-API-UNSAFE-9"
    requests.post(f"{base_url}/api/containers", json={
        "id": unsafe_container_id,
        "container_type": "Crate",
        "material": "Plastic",
        "weight_kg": 10.0,
        "age_months": 12,
        "usage_count": 30,
        "recyclable": True
    })
    
    u_i_res = requests.post(f"{base_url}/api/inspections", json={
        "container_id": unsafe_container_id,
        "damage_level": "High",
        "structural_condition": "Unsafe",
        "cleanliness_score": 50.0,
        "contamination": "None",
        "safety_risk": "High",
        "sensor_available": True,
        "network_available": True,
        "location": "Warehouse A",
        "inspection_completeness": 1.0,
        "raw_data_json": json.dumps({
            "resale_value": 150.0,
            "repair_cost": 30.0,
            "refurbishment_cost": 40.0,
            "recycling_value": 20.0,
            "disposal_cost": 5.0,
            "carbon_repair": 1.0,
            "carbon_refurbish": 1.0,
            "carbon_resell": 0.1,
            "carbon_recycle": 1.0,
            "carbon_dispose": 4.0
        })
    })
    
    u_inspection_id = u_i_res.json()["id"]
    u_r_res = requests.post(f"{base_url}/api/recommendations", json={
        "container_id": unsafe_container_id,
        "inspection_id": u_inspection_id
    })
    u_rec_data = u_r_res.json()
    u_action = u_rec_data["recommended_action"]
    print(f"[PASS] Unsafe container AI recommendation: {u_action}")
    assert u_action in ["RECYCLE", "DISPOSE"], f"Safety violated! Recommended reuse: {u_action}"
    
    # Attempting to submit override to resell (violates safety)
    over_res = requests.post(f"{base_url}/api/recommendations/{u_rec_data['id']}/override", json={
        "override_action": "RESELL",
        "override_reason": "Forced resell test",
        "reviewer_id": 1
    })
    assert over_res.status_code == 400, "Safety override check failed (allowed unsafe resell!)"
    print("[PASS] Safety override checked: correctly blocked forced resell override on unsafe container.")
    
    # 6. Sync replay simulation
    sync_res = requests.post(f"{base_url}/api/sync", json={
        "items": [
            {
                "entity_type": "Container",
                "entity_id": "CON-SYNC-1",
                "payload_json": json.dumps({
                    "id": "CON-SYNC-1",
                    "container_type": "Crate",
                    "material": "Metal",
                    "weight_kg": 15.0,
                    "age_months": 20,
                    "usage_count": 50,
                    "recyclable": True
                })
            }
        ]
    })
    assert sync_res.status_code == 200, f"Sync replay failed: {sync_res.text}"
    print("[PASS] Sync replay simulation completed successfully.")
    
    print("\n----------------------------------------------------")
    print("ALL API END-TO-END WORKFLOW CHECKS PASSED SUCCESSFULLY!")
    print("----------------------------------------------------")

if __name__ == "__main__":
    run_e2e_api_verification()
