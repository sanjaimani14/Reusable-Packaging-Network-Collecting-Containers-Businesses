import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from repackai.backend.app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="operator")  # admin, operator, inspector
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    audit_logs = relationship("AuditLog", back_populates="user")

class Container(Base):
    __tablename__ = "containers"
    
    id = Column(String, primary_key=True, index=True)  # container_id
    container_type = Column(String, nullable=False)
    material = Column(String, nullable=False)
    weight_kg = Column(Float, nullable=False)
    age_months = Column(Integer, nullable=False)
    usage_count = Column(Integer, nullable=False)
    recyclable = Column(Boolean, default=True)
    status = Column(String, default="synced")  # synced, pending_sync
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    inspections = relationship("Inspection", back_populates="container", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="container", cascade="all, delete-orphan")
    dispositions = relationship("Disposition", back_populates="container", cascade="all, delete-orphan")

class Inspection(Base):
    __tablename__ = "inspections"
    
    id = Column(Integer, primary_key=True, index=True)
    container_id = Column(String, ForeignKey("containers.id"), nullable=False)
    inspector_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    inspection_date = Column(DateTime, default=datetime.datetime.utcnow)
    damage_level = Column(String, nullable=True)  # None, Low, Medium, High, Critical
    structural_condition = Column(String, nullable=True)  # Safe, Minor Damage, Moderate Damage, Unsafe
    cleanliness_score = Column(Float, nullable=True)
    contamination = Column(String, nullable=True)  # None, Organic, Chemical, Hazardous
    safety_risk = Column(String, nullable=True)  # Low, Medium, High
    sensor_available = Column(Boolean, default=True)
    network_available = Column(Boolean, default=True)
    location_available = Column(Boolean, default=True)
    location = Column(String, nullable=True)
    inspection_completeness = Column(Float, default=1.0)
    raw_data_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    container = relationship("Container", back_populates="inspections")
    recommendations = relationship("Recommendation", back_populates="inspection", cascade="all, delete-orphan")

class Recommendation(Base):
    __tablename__ = "recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    container_id = Column(String, ForeignKey("containers.id"), nullable=False)
    inspection_id = Column(Integer, ForeignKey("inspections.id"), nullable=False)
    recommended_action = Column(String, nullable=False)  # REPAIR, REFURBISH, RESELL, RECYCLE, DISPOSE, MANUAL_REVIEW
    confidence = Column(Float, nullable=False)
    score = Column(Float, nullable=False)
    financial_score = Column(Float, nullable=False)
    environmental_score = Column(Float, nullable=False)
    reusability_score = Column(Float, nullable=False)
    operational_score = Column(Float, nullable=False)
    rules_triggered_json = Column(Text, nullable=True)  # json string list of rules
    explanation = Column(Text, nullable=True)
    status = Column(String, default="PENDING")  # PENDING, APPROVED, OVERRIDDEN
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    override_reason = Column(Text, nullable=True)
    review_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    container = relationship("Container", back_populates="recommendations")
    inspection = relationship("Inspection", back_populates="recommendations")
    dispositions = relationship("Disposition", back_populates="recommendation", cascade="all, delete-orphan")

class Disposition(Base):
    __tablename__ = "dispositions"
    
    id = Column(Integer, primary_key=True, index=True)
    container_id = Column(String, ForeignKey("containers.id"), nullable=False)
    recommendation_id = Column(Integer, ForeignKey("recommendations.id"), nullable=False)
    actual_action = Column(String, nullable=False)  # REPAIR, REFURBISH, RESELL, RECYCLE, DISPOSE
    processed_at = Column(DateTime, default=datetime.datetime.utcnow)
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)
    actual_cost = Column(Float, default=0.0)
    actual_recovery = Column(Float, default=0.0)
    carbon_impact = Column(Float, default=0.0)
    
    # Relationships
    container = relationship("Container", back_populates="dispositions")
    recommendation = relationship("Recommendation", back_populates="dispositions")

class MaterialRule(Base):
    __tablename__ = "material_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    material_name = Column(String, unique=True, index=True, nullable=False)
    recyclable = Column(Boolean, default=True)
    processing_cost_per_kg = Column(Float, nullable=False)
    recycling_value_per_kg = Column(Float, nullable=False)
    carbon_recycle_per_kg = Column(Float, nullable=False)
    carbon_dispose_per_kg = Column(Float, nullable=False)

class DisposalRule(Base):
    __tablename__ = "disposal_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    contamination_type = Column(String, unique=True, index=True, nullable=False)
    disposal_cost_multiplier = Column(Float, default=1.0)
    is_hazardous = Column(Boolean, default=False)
    requires_special_handling = Column(Boolean, default=False)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)  # APPROVE, OVERRIDE, CREATE_INSPECTION, etc.
    entity_type = Column(String, nullable=False)  # Recommendation, Inspection, Container
    entity_id = Column(String, nullable=False)
    old_value_json = Column(Text, nullable=True)
    new_value_json = Column(Text, nullable=True)
    ip_address = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")

class SyncQueue(Base):
    __tablename__ = "sync_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String, nullable=False)  # Container, Inspection
    entity_id = Column(String, nullable=False)
    payload_json = Column(Text, nullable=False)
    status = Column(String, default="PENDING")  # PENDING, SYNCED, FAILED
    retry_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Experiment(Base):
    __tablename__ = "experiments"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    model_version = Column(String, nullable=False)
    parameters_json = Column(Text, nullable=True)
    metrics_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
