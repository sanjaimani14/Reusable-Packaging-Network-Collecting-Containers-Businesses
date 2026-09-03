import os
import pytest
import json
import pandas as pd
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from repackai.backend.app.main import app
from repackai.backend.app.database import Base, get_db
from repackai.backend.app.models import domain
from repackai.backend.app.rules.engine import RuleEngine
from repackai.backend.app.calculations.financial import FinancialCalculator
from repackai.backend.app.calculations.environmental import EnvironmentalCalculator
from repackai.backend.app.services.recommender import RecommendationEngine
from repackai.backend.app.services.ml_service import MLService

# Setup separate test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_repack.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        # Seed test rules
        materials = [
            domain.MaterialRule(
                material_name="Cardboard", recyclable=True, processing_cost_per_kg=0.02,
                recycling_value_per_kg=0.08, carbon_recycle_per_kg=0.4, carbon_dispose_per_kg=1.2
            ),
            domain.MaterialRule(
                material_name="Wood", recyclable=True, processing_cost_per_kg=0.01,
                recycling_value_per_kg=0.03, carbon_recycle_per_kg=0.1, carbon_dispose_per_kg=0.5
            ),
            domain.MaterialRule(
                material_name="Plastic", recyclable=True, processing_cost_per_kg=0.05,
                recycling_value_per_kg=0.20, carbon_recycle_per_kg=1.0, carbon_dispose_per_kg=3.1
            ),
            domain.MaterialRule(
                material_name="Metal", recyclable=True, processing_cost_per_kg=0.10,
                recycling_value_per_kg=0.50, carbon_recycle_per_kg=2.2, carbon_dispose_per_kg=6.6
            )
        ]
        db.add_all(materials)
        
        disposals = [
            domain.DisposalRule(contamination_type="None", disposal_cost_multiplier=1.0, is_hazardous=False, requires_special_handling=False),
            domain.DisposalRule(contamination_type="Organic", disposal_cost_multiplier=1.5, is_hazardous=False, requires_special_handling=False),
            domain.DisposalRule(contamination_type="Chemical", disposal_cost_multiplier=2.5, is_hazardous=True, requires_special_handling=True),
            domain.DisposalRule(contamination_type="Hazardous", disposal_cost_multiplier=6.0, is_hazardous=True, requires_special_handling=True)
        ]
        db.add_all(disposals)
        db.commit()
    finally:
        db.close()
        
    yield
    # Clean up test DB file at end of session
    if os.path.exists("test_repack.db"):
        try:
            os.remove("test_repack.db")
        except Exception:
            pass

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

# 1. Dataset validation
def test_dataset_exists_and_valid():
    csv_path = "data/synthetic/synthetic_containers.csv"
    assert os.path.exists(csv_path), "Synthetic dataset does not exist."
    df = pd.read_csv(csv_path)
    assert len(df) >= 5000, "Dataset contains fewer than 5000 rows."
    required_cols = ["container_id", "container_type", "material", "weight_kg", "damage_level", "final_disposition"]
    for col in required_cols:
        assert col in df.columns, f"Column {col} missing in dataset."

# 2. Rule Engine: Unsafe structural condition
def test_rule_engine_unsafe_structural_condition():
    inspection = {"structural_condition": "Unsafe", "safety_risk": "Low", "contamination": "None", "inspection_completeness": 1.0}
    container = {"recyclable": True}
    res = RuleEngine.evaluate(inspection, container)
    prohibited = RuleEngine.get_prohibited_actions(res)
    assert "RESELL" in prohibited
    assert "REPAIR" in prohibited
    assert "REFURBISH" in prohibited

