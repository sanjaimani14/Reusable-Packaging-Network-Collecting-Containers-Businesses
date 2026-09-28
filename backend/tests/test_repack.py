import os
import sys
import json
import pytest
import pandas as pd
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup sys.path for repo root
current_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

try:
    from backend.app.main import app
    from backend.app.database import Base, get_db
    from backend.app.models import domain
    from backend.app.recommender_rules.engine import RuleEngine
    from backend.app.calculations.financial import FinancialCalculator
    from backend.app.calculations.environmental import EnvironmentalCalculator
    from backend.app.services.recommender import RecommendationEngine
    from backend.app.services.ml_service import MLService
    from backend.app.ingestion.validator import IngestionValidator
    from backend.app.offline_cache.cache_manager import OfflineCacheManager
    from scripts.baseline_heuristic import run_baseline_heuristic
    from scripts.generate_dataset import generate_synthetic_data
except ImportError:
    from repackai.backend.app.main import app
    from repackai.backend.app.database import Base, get_db
    from repackai.backend.app.models import domain
    from repackai.backend.app.recommender_rules.engine import RuleEngine
    from repackai.backend.app.calculations.financial import FinancialCalculator
    from repackai.backend.app.calculations.environmental import EnvironmentalCalculator
    from repackai.backend.app.services.recommender import RecommendationEngine
    from repackai.backend.app.services.ml_service import MLService
    from repackai.backend.app.ingestion.validator import IngestionValidator
    from repackai.backend.app.offline_cache.cache_manager import OfflineCacheManager
    from repackai.scripts.baseline_heuristic import run_baseline_heuristic
    from repackai.scripts.generate_dataset import generate_synthetic_data

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

# 1. Dataset existence & validation
def test_dataset_exists_and_valid():
    csv_path = "data/synthetic/synthetic_containers.csv"
    if not os.path.exists(csv_path):
        csv_path = "repackai/data/synthetic/synthetic_containers.csv"
    assert os.path.exists(csv_path), "Synthetic dataset does not exist."
    df = pd.read_csv(csv_path)
    assert len(df) >= 5000, "Dataset contains fewer than 5000 rows."
    required_cols = ["container_id", "material_type", "container_type", "structural_damage", "recommended_disposition"]
    for col in required_cols:
        assert col in df.columns, f"Column {col} missing in dataset."

# 2. Dataset generator script reproducibility
def test_dataset_generation_script(tmp_path):
    out_file = str(tmp_path / "test_synth.csv")
    df = generate_synthetic_data(num_records=50, output_path=out_file, seed=123)
    assert os.path.exists(out_file)
    assert len(df) == 50
    assert "inspection_date" in df.columns
    assert "material_content" in df.columns

# 3. Ingestion Validator: Container validation
def test_ingestion_validator_container():
    valid, err, cleaned = IngestionValidator.validate_container({
        "id": "CON-VAL-1", "container_type": "Tote", "material": "Plastic", "weight_kg": 5.0
    })
    assert valid is True
    assert err is None
    
    # Invalid container (weight <= 0)
    valid_inv, err_inv, _ = IngestionValidator.validate_container({
        "id": "CON-VAL-2", "container_type": "Tote", "material": "Plastic", "weight_kg": -1.0
    })
    assert valid_inv is False
    assert "greater than zero" in err_inv

# 4. Ingestion Validator: Inspection validation & Fallback handling
def test_ingestion_validator_inspection_fallbacks():
    # Sensor and location unavailable
    valid, err, cleaned = IngestionValidator.validate_and_normalize_inspection({
        "container_id": "CON-VAL-1",
        "sensor_available": False,
        "location_available": False,
        "cleanliness_score": None,
        "damage_level": None,
        "location": None
    })
    assert valid is True
    assert "FALLBACK_SENSOR_UNAVAILABLE" in cleaned["ingestion_flags"]
    assert "FALLBACK_LOCATION_DEFAULTED" in cleaned["ingestion_flags"]
    assert cleaned["cleanliness_score"] == 50.0  # conservative median fallback
    assert cleaned["damage_level"] == "Medium"
    assert cleaned["location"] == "Facility_Fallback_Dock"

