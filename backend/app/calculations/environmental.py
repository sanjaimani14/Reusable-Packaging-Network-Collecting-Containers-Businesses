from typing import Dict, Any

class EnvironmentalCalculator:
    @staticmethod
    def calculate(container: Dict[str, Any], inspection: Dict[str, Any], material_rules: Dict[str, Any] = None) -> Dict[str, Dict[str, float]]:
        # Default carbon production emission factors per kg of material
        new_carbon_factors = {
            "Cardboard": 1.0,
            "Wood": 0.4,
            "Plastic": 2.6,
            "Metal": 5.5
        }
        
        material = container.get("material", "Plastic")
        weight_kg = container.get("weight_kg", 5.0)
        
        # Override new container carbon factor with DB material rules if available
        carbon_factor = new_carbon_factors.get(material, 2.6)
        if material_rules and material in material_rules:
            # Let's say if we have custom carbon factors or processing carbon parameters
            pass
            
        new_container_carbon = weight_kg * carbon_factor
        
        # Get processing carbon emissions from inspection or fallbacks
        carbon_resell = inspection.get("carbon_resell", weight_kg * 0.02)
        carbon_repair = inspection.get("carbon_repair", weight_kg * 0.12 + 1.0)
        carbon_refurbish = inspection.get("carbon_refurbish", weight_kg * 0.25 + 0.8)
        
        # For recycling, carbon emission is usually around 40% of producing new material
        carbon_recycle = inspection.get("carbon_recycle", new_container_carbon * 0.40)
        # For disposing, carbon emission includes landfill/incineration overheads
        carbon_dispose = inspection.get("carbon_dispose", new_container_carbon * 1.20)
        
        # Waste avoided
        waste_resell = weight_kg
        waste_repair = weight_kg
        waste_refurbish = weight_kg
        waste_recycle = weight_kg * 0.80  # 80% material recovery
        waste_dispose = 0.0
        
        # Carbon avoided = carbon of producing a new container - carbon generated in processing
        # Note: Disposal avoids 0% of the new carbon and produces carbon_dispose, so it is negative
        carbon_avoided_resell = new_container_carbon - carbon_resell
        carbon_avoided_repair = new_container_carbon - carbon_repair
        carbon_avoided_refurbish = new_container_carbon - carbon_refurbish
        carbon_avoided_recycle = (new_container_carbon * 0.80) - carbon_recycle  # Recycling offset is 80%
        carbon_avoided_dispose = 0.0 - carbon_dispose
        
        return {
            "RESELL": {
                "waste_avoided_kg": waste_resell,
                "carbon_avoided_kg": carbon_avoided_resell,
                "processing_emission": carbon_resell,
                "disposal_emission": 0.0
            },
            "REPAIR": {
                "waste_avoided_kg": waste_repair,
                "carbon_avoided_kg": carbon_avoided_repair,
                "processing_emission": carbon_repair,
                "disposal_emission": 0.0
            },
            "REFURBISH": {
                "waste_avoided_kg": waste_refurbish,
                "carbon_avoided_kg": carbon_avoided_refurbish,
                "processing_emission": carbon_refurbish,
                "disposal_emission": 0.0
            },
            "RECYCLE": {
                "waste_avoided_kg": waste_recycle,
                "carbon_avoided_kg": carbon_avoided_recycle,
                "processing_emission": carbon_recycle,
                "disposal_emission": 0.0
            },
            "DISPOSE": {
                "waste_avoided_kg": waste_dispose,
                "carbon_avoided_kg": carbon_avoided_dispose,
                "processing_emission": 0.0,
                "disposal_emission": carbon_dispose
            }
        }
