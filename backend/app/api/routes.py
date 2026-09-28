import json
import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Dict, Any

try:
    from repackai.backend.app.database import get_db
    from repackai.backend.app.models import domain
    from repackai.backend.app.schemas import api_schemas
    from repackai.backend.app.recommender_rules.engine import RuleEngine
    from repackai.backend.app.services.recommender import RecommendationEngine
    from repackai.backend.app.services.audit_service import AuditService
    from repackai.backend.app.services.sync_service import SyncService
    from repackai.backend.app.offline_cache.cache_manager import OfflineCacheManager
    from repackai.backend.app.ingestion.validator import IngestionValidator
except ImportError:
    try:
        from backend.app.database import get_db
        from backend.app.models import domain
        from backend.app.schemas import api_schemas
        from backend.app.recommender_rules.engine import RuleEngine
        from backend.app.services.recommender import RecommendationEngine
        from backend.app.services.audit_service import AuditService
        from backend.app.services.sync_service import SyncService
        from backend.app.offline_cache.cache_manager import OfflineCacheManager
        from backend.app.ingestion.validator import IngestionValidator
    except ImportError:
        from app.database import get_db
        from app.models import domain
        from app.schemas import api_schemas
        from app.recommender_rules.engine import RuleEngine
        from app.services.recommender import RecommendationEngine
        from app.services.audit_service import AuditService
        from app.services.sync_service import SyncService
        from app.offline_cache.cache_manager import OfflineCacheManager
        from app.ingestion.validator import IngestionValidator

router = APIRouter()

def get_now():
    return datetime.datetime.now(datetime.timezone.utc)

# --- Health check ---
@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    from sqlalchemy import text
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
        
    return {
        "status": "healthy" if db_ok else "unhealthy",
        "database": "connected" if db_ok else "disconnected",
        "timestamp": get_now().isoformat()
    }

# --- Containers ---
@router.post("/containers", response_model=api_schemas.ContainerResponse)
def create_container(container: api_schemas.ContainerCreate, db: Session = Depends(get_db)):
    # Validate container fields
    valid, err_msg, cleaned_data = IngestionValidator.validate_container(container.model_dump())
    if not valid:
        raise HTTPException(status_code=400, detail=err_msg)

    db_container = db.query(domain.Container).filter(domain.Container.id == container.id).first()
    if db_container:
        raise HTTPException(status_code=400, detail="Container with this ID already exists.")
        
    # Check offline status or prefix
    status = "synced"
    if container.id.startswith("OFFLINE") or not OfflineCacheManager.is_network_online():
        status = "pending_sync"
        
    new_container = domain.Container(
        id=container.id,
        container_type=container.container_type,
        material=container.material,
        weight_kg=container.weight_kg,
        age_months=container.age_months,
        usage_count=container.usage_count,
        recyclable=container.recyclable,
        status=status
    )
    db.add(new_container)
    db.commit()
    db.refresh(new_container)
    
    # Audit log
    AuditService.log_action(
        db=db,
        user_id=None,
        action="CREATE_CONTAINER",
        entity_type="Container",
        entity_id=new_container.id,
        new_value=container.model_dump()
    )
    
    if status == "pending_sync":
        OfflineCacheManager.enqueue(db, "Container", new_container.id, container.model_dump())
        SyncService.queue_item(db, "Container", new_container.id, container.model_dump())
        
    return new_container

@router.get("/containers", response_model=List[api_schemas.ContainerResponse])
def get_containers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(domain.Container).offset(skip).limit(limit).all()

@router.get("/containers/{id}", response_model=api_schemas.ContainerResponse)
def get_container(id: str, db: Session = Depends(get_db)):
    container = db.query(domain.Container).filter(domain.Container.id == id).first()
    if not container:
        raise HTTPException(status_code=404, detail="Container not found")
    return container