# 5. Rule Engine: Unsafe structural condition
def test_rule_engine_unsafe_structural_condition():
    inspection = {"structural_condition": "Unsafe", "safety_risk": "Low", "contamination": "None", "inspection_completeness": 1.0}
    container = {"recyclable": True}
    res = RuleEngine.evaluate(inspection, container)
    prohibited = RuleEngine.get_prohibited_actions(res)
    assert "RESELL" in prohibited
    assert "REPAIR" in prohibited
    assert "REFURBISH" in prohibited

# 6. Rule Engine: Hazardous contamination
def test_rule_engine_hazardous_contamination():
    inspection = {"structural_condition": "Safe", "safety_risk": "Low", "contamination": "Hazardous", "inspection_completeness": 1.0}
    container = {"recyclable": True}
    res = RuleEngine.evaluate(inspection, container)
    prohibited = RuleEngine.get_prohibited_actions(res)
    assert "RECYCLE" in prohibited
    assert "RESELL" in prohibited
    assert "REPAIR" in prohibited
    assert "REFURBISH" in prohibited

# 7. Rule Engine: Non-recyclable material
def test_rule_engine_recyclable_false():
    inspection = {"structural_condition": "Safe", "safety_risk": "Low", "contamination": "None", "inspection_completeness": 1.0}
    container = {"recyclable": False}
    res = RuleEngine.evaluate(inspection, container)
    prohibited = RuleEngine.get_prohibited_actions(res)
    assert "RECYCLE" in prohibited
    assert "RESELL" not in prohibited

# 8. Rule Engine: Incomplete inspection triggers escalation
def test_rule_engine_completeness():
    inspection = {"structural_condition": "Safe", "safety_risk": "Low", "contamination": "None", "inspection_completeness": 0.7}
    container = {"recyclable": True}
    res = RuleEngine.evaluate(inspection, container)
    triggered_names = [r.rule_name for r in res if r.is_triggered]
    assert "Completeness Constraint" in triggered_names
    assert RuleEngine.requires_human_confirmation(inspection, res, "RESELL") is True

# 9. Financial Calculations
def test_financial_calc():
    container = {"material": "Plastic", "weight_kg": 10.0}
    inspection = {"resale_value": 100.0, "repair_cost": 20.0, "refurbishment_cost": 40.0, "recycling_value": 15.0, "disposal_cost": 8.0}
    f_res = FinancialCalculator.calculate(container, inspection)
    assert f_res["RESELL"]["net_value"] == 100.0
    assert f_res["REPAIR"]["net_value"] == 80.0
    assert f_res["REFURBISH"]["net_value"] == 60.0
    assert f_res["RECYCLE"]["net_value"] == 14.5
    assert f_res["DISPOSE"]["net_value"] == -8.0

# 10. Environmental Calculations
def test_environmental_calc():
    container = {"material": "Plastic", "weight_kg": 10.0}
    inspection = {"carbon_repair": 2.0, "carbon_refurbish": 4.0, "carbon_recycle": 10.0, "carbon_dispose": 30.0, "carbon_resell": 0.2}
    e_res = EnvironmentalCalculator.calculate(container, inspection)
    assert e_res["RESELL"]["waste_avoided_kg"] == 10.0
    assert e_res["RECYCLE"]["waste_avoided_kg"] == 8.0
    assert e_res["DISPOSE"]["waste_avoided_kg"] == 0.0
    assert e_res["RESELL"]["carbon_avoided_kg"] == 25.8
    assert e_res["REPAIR"]["carbon_avoided_kg"] == 24.0