# 3. Rule Engine: Hazardous contamination
def test_rule_engine_hazardous_contamination():
    inspection = {"structural_condition": "Safe", "safety_risk": "Low", "contamination": "Hazardous", "inspection_completeness": 1.0}
    container = {"recyclable": True}
    res = RuleEngine.evaluate(inspection, container)
    prohibited = RuleEngine.get_prohibited_actions(res)
    assert "RECYCLE" in prohibited
    assert "RESELL" in prohibited
    assert "REPAIR" in prohibited
    assert "REFURBISH" in prohibited

# 4. Rule Engine: Non-recyclable material
def test_rule_engine_recyclable_false():
    inspection = {"structural_condition": "Safe", "safety_risk": "Low", "contamination": "None", "inspection_completeness": 1.0}
    container = {"recyclable": False}
    res = RuleEngine.evaluate(inspection, container)
    prohibited = RuleEngine.get_prohibited_actions(res)
    assert "RECYCLE" in prohibited
    assert "RESELL" not in prohibited

# 5. Rule Engine: Incomplete inspection
def test_rule_engine_completeness():
    inspection = {"structural_condition": "Safe", "safety_risk": "Low", "contamination": "None", "inspection_completeness": 0.7}
    container = {"recyclable": True}
    res = RuleEngine.evaluate(inspection, container)
    triggered_names = [r.rule_name for r in res if r.is_triggered]
    assert "Completeness Constraint" in triggered_names
    assert RuleEngine.requires_human_confirmation(inspection, res, "RESELL") is True

# 6. Financial Calculations
def test_financial_calc():
    container = {"material": "Plastic", "weight_kg": 10.0}
    inspection = {"resale_value": 100.0, "repair_cost": 20.0, "refurbishment_cost": 40.0, "recycling_value": 15.0, "disposal_cost": 8.0}
    
    # Custom material rule processing cost per kg is 0.05, so recycle cost is 10.0 * 0.05 = 0.5
    f_res = FinancialCalculator.calculate(container, inspection)
    assert f_res["RESELL"]["net_value"] == 100.0
    assert f_res["REPAIR"]["net_value"] == 80.0
    assert f_res["REFURBISH"]["net_value"] == 60.0
    assert f_res["RECYCLE"]["net_value"] == 14.5
    assert f_res["DISPOSE"]["net_value"] == -8.0

# 7. Environmental Calculations
def test_environmental_calc():
    container = {"material": "Plastic", "weight_kg": 10.0}
    inspection = {"carbon_repair": 2.0, "carbon_refurbish": 4.0, "carbon_recycle": 10.0, "carbon_dispose": 30.0, "carbon_resell": 0.2}
    
    # Plastic base carbon is 2.6, so new container carbon is 10.0 * 2.6 = 26.0
    e_res = EnvironmentalCalculator.calculate(container, inspection)
    assert e_res["RESELL"]["waste_avoided_kg"] == 10.0
    assert e_res["RECYCLE"]["waste_avoided_kg"] == 8.0
    assert e_res["DISPOSE"]["waste_avoided_kg"] == 0.0
    
    assert e_res["RESELL"]["carbon_avoided_kg"] == 25.8
    assert e_res["REPAIR"]["carbon_avoided_kg"] == 24.0

# 8. Recommendation Engine Scoring
def test_recommendation_scoring():
    container = {"material": "Plastic", "weight_kg": 10.0, "recyclable": True}
    inspection = {
        "resale_value": 100.0, "repair_cost": 10.0, "refurbishment_cost": 40.0, "recycling_value": 15.0, "disposal_cost": 10.0,
        "structural_condition": "Safe", "safety_risk": "Low", "contamination": "None", "inspection_completeness": 1.0,
        "carbon_repair": 1.0, "carbon_refurbish": 2.0, "carbon_recycle": 3.0, "carbon_dispose": 5.0, "carbon_resell": 0.1
    }
    
    rec = RecommendationEngine.generate_recommendation(container, inspection)
    # The high net value of Resell and low costs should recommend RESELL or REPAIR
    assert rec["recommended_action"] in ["RESELL", "REPAIR"]
    assert rec["requires_human_confirmation"] is False

