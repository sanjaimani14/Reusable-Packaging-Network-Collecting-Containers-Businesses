import time
from typing import Dict, Any, List
import numpy as np

class EvaluationMetrics:
    """
    Computes rigorous evaluation metrics comparing Baseline heuristic
    versus Proposed multi-criteria recommendation engine.
    """

    @staticmethod
    def compute_value_recovered(actions: List[str], financial_breakdowns: List[Dict[str, Dict[str, float]]]) -> float:
        total = 0.0
        for act, fin in zip(actions, financial_breakdowns):
            if act not in ["MANUAL_REVIEW", "PENDING", "UNKNOWN"]:
                total += fin.get(act, {}).get("net_value", 0.0)
        return round(total, 2)

    @staticmethod
    def compute_waste_avoided(actions: List[str], environmental_breakdowns: List[Dict[str, Dict[str, float]]]) -> float:
        total = 0.0
        for act, env in zip(actions, environmental_breakdowns):
            if act not in ["MANUAL_REVIEW", "PENDING", "UNKNOWN"]:
                total += env.get(act, {}).get("waste_avoided_kg", 0.0)
        return round(total, 2)

    @staticmethod
    def compute_carbon_avoided(actions: List[str], environmental_breakdowns: List[Dict[str, Dict[str, float]]]) -> float:
        total = 0.0
        for act, env in zip(actions, environmental_breakdowns):
            if act not in ["MANUAL_REVIEW", "PENDING", "UNKNOWN"]:
                total += env.get(act, {}).get("carbon_avoided_kg", 0.0)
        return round(total, 2)

    @staticmethod
    def compute_safety_compliance(actions: List[str], prohibited_actions_list: List[List[str]]) -> float:
        """
        Safety Compliance = 1.0 - (Violations / Total).
        A violation occurs if a recommended action is in prohibited_actions (e.g. RESELL on Unsafe container).
        """
        if not actions:
            return 1.0
        violations = 0
        for act, prohibited in zip(actions, prohibited_actions_list):
            if act.upper() in [p.upper() for p in prohibited]:
                violations += 1
        return round(1.0 - (violations / len(actions)), 4)

    @staticmethod
    def compute_consistency(predictions_run_a: List[str], predictions_run_b: List[str]) -> float:
        """
        Measures recommendation consistency across identical repeated inputs.
        """
        if not predictions_run_a or len(predictions_run_a) != len(predictions_run_b):
            return 0.0
        matches = sum(1 for a, b in zip(predictions_run_a, predictions_run_b) if a == b)
        return round(matches / len(predictions_run_a), 4)

    @staticmethod
    def compute_human_review_rate(human_confirmation_flags: List[bool]) -> float:
        if not human_confirmation_flags:
            return 0.0
        return round(sum(1 for f in human_confirmation_flags if f) / len(human_confirmation_flags), 4)

    @staticmethod
    def compute_summary_table(
        baseline_metrics: Dict[str, Any],
        proposed_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generates a comparative summary table between baseline and proposed system.
        """
        val_delta = proposed_metrics["value_recovered"] - baseline_metrics["value_recovered"]
        waste_delta = proposed_metrics["waste_avoided_kg"] - baseline_metrics["waste_avoided_kg"]
        carbon_delta = proposed_metrics["carbon_avoided_kg"] - baseline_metrics["carbon_avoided_kg"]
        
        return {
            "baseline": baseline_metrics,
            "proposed": proposed_metrics,
            "improvements": {
                "additional_value_recovered": round(val_delta, 2),
                "additional_waste_avoided_kg": round(waste_delta, 2),
                "additional_carbon_avoided_kg": round(carbon_delta, 2),
                "safety_compliance_delta": round(proposed_metrics.get("safety_compliance", 1.0) - baseline_metrics.get("safety_compliance", 1.0), 4)
            }
        }