# 11. Recommendation Engine Scoring
def test_recommendation_scoring():
    container = {"material": "Plastic", "weight_kg": 10.0, "recyclable": True}
    inspection = {
        "resale_value": 100.0, "repair_cost": 10.0, "refurbishment_cost": 40.0, "recycling_value": 15.0, "disposal_cost": 10.0,
        "structural_condition": "Safe", "safety_risk": "Low", "contamination": "None", "inspection_completeness": 1.0,
        "carbon_repair": 1.0, "carbon_refurbish": 2.0, "carbon_recycle": 3.0, "carbon_dispose": 5.0, "carbon_resell": 0.1
    }
    rec = RecommendationEngine.generate_recommendation(container, inspection)
    assert rec["recommended_action"] in ["RESELL", "REPAIR"]
    assert rec["requires_human_confirmation"] is False

# 12. Recommendation Engine: Safety constraint overrides high economic value
def test_recommendation_safety_override():
    container = {"material": "Plastic", "weight_kg": 10.0, "recyclable": True}
    inspection = {
        "resale_value": 100.0, "repair_cost": 10.0, "refurbishment_cost": 40.0, "recycling_value": 15.0, "disposal_cost": 10.0,
        "structural_condition": "Unsafe", "safety_risk": "High", "contamination": "None", "inspection_completeness": 1.0,
        "carbon_repair": 1.0, "carbon_refurbish": 2.0, "carbon_recycle": 3.0, "carbon_dispose": 5.0, "carbon_resell": 0.1
    }
    rec = RecommendationEngine.generate_recommendation(container, inspection)
    assert rec["recommended_action"] == "RECYCLE"
    assert rec["requires_human_confirmation"] is True

# 13. Missing Data Handling
def test_missing_data_handling():
    container = {"material": "Plastic", "weight_kg": 10.0, "recyclable": True}
    inspection = {
        "resale_value": 100.0, "repair_cost": 10.0,
        "structural_condition": None, "safety_risk": None, "contamination": None, "inspection_completeness": 0.9
    }
    rec = RecommendationEngine.generate_recommendation(container, inspection)
    assert rec["recommended_action"] is not None

# 14. ML Service Heuristic Fallback
def test_ml_service_fallback():
    cls_pred, conf = MLService.predict({"recyclable": True}, {"damage_level": "None"})
    assert cls_pred.lower() == "resell"
    assert 0.0 <= conf <= 1.0

# 15. Baseline Heuristic Script Execution
def test_baseline_heuristic_execution(tmp_path):
    out_file = str(tmp_path / "baseline_out.json")
    csv_path = "data/synthetic/synthetic_containers.csv"
    if not os.path.exists(csv_path):
        csv_path = "repackai/data/synthetic/synthetic_containers.csv"
    res = run_baseline_heuristic(data_path=csv_path, output_path=out_file)
    assert res["total_containers_evaluated"] >= 5000
    assert "value_recovered" in res
    assert "safety_compliance" in res
    assert os.path.exists(out_file)

# 16. Offline Cache Manager: Network unavailable -> Enqueue pending
def test_offline_cache_manager_network_unavailable():
    db = TestingSessionLocal()
    try:
        OfflineCacheManager.set_network_state(False)
        assert OfflineCacheManager.is_network_online() is False
        
        item = OfflineCacheManager.enqueue(db, "Container", "CON-OFFLINE-TEST-1", {"weight_kg": 10.0})
        assert item.status == "PENDING"
        
        sync_res = OfflineCacheManager.sync_all(db)
        assert sync_res["status"] == "OFFLINE_PENDING"
        assert sync_res["synced_count"] == 0
    finally:
        OfflineCacheManager.set_network_state(True)
        db.close()

# 17. Offline Cache Manager: Network restored -> Sync all
def test_offline_cache_manager_network_restored():
    db = TestingSessionLocal()
    try:
        OfflineCacheManager.set_network_state(True)
        item = OfflineCacheManager.enqueue(db, "Container", "CON-OFFLINE-SYNC-1", {"weight_kg": 10.0, "material": "Plastic"})
        assert item.status == "PENDING"
        
        sync_res = OfflineCacheManager.sync_all(db)
        assert sync_res["status"] == "SYNC_COMPLETE"
        assert sync_res["synced_count"] >= 1
    finally:
        db.close()

