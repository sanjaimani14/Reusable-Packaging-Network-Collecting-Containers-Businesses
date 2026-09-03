from typing import Dict, Any

class FinancialCalculator:
    @staticmethod
    def calculate(container: Dict[str, Any], inspection: Dict[str, Any], material_rules: Dict[str, Any] = None) -> Dict[str, Dict[str, float]]:
        # Material processing costs per kg fallbacks
        processing_costs_per_kg = {
            "Cardboard": 0.02,
            "Plastic": 0.05,
            "Metal": 0.10,
            "Wood": 0.01
        }
        
        material = container.get("material", "Plastic")
        weight_kg = container.get("weight_kg", 5.0)
        
        # Override processing cost with DB material rules if available
        mat_proc_cost_rate = processing_costs_per_kg.get(material, 0.05)
        if material_rules and material in material_rules:
            mat_proc_cost_rate = material_rules[material].get("processing_cost_per_kg", mat_proc_cost_rate)
            
        recycle_processing_cost = weight_kg * mat_proc_cost_rate
        
        resale_value = inspection.get("resale_value", 0.0)
        repair_cost = inspection.get("repair_cost", 0.0)
        refurbishment_cost = inspection.get("refurbishment_cost", 0.0)
        recycling_value = inspection.get("recycling_value", 0.0)
        disposal_cost = inspection.get("disposal_cost", 10.0)
        
        # Financial breakdown for each action
        # Net value = recovery - cost
        
        resell_net = resale_value
        repair_net = resale_value - repair_cost
        refurbish_net = resale_value - refurbishment_cost
        recycle_net = recycling_value - recycle_processing_cost
        dispose_net = -disposal_cost
        
        return {
            "RESELL": {
                "expected_recovery": resale_value,
                "processing_cost": 0.0,
                "net_value": resell_net
            },
            "REPAIR": {
                "expected_recovery": resale_value,
                "processing_cost": repair_cost,
                "net_value": repair_net
            },
            "REFURBISH": {
                "expected_recovery": resale_value,
                "processing_cost": refurbishment_cost,
                "net_value": refurbish_net
            },
            "RECYCLE": {
                "expected_recovery": recycling_value,
                "processing_cost": recycle_processing_cost,
                "net_value": recycle_net
            },
            "DISPOSE": {
                "expected_recovery": 0.0,
                "processing_cost": disposal_cost,
                "net_value": dispose_net
            }
        }
Definition = "Financial Calculator formulas for RePackAI."
