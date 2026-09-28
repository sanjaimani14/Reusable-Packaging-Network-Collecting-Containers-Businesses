import os
import argparse
import random
import datetime
import numpy as np
import pandas as pd

def generate_synthetic_data(num_records: int = 5500, output_path: str = "data/synthetic/synthetic_containers.csv", seed: int = 42):
    """
    Generates a realistic, reproducible synthetic dataset for reusable packaging network disposition.
    Supports configurable dataset size and random seed.
    Includes all core and extended fields required by the problem statement and review improvements.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    random.seed(seed)
    np.random.seed(seed)
    
    container_types = ["Box", "Pallet", "Crate", "Drum", "Tote"]
    materials_by_type = {
        "Box": ["Cardboard", "Plastic"],
        "Pallet": ["Wood", "Plastic"],
        "Crate": ["Wood", "Plastic", "Metal"],
        "Drum": ["Metal", "Plastic"],
        "Tote": ["Plastic"]
    }
    
    material_content_desc = {
        "Cardboard": "100% Recycled Corrugated Board",
        "Wood": "Heat-Treated Pine Timber",
        "Plastic": "High-Density Polyethylene (HDPE)",
        "Metal": "Industrial Galvanized Cold-Rolled Steel"
    }
    
    locations = ["Warehouse A", "Hub B", "Depot C", "Facility D", "Terminal E"]
    
    records = []
    base_date = datetime.datetime(2026, 1, 1)
    
    for i in range(num_records):
        container_id = f"CON-{100000 + i}"
        container_type = random.choice(container_types)
        material = random.choice(materials_by_type[container_type])
        material_content = material_content_desc[material]
        
        # Base weights per material
        base_weights = {
            "Cardboard": 1.5,
            "Wood": 20.0,
            "Plastic": 6.0,
            "Metal": 30.0
        }
        weight_kg = round(base_weights[material] * random.uniform(0.85, 1.15), 2)
        
        age_months = random.randint(1, 60)
        usage_count = int(age_months * random.uniform(0.5, 3.5))
        
        # Inspection date staggered over past 180 days
        inspection_date = (base_date + datetime.timedelta(days=random.randint(0, 180), hours=random.randint(0, 23))).strftime("%Y-%m-%d %H:%M:%S")
        
        # Structural damage & cosmetic damage
        damage_prob = [0.4, 0.3, 0.2, 0.08, 0.02]
        if usage_count > 100:
            damage_prob = [0.05, 0.15, 0.35, 0.30, 0.15]
        elif usage_count > 50:
            damage_prob = [0.15, 0.25, 0.35, 0.20, 0.05]
            
        damage_level = np.random.choice(["None", "Low", "Medium", "High", "Critical"], p=damage_prob)
        
        struct_map = {
            "None": ["Safe"],
            "Low": ["Safe", "Minor Damage"],
            "Medium": ["Minor Damage", "Moderate Damage"],
            "High": ["Moderate Damage", "Unsafe"],
            "Critical": ["Unsafe"]
        }
        structural_damage = random.choice(struct_map[damage_level])
        structural_condition = structural_damage
        
        cosmetic_prob = [0.35, 0.40, 0.20, 0.05]
        cosmetic_damage = np.random.choice(["None", "Scratches", "Dents", "Discoloration"], p=cosmetic_prob)
        
        # Cleanliness / Inspection score
        cleanliness_score = float(np.clip(100.0 - usage_count * 0.2 - random.uniform(0, 25), 10.0, 100.0))
        inspection_score = round(cleanliness_score, 1)
        
        # Contamination level
        contamination_prob = [0.85, 0.08, 0.05, 0.02]  # None, Organic, Chemical, Hazardous
        contamination_level = np.random.choice(["None", "Organic", "Chemical", "Hazardous"], p=contamination_prob)
        contamination = contamination_level
        
        # Safety status
        if structural_damage == "Unsafe" or contamination_level == "Hazardous":
            safety_status = "High"
        elif damage_level in ["High", "Medium"] or contamination_level == "Chemical":
            safety_status = "Medium"
        else:
            safety_status = "Low"
        safety_risk = safety_status
        
        recyclable = (material in ["Cardboard", "Plastic", "Metal"]) and (contamination_level != "Hazardous")
        
        base_replacement_values = {
            "Box": 15.0,
            "Tote": 40.0,
            "Pallet": 50.0,
            "Crate": 80.0,
            "Drum": 120.0
        }
        base_val = base_replacement_values[container_type]
        
        resale_val_factor = max(0.1, 1.0 - (age_months / 60.0) * 0.6 - (usage_count / 150.0) * 0.3)
        resale_value = round(base_val * resale_val_factor * random.uniform(0.9, 1.1), 2)
        if safety_status == "High" or structural_damage == "Unsafe":
            resale_value = 0.0
            
        repair_required = damage_level not in ["None", "Low"]
        if damage_level == "None":
            repair_cost = 0.0
        elif damage_level == "Low":
            repair_cost = round(base_val * 0.05 * random.uniform(0.8, 1.2), 2)
        elif damage_level == "Medium":
            repair_cost = round(base_val * 0.20 * random.uniform(0.8, 1.2), 2)
        elif damage_level == "High":
            repair_cost = round(base_val * 0.45 * random.uniform(0.8, 1.2), 2)
        else:
            repair_cost = round(base_val * 0.85 * random.uniform(0.8, 1.2), 2)
            
        refurbishment_cost = round((base_val * 0.15) + (100.0 - inspection_score) * 0.15 + (usage_count * 0.08), 2)
        
        recycling_rates = {
            "Cardboard": 0.08,
            "Plastic": 0.20,
            "Metal": 0.50,
            "Wood": 0.03
        }
        recycling_value = round(weight_kg * recycling_rates[material] * random.uniform(0.9, 1.1), 2) if recyclable else 0.0
        
        base_disposal = 5.0 + weight_kg * 0.25
        if contamination_level == "Hazardous":
            disposal_cost = round(base_disposal * 6.0, 2)
        elif contamination_level == "Chemical":
            disposal_cost = round(base_disposal * 2.5, 2)
        else:
            disposal_cost = round(base_disposal, 2)
            
        material_carbon_factor = {
            "Cardboard": 1.0,
            "Wood": 0.4,
            "Plastic": 2.6,
            "Metal": 5.5
        }
        new_carbon = weight_kg * material_carbon_factor[material]
        
        carbon_resell = round(weight_kg * 0.02, 2)
        carbon_repair = round(weight_kg * 0.12 + (0.5 if damage_level == "Medium" else 1.5 if damage_level == "High" else 3.0), 2)
        carbon_refurbish = round(weight_kg * 0.25 + 0.8, 2)
        carbon_recycle = round(new_carbon * 0.4, 2)
        carbon_disposal = round(new_carbon * 1.2, 2)
        carbon_dispose = carbon_disposal
        
        location = random.choice(locations)
        sensor_available = random.choice([True, True, True, False])
        network_available = random.choice([True, True, True, True, False])
        
        inspection_completeness = 1.0
        if random.random() < 0.03:
            inspection_completeness = round(random.uniform(0.5, 0.85), 2)
            
        # Disposition calculation for training labels
        is_unsafe = (structural_damage == "Unsafe") or (safety_status == "High") or (contamination_level == "Hazardous")
        
        if inspection_completeness < 0.8:
            recommended_disposition = "Manual_Review"
        elif is_unsafe:
            if recyclable:
                recommended_disposition = "Recycle"
            else:
                recommended_disposition = "Dispose"
        else:
            nets = {
                "Resell": resale_value,
                "Repair": resale_value - repair_cost,
                "Refurbish": resale_value - refurbishment_cost,
                "Recycle": recycling_value - (weight_kg * 0.05),
                "Dispose": -disposal_cost
            }
            carbon_avoided = {
                "Resell": new_carbon - carbon_resell,
                "Repair": new_carbon - carbon_repair,
                "Refurbish": new_carbon - carbon_refurbish,
                "Recycle": (new_carbon * 0.8) - carbon_recycle,
                "Dispose": -carbon_disposal
            }
            reusability = {
                "Resell": 1.0,
                "Repair": 0.8,
                "Refurbish": 0.6,
                "Recycle": 0.2,
                "Dispose": 0.0
            }
            
            max_net = max(nets.values())
            min_net = min(nets.values())
            net_range = max_net - min_net if max_net != min_net else 1.0
            
            max_carbon = max(carbon_avoided.values())
            min_carbon = min(carbon_avoided.values())
            carbon_range = max_carbon - min_carbon if max_carbon != min_carbon else 1.0
            
            scores = {}
            for act in nets.keys():
                fin_score = (nets[act] - min_net) / net_range
                env_score = (carbon_avoided[act] - min_carbon) / carbon_range
                re_score = reusability[act]
                scores[act] = 0.40 * fin_score + 0.30 * env_score + 0.20 * re_score + 0.10 * 0.8
                
            recommended_disposition = max(scores, key=scores.get)
            
        final_disposition = recommended_disposition

        records.append({
            # Requested Schema Fields
            "container_id": container_id,
            "inspection_date": inspection_date,
            "material_type": material,
            "container_type": container_type,
            "structural_damage": structural_damage,
            "cosmetic_damage": cosmetic_damage,
            "contamination_level": contamination_level,
            "repair_cost": repair_cost,
            "resale_value": resale_value,
            "refurbishment_cost": refurbishment_cost,
            "recycling_value": recycling_value,
            "disposal_cost": disposal_cost,
            "carbon_repair": carbon_repair,
            "carbon_refurbish": carbon_refurbish,
            "carbon_recycle": carbon_recycle,
            "carbon_disposal": carbon_disposal,
            "weight_kg": weight_kg,
            "material_content": material_content,
            "safety_status": safety_status,
            "inspection_score": inspection_score,
            "location": location,
            "sensor_available": sensor_available,
            "network_available": network_available,
            "recommended_disposition": recommended_disposition,
            
            # Backward-Compatibility Aliases
            "material": material,
            "damage_level": damage_level,
            "structural_condition": structural_condition,
            "cleanliness_score": inspection_score,
            "contamination": contamination,
            "safety_risk": safety_status,
            "carbon_dispose": carbon_disposal,
            "carbon_resell": carbon_resell,
            "final_disposition": final_disposition,
            "age_months": age_months,
            "usage_count": usage_count,
            "repair_required": repair_required,
            "recyclable": recyclable,
            "inspection_completeness": inspection_completeness
        })

    df = pd.DataFrame(records)
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} records at {output_path} (seed={seed})")
    return df

def main():
    parser = argparse.ArgumentParser(description="Synthetic Reusable Packaging Data Generator")
    parser.add_argument("--rows", type=int, default=5500, help="Number of records to generate")
    parser.add_argument("--seed", type=int, default=42, help="Fixed random seed for reproducibility")
    parser.add_argument("--output", type=str, default="data/synthetic/synthetic_containers.csv", help="Output file path")
    args = parser.parse_args()
    
    generate_synthetic_data(num_records=args.rows, output_path=args.output, seed=args.seed)

if __name__ == "__main__":
    main()