# 18. Offline Cache Manager: Duplicate suppression
def test_offline_cache_manager_duplicate_suppression():
    db = TestingSessionLocal()
    try:
        # Enqueue same item twice
        item1 = OfflineCacheManager.enqueue(db, "Container", "CON-DUP-1", {"weight_kg": 10.0})
        item2 = OfflineCacheManager.enqueue(db, "Container", "CON-DUP-1", {"weight_kg": 12.0})
        # Should update existing record rather than creating duplicate
        assert item1.id == item2.id
        pending_items = [i for i in OfflineCacheManager.get_pending_items(db) if i.entity_id == "CON-DUP-1"]
        assert len(pending_items) == 1
    finally:
        db.close()

# 19. Failure Case 1: High Resale Value + Critical Structural Damage
def test_failure_case_1_high_resale_critical_damage():
    container = {"material": "Metal", "weight_kg": 25.0, "recyclable": True}
    inspection = {
        "resale_value": 500.0,  # Very high tempting economic value
        "repair_cost": 20.0,
        "refurbishment_cost": 30.0,
        "recycling_value": 12.5,
        "disposal_cost": 15.0,
        "structural_condition": "Unsafe",  # Critical safety flaw
        "safety_risk": "High",
        "contamination": "None",
        "inspection_completeness": 1.0,
        "carbon_repair": 2.0, "carbon_refurbish": 3.0, "carbon_recycle": 5.0, "carbon_dispose": 15.0, "carbon_resell": 0.2
    }
    rec = RecommendationEngine.generate_recommendation(container, inspection)
    # HARD GATE: Even with ₹500 resale and low repair, safety blocks RESELL and REPAIR
    assert rec["recommended_action"] in ["RECYCLE", "DISPOSE"]
    assert rec["recommended_action"] not in ["RESELL", "REPAIR", "REFURBISH"]
    assert rec["requires_human_confirmation"] is True

# 20. Failure Case 2: Network Unavailable Store-and-Forward
def test_failure_case_2_network_unavailable():
    client.post("/api/containers", json={
        "id": "CON-FAIL-NET", "container_type": "Tote", "material": "Plastic", "weight_kg": 8.0, "age_months": 2, "usage_count": 5, "recyclable": True
    })
    insp_res = client.post("/api/inspections", json={
        "container_id": "CON-FAIL-NET",
        "damage_level": "None", "structural_condition": "Safe", "cleanliness_score": 95.0,
        "contamination": "None", "safety_risk": "Low",
        "network_available": False,  # Network is down
        "location": "Remote Dock 4"
    })
    assert insp_res.status_code == 200
    db = TestingSessionLocal()
    try:
        pending = OfflineCacheManager.get_pending_items(db)
        queued_ids = [p.entity_id for p in pending]
        assert str(insp_res.json()["id"]) in queued_ids
    finally:
        db.close()

# 21. Failure Case 3: Missing Sensor Data Fallback
def test_failure_case_3_sensor_unavailable_fallback():
    client.post("/api/containers", json={
        "id": "CON-FAIL-SENSOR", "container_type": "Box", "material": "Cardboard", "weight_kg": 2.0, "age_months": 1, "usage_count": 2, "recyclable": True
    })
    insp_res = client.post("/api/inspections", json={
        "container_id": "CON-FAIL-SENSOR",
        "sensor_available": False,  # Sensor failed
        "location_available": False,  # Location sensor failed
        "cleanliness_score": None,  # Missing sensor telemetry
        "damage_level": None
    })
    assert insp_res.status_code == 200
    # Ingestion validator should set conservative fallbacks and not crash
    data = insp_res.json()
    assert data["cleanliness_score"] == 50.0
    assert data["damage_level"] == "Medium"
    assert data["location"] == "Facility_Fallback_Dock"

