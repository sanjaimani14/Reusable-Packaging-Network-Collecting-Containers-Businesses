from typing import Dict, Any, Tuple, Optional
import datetime

class IngestionValidator:
    """
    Validates and normalizes incoming inspection and container data.
    Implements sensor and network fallback handling, completeness scoring,
    and field normalization.
    """
    
    REQUIRED_CONTAINER_FIELDS = ["id", "container_type", "material", "weight_kg"]
    VALID_MATERIALS = ["Cardboard", "Plastic", "Wood", "Metal"]
    VALID_CONTAINER_TYPES = ["Box", "Pallet", "Crate", "Drum", "Tote"]
    
    @classmethod
    def validate_container(cls, data: Dict[str, Any]) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        cleaned = dict(data)
        for field in cls.REQUIRED_CONTAINER_FIELDS:
            if field not in cleaned or cleaned[field] is None:
                return False, f"Missing required container field: {field}", cleaned
                
        if cleaned["material"] not in cls.VALID_MATERIALS:
            return False, f"Invalid material '{cleaned['material']}'. Allowed: {cls.VALID_MATERIALS}", cleaned
            
        if cleaned["container_type"] not in cls.VALID_CONTAINER_TYPES:
            return False, f"Invalid container_type '{cleaned['container_type']}'. Allowed: {cls.VALID_CONTAINER_TYPES}", cleaned
            
        if float(cleaned.get("weight_kg", 0)) <= 0:
            return False, "weight_kg must be greater than zero.", cleaned
            
        # Defaults
        cleaned["age_months"] = int(cleaned.get("age_months", 1))
        cleaned["usage_count"] = int(cleaned.get("usage_count", 1))
        cleaned["recyclable"] = bool(cleaned.get("recyclable", True))
        
        return True, None, cleaned

    @classmethod
    def validate_and_normalize_inspection(cls, data: Dict[str, Any]) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        cleaned = dict(data)
        
        if "container_id" not in cleaned or not cleaned["container_id"]:
            return False, "Missing container_id in inspection record.", cleaned
            
        # Check sensor availability and location fallback (Edge Case 3)
        sensor_available = cleaned.get("sensor_available", True)
        location_available = cleaned.get("location_available", True)
        network_available = cleaned.get("network_available", True)
        
        flags = []
        if not sensor_available:
            flags.append("FALLBACK_SENSOR_UNAVAILABLE")
            if cleaned.get("cleanliness_score") is None:
                cleaned["cleanliness_score"] = 50.0  # conservative median fallback
            if cleaned.get("damage_level") is None:
                cleaned["damage_level"] = "Medium"  # conservative estimate
                
        if not location_available:
            flags.append("FALLBACK_LOCATION_DEFAULTED")
            if not cleaned.get("location"):
                cleaned["location"] = "Facility_Fallback_Dock"
                
        if not network_available:
            flags.append("OFFLINE_PENDING")

        # Map alternate field names for compatibility
        if "material_type" in cleaned and "material" not in cleaned:
            cleaned["material"] = cleaned["material_type"]
        if "structural_damage" in cleaned and "structural_condition" not in cleaned:
            cleaned["structural_condition"] = cleaned["structural_damage"]
        if "contamination_level" in cleaned and "contamination" not in cleaned:
            cleaned["contamination"] = cleaned["contamination_level"]
        if "carbon_disposal" in cleaned and "carbon_dispose" not in cleaned:
            cleaned["carbon_dispose"] = cleaned["carbon_disposal"]

        # Calculate completeness score based on presence of key fields
        key_fields = ["damage_level", "structural_condition", "cleanliness_score", "contamination", "safety_risk"]
        present_count = sum(1 for f in key_fields if cleaned.get(f) is not None and str(cleaned.get(f)).lower() != "nan")
        completeness = round(present_count / len(key_fields), 2)
        cleaned["inspection_completeness"] = completeness
        
        # If completeness is low, flag for human escalation
        if completeness < 0.8:
            flags.append("INCOMPLETE_INSPECTION_ESCALATION")

        cleaned["ingestion_flags"] = flags
        cleaned["is_fallback"] = len(flags) > 0
        
        return True, None, cleaned
