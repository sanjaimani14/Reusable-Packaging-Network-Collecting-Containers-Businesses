from typing import List, Dict, Any
from pydantic import BaseModel, ConfigDict

class RuleResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    rule_name: str
    is_triggered: bool
    severity: str  # INFO, WARNING, CRITICAL
    explanation: str
    prohibited_actions: List[str]

class RuleEngine:
    """
    Deterministic rule engine implementing strict safety hard gates,
    contamination restrictions, material recycling constraints, and
    inspection completeness requirements.
    """
    
    @staticmethod
    def evaluate(inspection_data: Dict[str, Any], container_data: Dict[str, Any]) -> List[RuleResult]:
        results = []
        
        # 1. Structural condition & safety risk hard gate
        struct_cond = inspection_data.get("structural_condition")
        damage_lvl = inspection_data.get("damage_level")
        safety_risk = inspection_data.get("safety_risk")
        
        unsafe_triggered = (
            struct_cond in ["Unsafe", "Critical"] or
            damage_lvl in ["Critical", "High"] and struct_cond == "Unsafe" or
            safety_risk == "High" or
            struct_cond == "Unsafe"
        )
        results.append(RuleResult(
            rule_name="Safety Constraint (Structural & Risk)",
            is_triggered=bool(unsafe_triggered),
            severity="CRITICAL" if unsafe_triggered else "INFO",
            explanation="Unsafe structure or high safety risk detected. Prohibiting resale, repair, and refurbishment.",
            prohibited_actions=["RESELL", "REPAIR", "REFURBISH"] if unsafe_triggered else []
        ))
        
        # 2. Hazardous contamination rule
        contamination = inspection_data.get("contamination")
        if not contamination:
            contamination = inspection_data.get("contamination_level", "None")
        haz_triggered = (contamination == "Hazardous")
        results.append(RuleResult(
            rule_name="Contamination Constraint",
            is_triggered=haz_triggered,
            severity="CRITICAL" if haz_triggered else "INFO",
            explanation="Hazardous contamination prohibits standard handling (repair, refurbish, resell, recycle).",
            prohibited_actions=["RESELL", "REPAIR", "REFURBISH", "RECYCLE"] if haz_triggered else []
        ))
        
        # 3. Recyclable constraint rule
        recyclable = container_data.get("recyclable", True)
        recycle_prohibited = (not recyclable) or (contamination == "Hazardous")
        results.append(RuleResult(
            rule_name="Recycling Constraint",
            is_triggered=recycle_prohibited,
            severity="WARNING" if not recyclable else "INFO",
            explanation="Material is flagged as non-recyclable or contamination makes recycling impossible.",
            prohibited_actions=["RECYCLE"] if recycle_prohibited else []
        ))
        
        # 4. Inspection completeness rule
        completeness = inspection_data.get("inspection_completeness", 1.0)
        incomplete_triggered = (completeness is not None and float(completeness) < 0.8)
        results.append(RuleResult(
            rule_name="Completeness Constraint",
            is_triggered=incomplete_triggered,
            severity="WARNING" if incomplete_triggered else "INFO",
            explanation="Inspection details are incomplete (< 80%). Requires manual review escalation.",
            prohibited_actions=[]
        ))
        
        return results

    @staticmethod
    def get_prohibited_actions(rule_results: List[RuleResult]) -> List[str]:
        prohibited = set()
        for res in rule_results:
            if res.is_triggered:
                prohibited.update(res.prohibited_actions)
        return list(prohibited)

    @staticmethod
    def is_action_allowed(action: str, rule_results: List[RuleResult]) -> bool:
        prohibited = RuleEngine.get_prohibited_actions(rule_results)
        return action.upper() not in prohibited

    @staticmethod
    def requires_human_confirmation(inspection_data: Dict[str, Any], rule_results: List[RuleResult], selected_action: str) -> bool:
        # Require human confirmation if:
        # - Selected action is DISPOSE
        # - Selected action is MANUAL_REVIEW
        # - High safety risk or critical rule triggered
        # - Inspection completeness < 0.8
        # - High resale value items under uncertainty
        
        if selected_action in ["DISPOSE", "MANUAL_REVIEW"]:
            return True
            
        safety_risk = inspection_data.get("safety_risk")
        if safety_risk == "High":
            return True
            
        completeness = inspection_data.get("inspection_completeness", 1.0)
        if completeness is not None and float(completeness) < 0.8:
            return True
            
        for res in rule_results:
            if res.is_triggered and res.severity == "CRITICAL":
                return True
                
        return False