# 22. API: Health Check
def test_api_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

# 23. API: Create Container
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

# 24. API: Create Inspection
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

# 25. API: Recommendation Generation & Evidence
def test_api_recommendation():
    client.post("/api/containers", json={
        "id": "CON-REC-1", "container_type": "Crate", "material": "Plastic", "weight_kg": 15.0, "age_months": 12, "usage_count": 50, "recyclable": True
    })
    insp_res = client.post("/api/inspections", json={
        "container_id": "CON-REC-1", "damage_level": "Medium", "structural_condition": "Minor Damage", "cleanliness_score": 80.0,
        "contamination": "None", "safety_risk": "Low", "sensor_available": True, "network_available": True, "location": "Warehouse A", "inspection_completeness": 1.0,
        "raw_data_json": json.dumps({"resale_value": 50.0, "repair_cost": 15.0, "refurbishment_cost": 25.0, "recycling_value": 3.0, "disposal_cost": 5.0})
    })
    insp_id = insp_res.json()["id"]
    
    res = client.post("/api/recommendations", json={
        "container_id": "CON-REC-1",
        "inspection_id": insp_id
    })
    assert res.status_code == 200
    rec_data = res.json()
    assert rec_data["recommended_action"] in ["RESELL", "REPAIR", "REFURBISH", "RECYCLE", "DISPOSE"]
    assert "evidence" in rec_data
    assert "financial_breakdown" in rec_data["evidence"]
    assert "environmental_breakdown" in rec_data["evidence"]

# 26. API: Approve Recommendation
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
    
    app_res = client.post(f"/api/recommendations/{rec_id}/approve", json={"reviewer_id": 1})
    assert app_res.status_code == 200
    assert app_res.json()["status"] == "APPROVED"

# 27. API: Override validation with safety blocking and reason capture
def test_api_override_success_and_fail():
    client.post("/api/containers", json={
        "id": "CON-REC-3", "container_type": "Drum", "material": "Metal", "weight_kg": 40.0, "age_months": 24, "usage_count": 80, "recyclable": True
    })
    insp_res = client.post("/api/inspections", json={
        "container_id": "CON-REC-3", "damage_level": "Critical", "structural_condition": "Unsafe", "cleanliness_score": 50.0,
        "contamination": "None", "safety_risk": "High", "sensor_available": True, "network_available": True, "location": "Warehouse A", "inspection_completeness": 1.0
    })
    insp_id = insp_res.json()["id"]
    
    rec_res = client.post("/api/recommendations", json={"container_id": "CON-REC-3", "inspection_id": insp_id})
    rec_id = rec_res.json()["id"]
    
    # Override to RESELL should fail (Safety rule violation)
    override_fail = client.post(f"/api/recommendations/{rec_id}/override", json={
        "override_action": "RESELL",
        "override_reason": "Testing invalid safety override",
        "reviewer_id": 1
    })
    assert override_fail.status_code == 400
    assert "Safety rule violation" in override_fail.json()["detail"]
    
    # Override to RECYCLE should succeed
    override_success = client.post(f"/api/recommendations/{rec_id}/override", json={
        "override_action": "RECYCLE",
        "override_reason": "Approved recycling route for metal components",
        "reviewer_id": 1
    })
    assert override_success.status_code == 200
    assert override_success.json()["status"] == "OVERRIDDEN"
    assert override_success.json()["override_reason"] == "Approved recycling route for metal components"

# 28. API: Offline fallback & Sync endpoint
def test_api_offline_fallback():
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
    
    sync_res = client.post("/api/sync")
    assert sync_res.status_code == 200
    assert sync_res.json()["synced_count"] >= 1
    
    container_res = client.get("/api/containers/OFFLINE-CON-999")
    assert container_res.json()["status"] == "synced"