# 9. Recommendation Engine: Safety constraint overrides
def test_recommendation_safety_override():
    container = {"material": "Plastic", "weight_kg": 10.0, "recyclable": True}
    inspection = {
        "resale_value": 100.0, "repair_cost": 10.0, "refurbishment_cost": 40.0, "recycling_value": 15.0, "disposal_cost": 10.0,
        "structural_condition": "Unsafe", "safety_risk": "High", "contamination": "None", "inspection_completeness": 1.0,
        "carbon_repair": 1.0, "carbon_refurbish": 2.0, "carbon_recycle": 3.0, "carbon_dispose": 5.0, "carbon_resell": 0.1
    }
    
    rec = RecommendationEngine.generate_recommendation(container, inspection)
    # Unsafe structural condition prohibits resale, repair, refurbishment
    # Recommended must fall back to RECYCLE since it is recyclable
    assert rec["recommended_action"] == "RECYCLE"
    assert rec["requires_human_confirmation"] is True  # due to high safety risk/critical rules

# 10. Missing Data Handling
def test_missing_data_handling():
    # If structural condition or damage is missing, it should handle fallback gracefully and not crash
    container = {"material": "Plastic", "weight_kg": 10.0, "recyclable": True}
    inspection = {
        "resale_value": 100.0, "repair_cost": 10.0,
        "structural_condition": None, "safety_risk": None, "contamination": None, "inspection_completeness": 0.9
    }
    rec = RecommendationEngine.generate_recommendation(container, inspection)
    assert rec["recommended_action"] is not None

# 11. ML Service Heuristic Fallback
def test_ml_service_fallback():
    # If model is unavailable (or fake container data is passed), it should fall back to baseline heuristics
    cls_pred, conf = MLService.predict({"recyclable": True}, {"damage_level": "None"})
    assert cls_pred.lower() == "resell"
    assert 0.0 <= conf <= 1.0

# 12. API: Health Check
def test_api_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

# 13. API: Create Container
def test_api_create_container():
    payload = {
        "id": "CON-TEST-123",
        "container_type": "Tote",
        "material": "Plastic",
        "weight_kg": 8.5,
        "age_months": 6,
        "usage_count": 12,
        "recyclable": True
    }
    res = client.post("/api/containers", json=payload)
    assert res.status_code == 200
    assert res.json()["id"] == "CON-TEST-123"

# 14. API: Create Inspection
def test_api_create_inspection():
    payload = {
        "container_id": "CON-TEST-123",
        "damage_level": "Low",
        "structural_condition": "Safe",
        "cleanliness_score": 92.5,
        "contamination": "None",
        "safety_risk": "Low",
        "sensor_available": True,
        "network_available": True,
        "location_available": True,
        "location": "Warehouse A",
        "inspection_completeness": 1.0
    }
    res = client.post("/api/inspections", json=payload)
    assert res.status_code == 200
    assert res.json()["container_id"] == "CON-TEST-123"
    assert res.json()["id"] is not None

# 15. API: Recommendation Generation
def test_api_recommendation():
    # Create Container
    client.post("/api/containers", json={
        "id": "CON-REC-1", "container_type": "Crate", "material": "Plastic", "weight_kg": 15.0, "age_months": 12, "usage_count": 50, "recyclable": True
    })
    # Create Inspection
    insp_res = client.post("/api/inspections", json={
        "container_id": "CON-REC-1", "damage_level": "Medium", "structural_condition": "Minor Damage", "cleanliness_score": 80.0,
        "contamination": "None", "safety_risk": "Low", "sensor_available": True, "network_available": True, "location": "Warehouse A", "inspection_completeness": 1.0,
        "raw_data_json": json.dumps({"resale_value": 50.0, "repair_cost": 15.0, "refurbishment_cost": 25.0, "recycling_value": 3.0, "disposal_cost": 5.0})
    })
    insp_id = insp_res.json()["id"]
    
    # Generate recommendation
    res = client.post("/api/recommendations", json={
        "container_id": "CON-REC-1",
        "inspection_id": insp_id
    })
    assert res.status_code == 200
    assert res.json()["recommended_action"] in ["RESELL", "REPAIR", "REFURBISH", "RECYCLE", "DISPOSE"]
    assert "evidence" in res.json()

