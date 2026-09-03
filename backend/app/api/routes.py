import json
import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Dict, Any



from repackai.backend.app.database import get_db
from repackai.backend.app.models import domain
from repackai.backend.app.schemas import api_schemas
from repackai.backend.app.rules.engine import RuleEngine
from repackai.backend.app.services.recommender import RecommendationEngine
from repackai.backend.app.services.audit_service import AuditService
from repackai.backend.app.services.sync_service import SyncService

router = APIRouter()

# --- Health check ---
@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    from sqlalchemy import text
    try:
        # Verify database connection
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        db_ok = False
        
    return {
        "status": "healthy" if db_ok else "unhealthy",
        "database": "connected" if db_ok else "disconnected",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

# --- Containers ---
@router.post("/containers", response_model=api_schemas.ContainerResponse)
def create_container(container: api_schemas.ContainerCreate, db: Session = Depends(get_db)):
    db_container = db.query(domain.Container).filter(domain.Container.id == container.id).first()
    if db_container:
        raise HTTPException(status_code=400, detail="Container with this ID already exists.")
        
    # Check if network is available to simulate offline fallback
    status = "synced"
    # To demonstrate offline queueing, let's say if we get container ID starting with 'OFFLINE-', we queue it
    if container.id.startswith("OFFLINE"):
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
        new_value=container.dict()
    )
    
    if status == "pending_sync":
        # Add to SyncQueue
        SyncService.queue_item(db, "Container", new_container.id, container.dict())
        
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
        
    new_inspection = domain.Inspection(
        container_id=inspection.container_id,
        damage_level=inspection.damage_level,
        structural_condition=inspection.structural_condition,
        cleanliness_score=inspection.cleanliness_score,
        contamination=inspection.contamination,
        safety_risk=inspection.safety_risk,
        sensor_available=inspection.sensor_available,
        network_available=inspection.network_available,
        location_available=inspection.location_available,
        location=inspection.location,
        inspection_completeness=inspection.inspection_completeness,
        raw_data_json=inspection.raw_data_json
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
        new_value=inspection.dict()
    )
    
    # If network is unavailable, enqueue inspection sync
    if not inspection.network_available:
        SyncService.queue_item(db, "Inspection", str(new_inspection.id), inspection.dict())
        
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
    
    new_rec = domain.Recommendation(
        container_id=req.container_id,
        inspection_id=req.inspection_id,
        recommended_action=rec_result["recommended_action"],
        confidence=rec_result["confidence"],
        score=rec_result["score"],
        financial_score=rec_result["evidence"]["score_breakdown"][rec_result["recommended_action"]]["financial_score"] if rec_result["recommended_action"] != "MANUAL_REVIEW" else 0.0,
        environmental_score=rec_result["evidence"]["score_breakdown"][rec_result["recommended_action"]]["environmental_score"] if rec_result["recommended_action"] != "MANUAL_REVIEW" else 0.0,
        reusability_score=rec_result["evidence"]["score_breakdown"][rec_result["recommended_action"]]["reusability_score"] if rec_result["recommended_action"] != "MANUAL_REVIEW" else 0.0,
        operational_score=rec_result["evidence"]["score_breakdown"][rec_result["recommended_action"]]["operational_score"] if rec_result["recommended_action"] != "MANUAL_REVIEW" else 0.0,
        rules_triggered_json=json.dumps(rec_result["rules_triggered"]),
        explanation=f"{rec_result['financial_reason']} {rec_result['environmental_reason']}",
        status="PENDING"
    )
    
    db.add(new_rec)
    db.commit()
    db.refresh(new_rec)
    
    # Populate the additional response fields in model
    response_rec = api_schemas.RecommendationResponse.from_orm(new_rec)
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
    
    # Regenerate evaluation context dynamically for evidence details
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
    
    response_rec = api_schemas.RecommendationResponse.from_orm(rec)
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
    if rec.status != "PENDING":
        raise HTTPException(status_code=400, detail=f"Recommendation already resolved with status {rec.status}")
        
    container = db.query(domain.Container).filter(domain.Container.id == rec.container_id).first()
    inspection = db.query(domain.Inspection).filter(domain.Inspection.id == rec.inspection_id).first()
    
    # Calculate costs for disposition mapping
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
    
    # Finalize status
    rec.status = "APPROVED"
    rec.reviewer_id = body.reviewer_id
    rec.review_date = datetime.datetime.utcnow()
    
    action = rec.recommended_action
    
    # Record actual disposition operation
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
    
    # Record audit log
    AuditService.log_action(
        db=db,
        user_id=body.reviewer_id,
        action="APPROVE_RECOMMENDATION",
        entity_type="Recommendation",
        entity_id=str(rec.id),
        old_value={"status": "PENDING"},
        new_value={"status": "APPROVED", "reviewer_id": body.reviewer_id}
    )
    
    db.commit()
    db.refresh(rec)
    
    # Set helper fields on response model
    response_rec = api_schemas.RecommendationResponse.from_orm(rec)
    response_rec.evidence = rec_result["evidence"]
    response_rec.financial_reason = rec_result["financial_reason"]
    response_rec.environmental_reason = rec_result["environmental_reason"]
    response_rec.safety_reason = rec_result["safety_reason"]
    response_rec.requires_human_confirmation = rec_result["requires_human_confirmation"]
    response_rec.alternative_actions = rec_result["alternative_actions"]
    
    return response_rec

