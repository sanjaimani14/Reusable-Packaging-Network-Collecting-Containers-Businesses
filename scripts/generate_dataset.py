import os
import random
import numpy as np
import pandas as pd

def generate_synthetic_data(num_records=5500, output_path="data/synthetic/synthetic_containers.csv"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Set random seeds for reproducibility
    random.seed(42)
    np.random.seed(42)
    
    container_types = ["Box", "Pallet", "Crate", "Drum", "Tote"]
    materials_by_type = {
        "Box": ["Cardboard", "Plastic"],
        "Pallet": ["Wood", "Plastic"],
        "Crate": ["Wood", "Plastic", "Metal"],
        "Drum": ["Metal", "Plastic"],
        "Tote": ["Plastic"]
    }
    
    locations = ["Warehouse A", "Hub B", "Depot C", "Facility D", "Terminal E"]
    
    records = []
    
    for i in range(num_records):
        container_id = f"CON-{100000 + i}"
        container_type = random.choice(container_types)
        material = random.choice(materials_by_type[container_type])
        
        # Determine weight based on type and material
        base_weights = {
            "Cardboard": 1.5,
            "Wood": 20.0,
            "Plastic": 6.0,
            "Metal": 30.0
        }
        weight_kg = base_weights[material] * random.uniform(0.8, 1.2)
        
        # Age and usage
        age_months = random.randint(1, 60)
        # Higher age tends to mean more usage
        usage_count = int(age_months * random.uniform(0.5, 3.5))
        
        # Damage level
        # Higher usage count increases probability of higher damage level
        damage_prob = [0.4, 0.3, 0.2, 0.08, 0.02] # None, Low, Medium, High, Critical
        if usage_count > 100:
            damage_prob = [0.05, 0.15, 0.35, 0.30, 0.15]
        elif usage_count > 50:
            damage_prob = [0.15, 0.25, 0.35, 0.20, 0.05]
            
        damage_level = np.random.choice(["None", "Low", "Medium", "High", "Critical"], p=damage_prob)
        
        # Structural condition correlates with damage level
        struct_map = {
            "None": ["Safe"],
            "Low": ["Safe", "Minor Damage"],
            "Medium": ["Minor Damage", "Moderate Damage"],
            "High": ["Moderate Damage", "Unsafe"],
            "Critical": ["Unsafe"]
        }
        structural_condition = random.choice(struct_map[damage_level])
        
        # Cleanliness score
        cleanliness_score = float(np.clip(100.0 - usage_count * 0.2 - random.uniform(0, 30), 0.0, 100.0))
        
        # Contamination
        contamination_prob = [0.85, 0.08, 0.05, 0.02] # None, Organic, Chemical, Hazardous
        contamination = np.random.choice(["None", "Organic", "Chemical", "Hazardous"], p=contamination_prob)
        
        # Safety risk
        if structural_condition == "Unsafe" or contamination == "Hazardous":
            safety_risk = "High"
        elif damage_level in ["High", "Medium"] or contamination == "Chemical":
            safety_risk = "Medium"
        else:
            safety_risk = "Low"
            
        # Recyclable status
        recyclable = material in ["Cardboard", "Plastic", "Metal"]
        if contamination == "Hazardous":
            recyclable = False # Hazardous contamination ruins recyclability
            
        # Costs and replacement value (base reference)
        base_replacement_values = {
            "Box": 15.0,
            "Tote": 40.0,
            "Pallet": 50.0,
            "Crate": 80.0,
            "Drum": 120.0
        }
        base_val = base_replacement_values[container_type]
        
        # Resale value decreases with age and usage
        resale_val_factor = max(0.1, 1.0 - (age_months / 60.0) * 0.6 - (usage_count / 150.0) * 0.3)
        resale_value = round(base_val * resale_val_factor * random.uniform(0.9, 1.1), 2)
        
        # If safety risk is High or structural condition is Unsafe, resale value drops to 0
        if safety_risk == "High" or structural_condition == "Unsafe":
            resale_value = 0.0
            
        # Repair required and cost
        repair_required = damage_level not in ["None", "Low"]
        if damage_level == "None":
            repair_cost = 0.0
        elif damage_level == "Low":
            repair_cost = round(base_val * 0.05 * random.uniform(0.8, 1.2), 2)
        elif damage_level == "Medium":
            repair_cost = round(base_val * 0.20 * random.uniform(0.8, 1.2), 2)
        elif damage_level == "High":
            repair_cost = round(base_val * 0.45 * random.uniform(0.8, 1.2), 2)
        else: # Critical
            repair_cost = round(base_val * 0.85 * random.uniform(0.8, 1.2), 2)
            
        # Refurbishment cost: cleaning + age wear
        refurbishment_cost = round((base_val * 0.15) + (100.0 - cleanliness_score) * 0.15 + (usage_count * 0.1), 2)
        
        # Recycling value
        recycling_rates = {
            "Cardboard": 0.08,
            "Plastic": 0.20,
            "Metal": 0.50,
            "Wood": 0.03
        }
        if recyclable:
            recycling_value = round(weight_kg * recycling_rates[material] * random.uniform(0.9, 1.1), 2)
        else:
            recycling_value = 0.0
            
        # Disposal cost
        base_disposal = 5.0 + weight_kg * 0.25
        if contamination == "Hazardous":
            disposal_cost = round(base_disposal * 6.0, 2)
        elif contamination == "Chemical":
            disposal_cost = round(base_disposal * 2.5, 2)
        else:
            disposal_cost = round(base_disposal, 2)
            
        # Carbon emissions per material (kg CO2 / kg material)
        material_carbon_factor = {
            "Cardboard": 1.0,
            "Wood": 0.4,
            "Plastic": 2.6,
            "Metal": 5.5
        }
        new_carbon = weight_kg * material_carbon_factor[material]
        
        # Carbon footprint of each disposition
        carbon_resell = round(weight_kg * 0.02, 2)
        carbon_repair = round(weight_kg * 0.12 + (0.5 if damage_level == "Medium" else 1.5 if damage_level == "High" else 3.0), 2)
        carbon_refurbish = round(weight_kg * 0.25 + 0.8, 2)
        carbon_recycle = round(new_carbon * 0.4, 2) # recycle saves 60% compared to new
        carbon_dispose = round(new_carbon * 1.2, 2) # landfill emissions + overhead
        
        # Location and network configuration
        location = random.choice(locations)
        sensor_available = random.choice([True, True, True, False]) # 75% True
        network_available = random.choice([True, True, True, True, False]) # 80% True
        
        # Missing values (edge cases)
        # 3% of inspections are missing some fields (completeness score < 1.0)
        inspection_completeness = 1.0
        if random.random() < 0.03:
            inspection_completeness = round(random.uniform(0.5, 0.9), 2)
            
        # Determine final disposition label using a deterministic helper rule to mimic recommendation logic
        # 1. Check Safety and Contamination
        is_unsafe = (structural_condition == "Unsafe") or (safety_risk == "High") or (contamination == "Hazardous")
        
        if inspection_completeness < 0.8:
            final_disposition = "Manual_Review"
        elif is_unsafe:
            if recyclable:
                final_disposition = "Recycle"
            else:
                final_disposition = "Dispose"
        else:
            # Evaluate financial net recovery
            # Resell net: resale_value
            # Repair net: resale_value - repair_cost
            # Refurbish net: resale_value - refurbishment_cost
            # Recycle net: recycling_value - (weight_kg * 0.05)
            # Dispose net: -disposal_cost
            
            nets = {
                "Resell": resale_value,
                "Repair": resale_value - repair_cost,
                "Refurbish": resale_value - refurbishment_cost,
                "Recycle": recycling_value - (weight_kg * 0.05),
                "Dispose": -disposal_cost
            }
            
            # Incorporate carbon avoided in scoring:
            # carbon_avoided = new_carbon - processing_emission
            # higher carbon avoided = better environmental score
            carbon_avoided = {
                "Resell": new_carbon - carbon_resell,
                "Repair": new_carbon - carbon_repair,
                "Refurbish": new_carbon - carbon_refurbish,
                "Recycle": (new_carbon * 0.8) - carbon_recycle,
                "Dispose": -carbon_dispose
            }
            
            # Reusability score: Resell (1.0), Repair (0.8), Refurbish (0.6), Recycle (0.2), Dispose (0.0)
            reusability = {
                "Resell": 1.0,
                "Repair": 0.8,
                "Refurbish": 0.6,
                "Recycle": 0.2,
                "Dispose": 0.0
            }
            
            # Let's compute composite scores to choose:
            # Let's normalize nets first.
            max_net = max(nets.values())
            min_net = min(nets.values())
            net_range = max_net - min_net if max_net != min_net else 1.0
            
            max_carbon = max(carbon_avoided.values())
            min_carbon = min(carbon_avoided.values())
            carbon_range = max_carbon - min_carbon if max_carbon != min_carbon else 1.0
            
            scores = {}
            for action in nets.keys():
                fin_score = (nets[action] - min_net) / net_range
                env_score = (carbon_avoided[action] - min_carbon) / carbon_range
                re_score = reusability[action]
                
                # Composite
                scores[action] = 0.40 * fin_score + 0.30 * env_score + 0.20 * re_score + 0.10 * 0.8
                
            # Pick highest score
            best_action = max(scores, key=scores.get)
            
            # Add some minor noise to training labels to make it interesting
            if random.random() < 0.02:
                valid_options = ["Resell", "Repair", "Refurbish", "Recycle", "Dispose"]
                if recyclable:
                    best_action = random.choice(valid_options)
                else:
                    best_action = random.choice(["Resell", "Repair", "Refurbish", "Dispose"])
                    
            final_disposition = best_action

        records.append({
            "container_id": container_id,
            "container_type": container_type,
            "material": material,
            "weight_kg": round(weight_kg, 2),
            "age_months": age_months,
            "usage_count": usage_count,
            "damage_level": damage_level,
            "structural_condition": structural_condition,
            "cleanliness_score": round(cleanliness_score, 2),
            "contamination": contamination,
            "repair_required": repair_required,
            "repair_cost": repair_cost,
            "refurbishment_cost": refurbishment_cost,
            "resale_value": resale_value,
            "recycling_value": recycling_value,
            "disposal_cost": disposal_cost,
            "carbon_repair": carbon_repair,
            "carbon_refurbish": carbon_refurbish,
            "carbon_resell": carbon_resell,
            "carbon_recycle": carbon_recycle,
            "carbon_dispose": carbon_dispose,
            "recyclable": recyclable,
            "safety_risk": safety_risk,
            "location": location,
            "sensor_available": sensor_available,
            "network_available": network_available,
            "inspection_completeness": inspection_completeness,
            "final_disposition": final_disposition
        })
        
    df = pd.DataFrame(records)
    
    # Introduce controlled missing values in inspection data to simulate edge cases in testing
    # But keep final_disposition filled
    for col in ["cleanliness_score", "damage_level", "structural_condition"]:
        mask = np.random.rand(len(df)) < 0.01 # 1% missing values
        df.loc[mask, col] = np.nan
        
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} records at {output_path}")

if __name__ == "__main__":
    generate_synthetic_data()
