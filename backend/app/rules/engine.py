from typing import List, Dict, Any
from pydantic import BaseModel

class RuleResult(BaseModel):
    rule_name: str
    is_triggered: bool
    severity: str  # INFO, WARNING, CRITICAL
    explanation: str
    prohibited_actions: List[str]

class RuleEngine:
    @staticmethod
    def evaluate(inspection_data: Dict[str, Any], container_data: Dict[str, Any]) -> List[RuleResult]:
        results = []
        
        # 1. Structural condition safety rule
        struct_cond = inspection_data.get("structural_condition")
        safety_risk = inspection_data.get("safety_risk")
        
        unsafe_triggered = (struct_cond == "Unsafe" or safety_risk == "High")
        results.append(RuleResult(
            rule_name="Safety Constraint (Structural & Risk)",
            is_triggered=unsafe_triggered,
            severity="CRITICAL" if unsafe_triggered else "INFO",
            explanation="Unsafe structure or high safety risk detected. Prohibiting resale, repair, and refurbishment.",
            prohibited_actions=["RESELL", "REPAIR", "REFURBISH"] if unsafe_triggered else []
        ))
        
        # 2. Hazardous contamination rule
        contamination = inspection_data.get("contamination")
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
        # Also check if contamination is hazardous, as it prevents recycling
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
        incomplete_triggered = (completeness < 0.8)
        results.append(RuleResult(
            rule_name="Completeness Constraint",
            is_triggered=incomplete_triggered,
            severity="WARNING" if incomplete_triggered else "INFO",
            explanation="Inspection details are incomplete (< 80%). Requires manual escalation.",
            prohibited_actions=[]  # Doesn't prohibit specific actions directly, but flags for escalation
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
    def requires_human_confirmation(inspection_data: Dict[str, Any], rule_results: List[RuleResult], selected_action: str) -> bool:
        # Require human confirmation if:
        # - Any critical rule is triggered
        # - Selected action is DISPOSE
        # - Safety risk is High
        # - Cleanliness score or damage level is missing (simulating completeness warning)
        # - Inspection completeness is < 0.8
        
        if selected_action == "DISPOSE":
            return True
            
        if selected_action == "MANUAL_REVIEW":
            return True
            
        safety_risk = inspection_data.get("safety_risk")
        if safety_risk == "High":
            return True
            
        completeness = inspection_data.get("inspection_completeness", 1.0)
        if completeness < 0.8:
            return True
            
        for res in rule_results:
            if res.is_triggered and res.severity == "CRITICAL":
                return True
                
        return False