# --- Inspections ---
@router.post("/inspections", response_model=api_schemas.InspectionResponse)
def create_inspection(inspection: api_schemas.InspectionCreate, db: Session = Depends(get_db)):
    container = db.query(domain.Container).filter(domain.Container.id == inspection.container_id).first()
    if not container:
        raise HTTPException(status_code=400, detail="Container not found. Register the container first.")
        
    # Validate and normalize inspection data with fallback handling
    valid, err_msg, cleaned_insp = IngestionValidator.validate_and_normalize_inspection(inspection.model_dump())
    if not valid:
        raise HTTPException(status_code=400, detail=err_msg)

    new_inspection = domain.Inspection(
        container_id=cleaned_insp["container_id"],
        damage_level=cleaned_insp.get("damage_level"),
        structural_condition=cleaned_insp.get("structural_condition"),
        cleanliness_score=cleaned_insp.get("cleanliness_score"),
        contamination=cleaned_insp.get("contamination"),
        safety_risk=cleaned_insp.get("safety_risk"),
        sensor_available=cleaned_insp.get("sensor_available", True),
        network_available=cleaned_insp.get("network_available", True),
        location_available=cleaned_insp.get("location_available", True),
        location=cleaned_insp.get("location"),
        inspection_completeness=cleaned_insp.get("inspection_completeness", 1.0),
        raw_data_json=cleaned_insp.get("raw_data_json")
    )
    
    db.add(new_inspection)
    db.commit()
    db.refresh(new_inspection)
    
    # Log action
    AuditService.log_action(
        db=db,
        user_id=None,
        action="CREATE_INSPECTION",
        entity_type="Inspection",
        entity_id=str(new_inspection.id),
        new_value=inspection.model_dump()
    )
    
    # If network is unavailable, enqueue inspection sync in offline cache
    if not inspection.network_available or not OfflineCacheManager.is_network_online():
        OfflineCacheManager.enqueue(db, "Inspection", str(new_inspection.id), inspection.model_dump())
        SyncService.queue_item(db, "Inspection", str(new_inspection.id), inspection.model_dump())
        
    return new_inspection

