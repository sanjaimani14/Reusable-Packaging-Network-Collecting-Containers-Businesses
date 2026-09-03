from typing import Dict, Any, List
from repackai.backend.app.config import settings
from repackai.backend.app.rules.engine import RuleEngine, RuleResult
from repackai.backend.app.calculations.financial import FinancialCalculator
from repackai.backend.app.calculations.environmental import EnvironmentalCalculator
from repackai.backend.app.services.ml_service import MLService

class RecommendationEngine:
    @staticmethod
    def generate_recommendation(
        container_data: Dict[str, Any],
        inspection_data: Dict[str, Any],
        material_rules: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        # 1. Evaluate Rule Engine
        rule_results = RuleEngine.evaluate(inspection_data, container_data)
        prohibited_actions = RuleEngine.get_prohibited_actions(rule_results)
        
        # 2. Financial Calculations
        financials = FinancialCalculator.calculate(container_data, inspection_data, material_rules)
        
        # 3. Environmental Calculations
        environmentals = EnvironmentalCalculator.calculate(container_data, inspection_data, material_rules)
        
        # 4. Normalize and calculate scores
        actions = ["RESELL", "REPAIR", "REFURBISH", "RECYCLE", "DISPOSE"]
        
        # Find min/max for normalization
        net_values = [financials[act]["net_value"] for act in actions]
        min_net = min(net_values)
        max_net = max(net_values)
        net_range = max_net - min_net if max_net != min_net else 1.0
        
        carbon_avoided_values = [environmentals[act]["carbon_avoided_kg"] for act in actions]
        min_carbon = min(carbon_avoided_values)
        max_carbon = max(carbon_avoided_values)
        carbon_range = max_carbon - min_carbon if max_carbon != min_carbon else 1.0
        
        # Reusability scores
        reusability_scores = {
            "RESELL": 1.0,
            "REPAIR": 0.8,
            "REFURBISH": 0.6,
            "RECYCLE": 0.2,
            "DISPOSE": 0.0
        }
        
        # Operational scores
        operational_scores = {
            "RESELL": 1.0,
            "DISPOSE": 0.9,
            "RECYCLE": 0.7,
            "REFURBISH": 0.5,
            "REPAIR": 0.4
        }
        
        # Get configured weights
        w_fin = settings.WEIGHT_FINANCIAL
        w_env = settings.WEIGHT_ENVIRONMENTAL
        w_re = settings.WEIGHT_REUSABILITY
        w_op = settings.WEIGHT_OPERATIONAL
        
        scored_actions = {}
        for action in actions:
            # Check if action is prohibited
            if action in prohibited_actions:
                scored_actions[action] = {
                    "financial_score": 0.0,
                    "environmental_score": 0.0,
                    "reusability_score": reusability_scores[action],
                    "operational_score": operational_scores[action],
                    "final_score": -1.0,
                    "prohibited": True
                }
                continue
                
            # Normalize
            fin_val = financials[action]["net_value"]
            fin_score = (fin_val - min_net) / net_range
            
            env_val = environmentals[action]["carbon_avoided_kg"]
            env_score = (env_val - min_carbon) / carbon_range
            
            final_score = (
                w_fin * fin_score +
                w_env * env_score +
                w_re * reusability_scores[action] +
                w_op * operational_scores[action]
            )
            
            scored_actions[action] = {
                "financial_score": round(fin_score, 4),
                "environmental_score": round(env_score, 4),
                "reusability_score": reusability_scores[action],
                "operational_score": operational_scores[action],
                "final_score": round(final_score, 4),
                "prohibited": False
            }
            
        # 5. Run ML Model Prediction for alignment/confidence validation
        ml_action, ml_confidence = MLService.predict(container_data, inspection_data)
        ml_action_upper = ml_action.upper()
        
        # 6. Select recommended action
        # Exclude prohibited actions and pick highest final_score
        allowed_scores = {act: scored_actions[act]["final_score"] for act in actions if not scored_actions[act]["prohibited"]}
        
        if not allowed_scores:
            # If all are prohibited (extreme corner case), default to DISPOSE as safest action
            recommended_action = "DISPOSE"
            recommendation_score = 0.0
        else:
            recommended_action = max(allowed_scores, key=allowed_scores.get)
            recommendation_score = allowed_scores[recommended_action]
            
        # Completeness override
        completeness = inspection_data.get("inspection_completeness", 1.0)
        if completeness < 0.8:
            recommended_action = "MANUAL_REVIEW"
            recommendation_score = 0.0
            
        # Determine confidence: hybrid score combining ML confidence and score margin
        # If recommended action matches ML prediction, boost confidence, else discount it
        if ml_action_upper == recommended_action:
            confidence = round(0.7 * ml_confidence + 0.3 * recommendation_score, 2)
        else:
            confidence = round(0.5 * ml_confidence, 2)
            
        if recommended_action == "MANUAL_REVIEW":
            confidence = 0.0
            
        # Ensure confidence is within [0.0, 1.0]
        confidence = float(max(0.0, min(1.0, confidence)))
        
        # 7. Formulate explanations and reasons
        fin_reason = (
            f"Expected Net Value: ₹{financials.get(recommended_action, {}).get('net_value', 0.0):.2f}. "
            f"Processing Cost: ₹{financials.get(recommended_action, {}).get('processing_cost', 0.0):.2f}."
        )
        env_reason = (
            f"Carbon Avoided: {environmentals.get(recommended_action, {}).get('carbon_avoided_kg', 0.0):.2f} kg. "
            f"Waste Avoided: {environmentals.get(recommended_action, {}).get('waste_avoided_kg', 0.0):.2f} kg."
        )
        
        safety_reason = "No critical safety triggers."
        triggered_rules_names = []
        for r in rule_results:
            if r.is_triggered:
                triggered_rules_names.append(r.rule_name)
                if r.severity == "CRITICAL":
                    safety_reason = r.explanation
                    
        # Check human confirmation triggers
        requires_human = RuleEngine.requires_human_confirmation(inspection_data, rule_results, recommended_action)
        if confidence < 0.6 and recommended_action != "MANUAL_REVIEW":
            requires_human = True
            
        # Alternative actions (sorted descending by score)
        alternatives = []
        for act in actions:
            if act != recommended_action and not scored_actions[act]["prohibited"]:
                alternatives.append({
                    "action": act,
                    "score": scored_actions[act]["final_score"],
                    "net_value": financials[act]["net_value"]
                })
        alternatives.sort(key=lambda x: x["score"], reverse=True)
        
        # Compile evidence evidence JSON
        evidence = {
            "financial_breakdown": financials,
            "environmental_breakdown": environmentals,
            "score_breakdown": scored_actions,
            "ml_prediction": {
                "action": ml_action,
                "confidence": ml_confidence
            }
        }
        
        return {
            "recommended_action": recommended_action,
            "confidence": confidence,
            "score": recommendation_score,
            "alternative_actions": alternatives,
            "rules_triggered": triggered_rules_names,
            "evidence": evidence,
            "financial_reason": fin_reason,
            "environmental_reason": env_reason,
            "safety_reason": safety_reason,
            "requires_human_confirmation": requires_human
        }