@router.post("/recommendations/{id}/override", response_model=api_schemas.RecommendationResponse)
def override_recommendation(id: int, body: api_schemas.RecommendationOverride, db: Session = Depends(get_db)):
    rec = db.query(domain.Recommendation).filter(domain.Recommendation.id == id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    if rec.status != "PENDING":
        raise HTTPException(status_code=400, detail=f"Recommendation already resolved with status {rec.status}")
        
    container = db.query(domain.Container).filter(domain.Container.id == rec.container_id).first()
    inspection = db.query(domain.Inspection).filter(domain.Inspection.id == rec.inspection_id).first()
    
    # Validate rules to block overriding safety rules (e.g. overriding Unsafe container to Resell)
    rule_results = RuleEngine.evaluate(inspection.__dict__, container.__dict__)
    prohibited = RuleEngine.get_prohibited_actions(rule_results)
    
    override_action = body.override_action.upper()
    if override_action in prohibited:
        raise HTTPException(
            status_code=400, 
            detail=f"Safety rule violation. Action {override_action} is prohibited for this container due to: "
                   f"{', '.join([r.explanation for r in rule_results if r.is_triggered and override_action in r.prohibited_actions])}"
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
    
    # Process override
    rec.status = "OVERRIDDEN"
    rec.override_reason = body.override_reason
    rec.reviewer_id = body.reviewer_id
    rec.review_date = datetime.datetime.utcnow()
    
    # Record actual disposition operation
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
    
    # Audit log
    AuditService.log_action(
        db=db,
        user_id=body.reviewer_id,
        action="OVERRIDE_RECOMMENDATION",
        entity_type="Recommendation",
        entity_id=str(rec.id),
        old_value={"status": "PENDING", "recommended_action": rec.recommended_action},
        new_value={"status": "OVERRIDDEN", "override_action": override_action, "override_reason": body.override_reason, "reviewer_id": body.reviewer_id}
    )
    
    db.commit()
    db.refresh(rec)
    
    response_rec = api_schemas.RecommendationResponse.from_orm(rec)
    response_rec.evidence = rec_result["evidence"]
    response_rec.financial_reason = rec_result["financial_reason"]
    response_rec.environmental_reason = rec_result["environmental_reason"]
    response_rec.safety_reason = rec_result["safety_reason"]
    response_rec.requires_human_confirmation = rec_result["requires_human_confirmation"]
    response_rec.alternative_actions = rec_result["alternative_actions"]
    
    return response_rec

# --- Rules ---
@router.get("/rules", response_model=List[api_schemas.RuleResponse])
def get_rules(db: Session = Depends(get_db)):
    # Standard static descriptions of the active rules in the engine
    # In a full project, rules could be retrieved from the db.
    # Here we mock them dynamically or return hardcoded rules metadata.
    return [
        api_schemas.RuleResponse(
            rule_name="Safety Constraint (Structural & Risk)",
            is_triggered=False,
            severity="CRITICAL",
            explanation="Unsafe structure or safety risk level Prohibits repair, resell, refurbishment.",
            prohibited_actions=["RESELL", "REPAIR", "REFURBISH"]
        ),
        api_schemas.RuleResponse(
            rule_name="Contamination Constraint",
            is_triggered=False,
            severity="CRITICAL",
            explanation="Hazardous contamination Prohibits resale, repair, refurbishment, recycling.",
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
    
    # Re-sum from dispositions
    actions_distribution = {}
    for d in dispositions:
        actions_distribution[d.actual_action] = actions_distribution.get(d.actual_action, 0) + 1
        total_carbon += d.carbon_impact
        # For waste mapping
        container = db.query(domain.Container).filter(domain.Container.id == d.container_id).first()
        if container:
            if d.actual_action in ["RESELL", "REPAIR", "REFURBISH"]:
                total_waste += container.weight_kg
            elif d.actual_action == "RECYCLE":
                total_waste += container.weight_kg * 0.8
                
    # Calculate override rate
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
    res = SyncService.sync_pending_queue(db)
    return res
