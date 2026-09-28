import os
import sys
import json
import tempfile
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
repack_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for p in [root_dir, repack_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from backend.app.database import Base
    from backend.app.models import domain
    from backend.app.ingestion.validator import IngestionValidator
    from backend.app.recommender_rules.engine import RuleEngine
    from backend.app.calculations.financial import FinancialCalculator
    from backend.app.calculations.environmental import EnvironmentalCalculator
    from backend.app.services.recommender import RecommendationEngine
    from backend.app.offline_cache.cache_manager import OfflineCacheManager
    from backend.app.evaluation.metrics import EvaluationMetrics
    from scripts.generate_dataset import generate_synthetic_data
    from scripts.baseline_heuristic import run_baseline_heuristic
except ImportError:
    from repackai.backend.app.database import Base
    from repackai.backend.app.models import domain
    from repackai.backend.app.ingestion.validator import IngestionValidator
    from repackai.backend.app.recommender_rules.engine import RuleEngine
    from repackai.backend.app.calculations.financial import FinancialCalculator
    from repackai.backend.app.calculations.environmental import EnvironmentalCalculator
    from repackai.backend.app.services.recommender import RecommendationEngine
    from repackai.backend.app.offline_cache.cache_manager import OfflineCacheManager
    from repackai.backend.app.evaluation.metrics import EvaluationMetrics
    from repackai.scripts.generate_dataset import generate_synthetic_data
    from repackai.scripts.baseline_heuristic import run_baseline_heuristic

def run_end_to_end_verification():
    print("=====================================")
    print("REUSABLE PACKAGING SYSTEM VERIFICATION")
    print("=====================================")

    # 1. Dataset Generation
    tmp_dir = tempfile.mkdtemp()
    try:
        temp_csv = os.path.join(tmp_dir, "test_dataset.csv")
        df_gen = generate_synthetic_data(num_records=100, output_path=temp_csv, seed=42)
        assert os.path.exists(temp_csv) and len(df_gen) == 100, "Dataset generation failed"
        print("[PASS] Dataset generation")

        # 2. Data Validation
        valid_c, _, cleaned_c = IngestionValidator.validate_container({
            "id": "CON-VERIFY-001", "container_type": "Crate", "material": "Plastic", "weight_kg": 12.0
        })
        assert valid_c is True, "Container validation failed"
        valid_i, _, cleaned_i = IngestionValidator.validate_and_normalize_inspection({
            "container_id": "CON-VERIFY-001", "damage_level": "Low", "structural_condition": "Safe",
            "cleanliness_score": 90.0, "contamination": "None", "safety_risk": "Low"
        })
        assert valid_i is True, "Inspection validation failed"
        print("[PASS] Data validation")

        # 3. Baseline
        temp_baseline_json = os.path.join(tmp_dir, "baseline_results.json")
        base_res = run_baseline_heuristic(data_path=temp_csv, output_path=temp_baseline_json)
        assert base_res["total_containers_evaluated"] == 100, "Baseline evaluation failed"
        print("[PASS] Baseline")

        # 4. Proposed Recommender
        rec_res = RecommendationEngine.generate_recommendation(cleaned_c, cleaned_i)
        assert rec_res["recommended_action"] in ["RESELL", "REPAIR", "REFURBISH", "RECYCLE", "DISPOSE"], "Recommendation failed"
        print("[PASS] Proposed recommender")

        # 5. Safety Gate (Unsafe container check)
        unsafe_c = {"material": "Metal", "weight_kg": 30.0, "recyclable": True}
        unsafe_i = {
            "resale_value": 500.0, "repair_cost": 20.0, "refurbishment_cost": 30.0, "recycling_value": 15.0, "disposal_cost": 10.0,
            "structural_condition": "Unsafe", "safety_risk": "High", "contamination": "None", "inspection_completeness": 1.0,
            "carbon_repair": 2.0, "carbon_refurbish": 3.0, "carbon_recycle": 5.0, "carbon_dispose": 15.0, "carbon_resell": 0.2
        }
        rec_unsafe = RecommendationEngine.generate_recommendation(unsafe_c, unsafe_i)
        assert rec_unsafe["recommended_action"] in ["RECYCLE", "DISPOSE"], "Safety gate failed: allowed reuse of unsafe container"
        assert rec_unsafe["recommended_action"] not in ["RESELL", "REPAIR", "REFURBISH"]
        print("[PASS] Safety gate")

        # 6. Evidence Generation
        evidence = rec_res["evidence"]
        assert "financial_breakdown" in evidence and "environmental_breakdown" in evidence and "score_breakdown" in evidence
        assert len(rec_res["financial_reason"]) > 0 and len(rec_res["environmental_reason"]) > 0
        print("[PASS] Evidence generation")

        # 7. Human Confirmation Flag
        assert rec_unsafe["requires_human_confirmation"] is True, "Human confirmation not flagged for unsafe container"
        print("[PASS] Human confirmation")

        # 8. Setup DB for Persistence, Override & Offline Tests
        db_path = os.path.join(tmp_dir, "verify.db")
        db_engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=db_engine)
        VerifySession = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
        db = VerifySession()

        try:
            # Create container & inspection in DB
            db_c = domain.Container(id="CON-DB-01", container_type="Drum", material="Metal", weight_kg=25.0, age_months=12, usage_count=20)
            db.add(db_c)
            db.commit()

            db_i = domain.Inspection(container_id="CON-DB-01", structural_condition="Unsafe", safety_risk="High")
            db.add(db_i)
            db.commit()

            # Create recommendation
            db_rec = domain.Recommendation(
                container_id="CON-DB-01", inspection_id=db_i.id, recommended_action="RECYCLE",
                confidence=0.85, score=0.75, financial_score=0.4, environmental_score=0.6,
                reusability_score=0.2, operational_score=0.7, status="PENDING_HUMAN_CONFIRMATION"
            )
            db.add(db_rec)
            db.commit()

            # Test Human Override & Logging
            override_reason = "Manual override by warehouse supervisor for metal scrap"
            insp_eval_dict = {"structural_condition": "Unsafe", "safety_risk": "High", "contamination": "None"}
            cont_eval_dict = {"recyclable": True, "material": "Metal"}
            rule_eval = RuleEngine.evaluate(insp_eval_dict, cont_eval_dict)
            prohibited = RuleEngine.get_prohibited_actions(rule_eval)
            
            # RESELL is prohibited by Safety Gate
            assert "RESELL" in prohibited
            # RECYCLE is allowed
            assert "RECYCLE" not in prohibited

            db_rec.status = "OVERRIDDEN"
            db_rec.override_reason = override_reason
            db_rec.reviewer_id = 1
            
            audit = domain.AuditLog(
                user_id=1, action="OVERRIDE_RECOMMENDATION", entity_type="Recommendation",
                entity_id=str(db_rec.id), new_value_json=json.dumps({"override_action": "RECYCLE", "reason": override_reason})
            )
            db.add(audit)
            db.commit()
            print("[PASS] Override logging")

            # 9. Offline Cache
            OfflineCacheManager.set_network_state(False)
            queue_item = OfflineCacheManager.enqueue(db, "Container", "CON-OFFLINE-01", {"weight_kg": 15.0})
            assert queue_item.status == "PENDING", "Offline cache enqueue failed"
            sync_res = OfflineCacheManager.sync_all(db)
            assert sync_res["status"] == "OFFLINE_PENDING", "Offline pending check failed"
            print("[PASS] Offline cache")

            # 10. Synchronization
            OfflineCacheManager.set_network_state(True)
            sync_restored = OfflineCacheManager.sync_all(db)
            assert sync_restored["status"] == "SYNC_COMPLETE" and sync_restored["synced_count"] >= 1
            print("[PASS] Synchronization")

            # 11. Evaluation
            eval_val = EvaluationMetrics.compute_value_recovered(["RESELL", "REPAIR"], [{"RESELL": {"net_value": 100.0}}, {"REPAIR": {"net_value": 80.0}}])
            assert eval_val == 180.0, "Evaluation metric calculation failed"
            print("[PASS] Evaluation")

            # 12. Database
            persisted_rec = db.query(domain.Recommendation).filter(domain.Recommendation.id == db_rec.id).first()
            assert persisted_rec is not None and persisted_rec.status == "OVERRIDDEN"
            assert persisted_rec.override_reason == override_reason
            print("[PASS] Database")

            # 13. Failure Cases Check
            # Case 1: High Value Unsafe Container
            assert rec_unsafe["recommended_action"] not in ["RESELL", "REPAIR"], "Failure Case 1 failed"
            # Case 2: Network Unavailable Handled
            assert queue_item is not None, "Failure Case 2 failed"
            # Case 3: Sensor Fallback Handled
            val_fb, _, clean_fb = IngestionValidator.validate_and_normalize_inspection({
                "container_id": "CON-FB-1", "sensor_available": False, "location_available": False
            })
            assert "FALLBACK_SENSOR_UNAVAILABLE" in clean_fb["ingestion_flags"], "Failure Case 3 failed"
            print("[PASS] Failure cases")

        finally:
            OfflineCacheManager.set_network_state(True)
            db.close()
            db_engine.dispose()
            
    finally:
        try:
            import shutil
            shutil.rmtree(tmp_dir, ignore_errors=True)
        except Exception:
            pass

    print("=====================================")
    print("FINAL STATUS: PASS")
    print("=====================================")

if __name__ == "__main__":
    run_end_to_end_verification()
