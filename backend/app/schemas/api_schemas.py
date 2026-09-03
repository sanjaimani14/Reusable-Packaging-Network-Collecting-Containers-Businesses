import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

# User schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: str = "operator"

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime.datetime
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str

# Container schemas
class ContainerBase(BaseModel):
    id: str = Field(..., description="Unique container ID (e.g., CON-12345)")
    container_type: str = Field(..., description="Box, Pallet, Crate, Drum, Tote")
    material: str = Field(..., description="Cardboard, Wood, Plastic, Metal")
    weight_kg: float
    age_months: int
    usage_count: int
    recyclable: bool = True

class ContainerCreate(ContainerBase):
    pass

class ContainerResponse(ContainerBase):
    status: str
    created_at: datetime.datetime
    
    class Config:
        from_attributes = True

# Inspection schemas
class InspectionBase(BaseModel):
    container_id: str
    damage_level: Optional[str] = None  # None, Low, Medium, High, Critical
    structural_condition: Optional[str] = None  # Safe, Minor Damage, Moderate Damage, Unsafe
    cleanliness_score: Optional[float] = None
    contamination: Optional[str] = None  # None, Organic, Chemical, Hazardous
    safety_risk: Optional[str] = None  # Low, Medium, High
    sensor_available: bool = True
    network_available: bool = True
    location_available: bool = True
    location: Optional[str] = None
    inspection_completeness: float = 1.0
    raw_data_json: Optional[str] = None

class InspectionCreate(InspectionBase):
    pass

class InspectionResponse(InspectionBase):
    id: int
    inspector_id: Optional[int] = None
    inspection_date: datetime.datetime
    created_at: datetime.datetime
    
    class Config:
        from_attributes = True

# Recommendation schemas
class RecommendationResponse(BaseModel):
    id: int
    container_id: str
    inspection_id: int
    recommended_action: str
    confidence: float
    score: float
    financial_score: float
    environmental_score: float
    reusability_score: float
    operational_score: float
    rules_triggered_json: Optional[str] = None
    explanation: Optional[str] = None
    status: str
    reviewer_id: Optional[int] = None
    override_reason: Optional[str] = None
    review_date: Optional[datetime.datetime] = None
    created_at: datetime.datetime
    
    # Custom fields for hybrid output details
    evidence: Optional[Dict[str, Any]] = None
    financial_reason: Optional[str] = None
    environmental_reason: Optional[str] = None
    safety_reason: Optional[str] = None
    requires_human_confirmation: bool = False
    alternative_actions: Optional[List[Dict[str, Any]]] = None

    class Config:
        from_attributes = True

class RecommendationApprove(BaseModel):
    reviewer_id: Optional[int] = None

class RecommendationOverride(BaseModel):
    override_action: str = Field(..., description="REPAIR, REFURBISH, RESELL, RECYCLE, DISPOSE")
    override_reason: str = Field(..., min_length=5, description="Justification for manual override")
    reviewer_id: Optional[int] = None

# Rule schemas
class RuleResponse(BaseModel):
    rule_name: str
    is_triggered: bool
    severity: str
    explanation: str
    prohibited_actions: List[str]

# Audit Log schemas
class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    action: str
    entity_type: str
    entity_id: str
    old_value_json: Optional[str] = None
    new_value_json: Optional[str] = None
    ip_address: Optional[str] = None
    timestamp: datetime.datetime
    
    class Config:
        from_attributes = True

# Analytics schemas
class AnalyticsResponse(BaseModel):
    total_processed: int
    total_financial_recovery: float
    total_waste_avoided_kg: float
    total_carbon_saved_kg: float
    actions_distribution: Dict[str, int]
    override_rate: float