# 16. API: Approve Recommendation
def test_api_approve():
    client.post("/api/containers", json={
        "id": "CON-REC-2", "container_type": "Box", "material": "Cardboard", "weight_kg": 2.0, "age_months": 2, "usage_count": 4, "recyclable": True
    })
    insp_res = client.post("/api/inspections", json={
        "container_id": "CON-REC-2", "damage_level": "None", "structural_condition": "Safe", "cleanliness_score": 99.0,
        "contamination": "None", "safety_risk": "Low", "sensor_available": True, "network_available": True, "location": "Warehouse A", "inspection_completeness": 1.0
    })
    insp_id = insp_res.json()["id"]
    
    rec_res = client.post("/api/recommendations", json={"container_id": "CON-REC-2", "inspection_id": insp_id})
    rec_id = rec_res.json()["id"]
    
    # Approve
    app_res = client.post(f"/api/recommendations/{rec_id}/approve", json={"reviewer_id": 1})
    assert app_res.status_code == 200
    assert app_res.json()["status"] == "APPROVED"

# 17. API: Override validation
def test_api_override_success_and_fail():
    client.post("/api/containers", json={
        "id": "CON-REC-3", "container_type": "Drum", "material": "Metal", "weight_kg": 40.0, "age_months": 24, "usage_count": 80, "recyclable": True
    })
    # Unsafe container inspection
    insp_res = client.post("/api/inspections", json={
        "container_id": "CON-REC-3", "damage_level": "Critical", "structural_condition": "Unsafe", "cleanliness_score": 50.0,
        "contamination": "None", "safety_risk": "High", "sensor_available": True, "network_available": True, "location": "Warehouse A", "inspection_completeness": 1.0
    })
    insp_id = insp_res.json()["id"]
    
    rec_res = client.post("/api/recommendations", json={"container_id": "CON-REC-3", "inspection_id": insp_id})
    rec_id = rec_res.json()["id"]
    
    # Override to RESELL should fail since RESELL is prohibited for Unsafe structural condition
    override_fail = client.post(f"/api/recommendations/{rec_id}/override", json={
        "override_action": "RESELL",
        "override_reason": "Testing invalid safety override",
        "reviewer_id": 1
    })
    assert override_fail.status_code == 400
    assert "Safety rule violation" in override_fail.json()["detail"]
    
    # Override to RECYCLE should succeed (since it is recyclable and not prohibited)
    override_success = client.post(f"/api/recommendations/{rec_id}/override", json={
        "override_action": "RECYCLE",
        "override_reason": "Custom override to recycle for metal",
        "reviewer_id": 1
    })
    assert override_success.status_code == 200
    assert override_success.json()["status"] == "OVERRIDDEN"

# 18. Offline Fallback
def test_offline_fallback():
    # Container with OFFLINE prefix triggers pending_sync
    container_payload = {
        "id": "OFFLINE-CON-999",
        "container_type": "Tote",
        "material": "Plastic",
        "weight_kg": 5.0,
        "age_months": 3,
        "usage_count": 5,
        "recyclable": True
    }
    res = client.post("/api/containers", json=container_payload)
    assert res.json()["status"] == "pending_sync"
    
    # Check sync endpoint
    sync_res = client.post("/api/sync")
    assert sync_res.status_code == 200
    assert sync_res.json()["synced_count"] >= 1
    
    # Container status is updated to synced
    container_res = client.get("/api/containers/OFFLINE-CON-999")
    assert container_res.json()["status"] == "synced"