@router.get("/inspections/{id}", response_model=api_schemas.InspectionResponse)
def get_inspection(id: int, db: Session = Depends(get_db)):
    inspection = db.query(domain.Inspection).filter(domain.Inspection.id == id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return inspection

# --- Recommendations ---
class RecommendationRequest(BaseModel):
    container_id: str
    inspection_id: int

@router.post("/recommendations", response_model=api_schemas.RecommendationResponse)
def create_recommendation(req: RecommendationRequest, db: Session = Depends(get_db)):
    container = db.query(domain.Container).filter(domain.Container.id == req.container_id).first()
    inspection = db.query(domain.Inspection).filter(domain.Inspection.id == req.inspection_id).first()
    
    if not container or not inspection:
        raise HTTPException(status_code=400, detail="Invalid container_id or inspection_id")
        
    # Fetch material rules config from DB
    mat_rules_db = db.query(domain.MaterialRule).all()
    material_rules = {r.material_name: {
        "recyclable": r.recyclable,
        "processing_cost_per_kg": r.processing_cost_per_kg,
        "recycling_value_per_kg": r.recycling_value_per_kg,
        "carbon_recycle_per_kg": r.carbon_recycle_per_kg,
        "carbon_dispose_per_kg": r.carbon_dispose_per_kg
    } for r in mat_rules_db}
    
    # Run recommendation logic
    rec_result = RecommendationEngine.generate_recommendation(
        container_data=container.__dict__,
        inspection_data=inspection.__dict__,
        material_rules=material_rules
    )
    
    action = rec_result["recommended_action"]
    new_rec = domain.Recommendation(
        container_id=req.container_id,
        inspection_id=req.inspection_id,
        recommended_action=action,
        confidence=rec_result["confidence"],
        score=rec_result["score"],
        financial_score=rec_result["evidence"]["score_breakdown"].get(action, {}).get("financial_score", 0.0) if action != "MANUAL_REVIEW" else 0.0,
        environmental_score=rec_result["evidence"]["score_breakdown"].get(action, {}).get("environmental_score", 0.0) if action != "MANUAL_REVIEW" else 0.0,
        reusability_score=rec_result["evidence"]["score_breakdown"].get(action, {}).get("reusability_score", 0.0) if action != "MANUAL_REVIEW" else 0.0,
        operational_score=rec_result["evidence"]["score_breakdown"].get(action, {}).get("operational_score", 0.0) if action != "MANUAL_REVIEW" else 0.0,
        rules_triggered_json=json.dumps(rec_result["rules_triggered"]),
        explanation=f"{rec_result['financial_reason']} {rec_result['environmental_reason']}",
        status="PENDING_HUMAN_CONFIRMATION" if rec_result["requires_human_confirmation"] else "PENDING"
    )
    
    db.add(new_rec)
    db.commit()
    db.refresh(new_rec)
    
    response_rec = api_schemas.RecommendationResponse.model_validate(new_rec)
    response_rec.evidence = rec_result["evidence"]
    response_rec.financial_reason = rec_result["financial_reason"]
    response_rec.environmental_reason = rec_result["environmental_reason"]
    response_rec.safety_reason = rec_result["safety_reason"]
    response_rec.requires_human_confirmation = rec_result["requires_human_confirmation"]
    response_rec.alternative_actions = rec_result["alternative_actions"]
    
    return response_rec

@router.get("/recommendations/{id}", response_model=api_schemas.RecommendationResponse)
def get_recommendation(id: int, db: Session = Depends(get_db)):
    rec = db.query(domain.Recommendation).filter(domain.Recommendation.id == id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
        
    container = db.query(domain.Container).filter(domain.Container.id == rec.container_id).first()
    inspection = db.query(domain.Inspection).filter(domain.Inspection.id == rec.inspection_id).first()
    
    mat_rules_db = db.query(domain.MaterialRule).all()
    material_rules = {r.material_name: {
        "recyclable": r.recyclable,
        "processing_cost_per_kg": r.processing_cost_per_kg,
        "recycling_value_per_kg": r.recycling_value_per_kg,
        "carbon_recycle_per_kg": r.carbon_recycle_per_kg,
        "carbon_dispose_per_kg": r.carbon_dispose_per_kg
    } for r in mat_rules_db}
    
    rec_result = RecommendationEngine.generate_recommendation(
        container_data=container.__dict__,
        inspection_data=inspection.__dict__,
        material_rules=material_rules
    )
    
    response_rec = api_schemas.RecommendationResponse.model_validate(rec)
    response_rec.evidence = rec_result["evidence"]
    response_rec.financial_reason = rec_result["financial_reason"]
    response_rec.environmental_reason = rec_result["environmental_reason"]
    response_rec.safety_reason = rec_result["safety_reason"]
    response_rec.requires_human_confirmation = rec_result["requires_human_confirmation"]
    response_rec.alternative_actions = rec_result["alternative_actions"]
    
    return response_rec

@router.post("/recommendations/{id}/approve", response_model=api_schemas.RecommendationResponse)
def approve_recommendation(id: int, body: api_schemas.RecommendationApprove, db: Session = Depends(get_db)):
    rec = db.query(domain.Recommendation).filter(domain.Recommendation.id == id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    if rec.status not in ["PENDING", "PENDING_HUMAN_CONFIRMATION"]:
        raise HTTPException(status_code=400, detail=f"Recommendation already resolved with status {rec.status}")
        
    container = db.query(domain.Container).filter(domain.Container.id == rec.container_id).first()
    inspection = db.query(domain.Inspection).filter(domain.Inspection.id == rec.inspection_id).first()
    
    mat_rules_db = db.query(domain.MaterialRule).all()
    material_rules = {r.material_name: {
        "recyclable": r.recyclable,
        "processing_cost_per_kg": r.processing_cost_per_kg,
        "recycling_value_per_kg": r.recycling_value_per_kg,
        "carbon_recycle_per_kg": r.carbon_recycle_per_kg,
        "carbon_dispose_per_kg": r.carbon_dispose_per_kg
    } for r in mat_rules_db}
    
    rec_result = RecommendationEngine.generate_recommendation(
        container_data=container.__dict__,
        inspection_data=inspection.__dict__,
        material_rules=material_rules
    )
    
    old_status = rec.status
    rec.status = "APPROVED"
    rec.reviewer_id = body.reviewer_id
    rec.review_date = get_now()
    
    action = rec.recommended_action
    
    disposition = domain.Disposition(
        container_id=rec.container_id,
        recommendation_id=rec.id,
        actual_action=action,
        operator_id=body.reviewer_id,
        notes="Approved recommended action.",
        actual_cost=rec_result["evidence"]["financial_breakdown"].get(action, {}).get("processing_cost", 0.0) if action != "MANUAL_REVIEW" else 0.0,
        actual_recovery=rec_result["evidence"]["financial_breakdown"].get(action, {}).get("expected_recovery", 0.0) if action != "MANUAL_REVIEW" else 0.0,
        carbon_impact=rec_result["evidence"]["environmental_breakdown"].get(action, {}).get("carbon_avoided_kg", 0.0) if action != "MANUAL_REVIEW" else 0.0
    )
    
    db.add(disposition)
    
    AuditService.log_action(
        db=db,
        user_id=body.reviewer_id,
        action="APPROVE_RECOMMENDATION",
        entity_type="Recommendation",
        entity_id=str(rec.id),
        old_value={"status": old_status},
        new_value={"status": "APPROVED", "reviewer_id": body.reviewer_id}
    )
    
    db.commit()
    db.refresh(rec)
    
    response_rec = api_schemas.RecommendationResponse.model_validate(rec)
    response_rec.evidence = rec_result["evidence"]
    response_rec.financial_reason = rec_result["financial_reason"]
    response_rec.environmental_reason = rec_result["environmental_reason"]
    response_rec.safety_reason = rec_result["safety_reason"]
    response_rec.requires_human_confirmation = False
    response_rec.alternative_actions = rec_result["alternative_actions"]
    
    return response_rec

@router.post("/recommendations/{id}/override", response_model=api_schemas.RecommendationResponse)
def override_recommendation(id: int, body: api_schemas.RecommendationOverride, db: Session = Depends(get_db)):
    rec = db.query(domain.Recommendation).filter(domain.Recommendation.id == id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    if rec.status not in ["PENDING", "PENDING_HUMAN_CONFIRMATION"]:
        raise HTTPException(status_code=400, detail=f"Recommendation already resolved with status {rec.status}")
        
    container = db.query(domain.Container).filter(domain.Container.id == rec.container_id).first()
    inspection = db.query(domain.Inspection).filter(domain.Inspection.id == rec.inspection_id).first()
    
    # HARD SAFETY GATE: Check if override action violates safety
    rule_results = RuleEngine.evaluate(inspection.__dict__, container.__dict__)
    prohibited = RuleEngine.get_prohibited_actions(rule_results)
    
    override_action = body.override_action.upper()
    if override_action in prohibited:
        violations = [r.explanation for r in rule_results if r.is_triggered and override_action in r.prohibited_actions]
        raise HTTPException(
            status_code=400, 
            detail=f"Safety rule violation. Action {override_action} is prohibited for this container due to: {', '.join(violations)}"
        )
        
    mat_rules_db = db.query(domain.MaterialRule).all()
    material_rules = {r.material_name: {
        "recyclable": r.recyclable,
        "processing_cost_per_kg": r.processing_cost_per_kg,
        "recycling_value_per_kg": r.recycling_value_per_kg,
        "carbon_recycle_per_kg": r.carbon_recycle_per_kg,
        "carbon_dispose_per_kg": r.carbon_dispose_per_kg
    } for r in mat_rules_db}
    
    rec_result = RecommendationEngine.generate_recommendation(
        container_data=container.__dict__,
        inspection_data=inspection.__dict__,
        material_rules=material_rules
    )
    
    old_status = rec.status
    old_action = rec.recommended_action
    rec.status = "OVERRIDDEN"
    rec.override_reason = body.override_reason
    rec.reviewer_id = body.reviewer_id
    rec.review_date = get_now()
    
    disposition = domain.Disposition(
        container_id=rec.container_id,
        recommendation_id=rec.id,
        actual_action=override_action,
        operator_id=body.reviewer_id,
        notes=f"Overridden: {body.override_reason}",
        actual_cost=rec_result["evidence"]["financial_breakdown"].get(override_action, {}).get("processing_cost", 0.0) if override_action != "MANUAL_REVIEW" else 0.0,
        actual_recovery=rec_result["evidence"]["financial_breakdown"].get(override_action, {}).get("expected_recovery", 0.0) if override_action != "MANUAL_REVIEW" else 0.0,
        carbon_impact=rec_result["evidence"]["environmental_breakdown"].get(override_action, {}).get("carbon_avoided_kg", 0.0) if override_action != "MANUAL_REVIEW" else 0.0
    )
    
    db.add(disposition)
    
    AuditService.log_action(
        db=db,
        user_id=body.reviewer_id,
        action="OVERRIDE_RECOMMENDATION",
        entity_type="Recommendation",
        entity_id=str(rec.id),
        old_value={"status": old_status, "recommended_action": old_action},
        new_value={"status": "OVERRIDDEN", "override_action": override_action, "override_reason": body.override_reason, "reviewer_id": body.reviewer_id}
    )
    
    db.commit()
    db.refresh(rec)
    
    response_rec = api_schemas.RecommendationResponse.model_validate(rec)
    response_rec.evidence = rec_result["evidence"]
    response_rec.financial_reason = rec_result["financial_reason"]
    response_rec.environmental_reason = rec_result["environmental_reason"]
    response_rec.safety_reason = rec_result["safety_reason"]
    response_rec.requires_human_confirmation = False
    response_rec.alternative_actions = rec_result["alternative_actions"]
    
    return response_rec

# --- Rules ---
@router.get("/rules", response_model=List[api_schemas.RuleResponse])
def get_rules(db: Session = Depends(get_db)):
    return [
        api_schemas.RuleResponse(
            rule_name="Safety Constraint (Structural & Risk)",
            is_triggered=False,
            severity="CRITICAL",
            explanation="Unsafe structure or critical safety risk prohibits repair, resell, refurbishment.",
            prohibited_actions=["RESELL", "REPAIR", "REFURBISH"]
        ),
        api_schemas.RuleResponse(
            rule_name="Contamination Constraint",
            is_triggered=False,
            severity="CRITICAL",
            explanation="Hazardous contamination prohibits resale, repair, refurbishment, recycling.",
            prohibited_actions=["RESELL", "REPAIR", "REFURBISH", "RECYCLE"]
        ),
        api_schemas.RuleResponse(
            rule_name="Recycling Constraint",
            is_triggered=False,
            severity="WARNING",
            explanation="Non-recyclable materials are prohibited from recycling pathways.",
            prohibited_actions=["RECYCLE"]
        ),
        api_schemas.RuleResponse(
            rule_name="Completeness Constraint",
            is_triggered=False,
            severity="WARNING",
            explanation="Inspection completeness < 80% requires Manual Review escalation.",
            prohibited_actions=[]
        )
    ]

# --- Audit Logs ---
@router.get("/audit-logs", response_model=List[api_schemas.AuditLogResponse])
def get_audit_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(domain.AuditLog).order_by(domain.AuditLog.timestamp.desc()).offset(skip).limit(limit).all()

# --- Analytics ---
@router.get("/analytics", response_model=api_schemas.AnalyticsResponse)
def get_analytics(db: Session = Depends(get_db)):
    dispositions = db.query(domain.Disposition).all()
    recommendations = db.query(domain.Recommendation).all()
    
    total_processed = len(dispositions)
    total_financial = sum(d.actual_recovery - d.actual_cost for d in dispositions)
    total_waste = 0.0
    total_carbon = 0.0
    
    actions_distribution = {}
    for d in dispositions:
        actions_distribution[d.actual_action] = actions_distribution.get(d.actual_action, 0) + 1
        total_carbon += d.carbon_impact
        container = db.query(domain.Container).filter(domain.Container.id == d.container_id).first()
        if container:
            if d.actual_action in ["RESELL", "REPAIR", "REFURBISH"]:
                total_waste += container.weight_kg
            elif d.actual_action == "RECYCLE":
                total_waste += container.weight_kg * 0.8
                
    total_resolved = len([r for r in recommendations if r.status in ["APPROVED", "OVERRIDDEN"]])
    total_overridden = len([r for r in recommendations if r.status == "OVERRIDDEN"])
    override_rate = (total_overridden / total_resolved) if total_resolved > 0 else 0.0
    
    return api_schemas.AnalyticsResponse(
        total_processed=total_processed,
        total_financial_recovery=round(total_financial, 2),
        total_waste_avoided_kg=round(total_waste, 2),
        total_carbon_saved_kg=round(total_carbon, 2),
        actions_distribution=actions_distribution,
        override_rate=round(override_rate, 4)
    )

# --- Force Sync Queue Endpoint ---
@router.post("/sync")
def trigger_sync(db: Session = Depends(get_db)):
    res_queue = OfflineCacheManager.sync_all(db)
    res_legacy = SyncService.sync_pending_queue(db)
    return {
        "status": "SYNCED",
        "synced_count": res_queue.get("synced_count", 0) + res_legacy.get("synced_count", 0),
        "failed_count": res_queue.get("failed_count", 0) + res_legacy.get("failed_count", 0),
        "errors": res_queue.get("errors", []) + res_legacy.get("errors", [])
    }
