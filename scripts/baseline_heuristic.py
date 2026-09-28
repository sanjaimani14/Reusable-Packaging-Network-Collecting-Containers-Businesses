import os
import json
import argparse
import pandas as pd
import numpy as np

def run_baseline_heuristic(data_path: str = "data/synthetic/synthetic_containers.csv", output_path: str = "experiments/baseline_results.json"):
    """
    Executes a simple, transparent, and explainable Baseline Heuristic
    on the inspection dataset and computes measurable financial, operational,
    and environmental metrics.
    """
    if not os.path.exists(data_path):
        # Try alternate path
        alt_path = os.path.join("repackai", data_path)
        if os.path.exists(alt_path):
            data_path = alt_path
        else:
            raise FileNotFoundError(f"Inspection dataset not found at {data_path} or {alt_path}")
            
    df = pd.read_csv(data_path)
    print(f"Loaded {len(df)} records for Baseline Heuristic Evaluation from {data_path}")

    # Standardize column access
    records = []
    total_val = 0.0
    total_waste = 0.0
    total_carbon = 0.0
    safety_violations = 0
    human_reviews = 0
    
    action_counts = {
        "RESELL": 0,
        "REPAIR": 0,
        "REFURBISH": 0,
        "RECYCLE": 0,
        "DISPOSE": 0,
        "MANUAL_REVIEW": 0
    }

    # Material processing carbon rates for reference
    carbon_rates = {"Cardboard": 1.0, "Wood": 0.4, "Plastic": 2.6, "Metal": 5.5}
    recycle_cost_rates = {"Cardboard": 0.02, "Wood": 0.01, "Plastic": 0.05, "Metal": 0.10}

    for _, row in df.iterrows():
        # Read fields with fallback support
        damage = str(row.get("structural_damage", row.get("damage_level", "None"))).strip()
        struct_cond = str(row.get("structural_condition", damage)).strip()
        contamination = str(row.get("contamination_level", row.get("contamination", "None"))).strip()
        safety = str(row.get("safety_status", row.get("safety_risk", "Low"))).strip()
        completeness = float(row.get("inspection_completeness", 1.0)) if pd.notnull(row.get("inspection_completeness")) else 1.0
        
        repair_cost = float(row.get("repair_cost", 0.0))
        refurb_cost = float(row.get("refurbishment_cost", 0.0))
        resale_val = float(row.get("resale_value", 0.0))
        recycle_val = float(row.get("recycling_value", 0.0))
        disposal_cost = float(row.get("disposal_cost", 10.0))
        
        weight_kg = float(row.get("weight_kg", 5.0))
        material = str(row.get("material_type", row.get("material", "Plastic"))).strip()
        recyclable = bool(row.get("recyclable", True))
        
        c_repair = float(row.get("carbon_repair", weight_kg * 0.12 + 1.0))
        c_refurb = float(row.get("carbon_refurbish", weight_kg * 0.25 + 0.8))
        c_recycle = float(row.get("carbon_recycle", weight_kg * 0.8))
        c_dispose = float(row.get("carbon_disposal", row.get("carbon_dispose", weight_kg * 1.5)))
        c_resell = float(row.get("carbon_resell", weight_kg * 0.02))

        new_carbon = weight_kg * carbon_rates.get(material, 2.6)

        # Baseline Heuristic Decision Tree
        is_unsafe = (struct_cond in ["Unsafe", "Critical"]) or (safety == "High") or (contamination == "Hazardous")

        if completeness < 0.8:
            action = "MANUAL_REVIEW"
            human_reviews += 1
        elif is_unsafe:
            if recyclable and contamination != "Hazardous":
                action = "RECYCLE"
            else:
                action = "DISPOSE"
        elif damage in ["None", "Safe"] and repair_cost == 0.0 and resale_val > 0.0:
            action = "RESELL"
        elif repair_cost < resale_val and repair_cost > 0.0:
            action = "REPAIR"
        elif refurb_cost < resale_val and refurb_cost > 0.0:
            action = "REFURBISH"
        elif recyclable:
            action = "RECYCLE"
        else:
            action = "DISPOSE"

        action_counts[action] = action_counts.get(action, 0) + 1

        # Check safety violation
        if is_unsafe and action in ["RESELL", "REPAIR", "REFURBISH"]:
            safety_violations += 1

        # Accumulate metrics
        if action == "RESELL":
            net = resale_val
            waste = weight_kg
            carbon = new_carbon - c_resell
        elif action == "REPAIR":
            net = resale_val - repair_cost
            waste = weight_kg
            carbon = new_carbon - c_repair
        elif action == "REFURBISH":
            net = resale_val - refurb_cost
            waste = weight_kg
            carbon = new_carbon - c_refurb
        elif action == "RECYCLE":
            proc = weight_kg * recycle_cost_rates.get(material, 0.05)
            net = recycle_val - proc
            waste = weight_kg * 0.8
            carbon = (new_carbon * 0.8) - c_recycle
        elif action == "DISPOSE":
            net = -disposal_cost
            waste = 0.0
            carbon = -c_dispose
        else:  # MANUAL_REVIEW
            net = 0.0
            waste = 0.0
            carbon = 0.0

        total_val += net
        total_waste += waste
        total_carbon += carbon

    n = len(df)
    results = {
        "model_name": "Baseline Heuristic",
        "total_containers_evaluated": n,
        "disposition_distribution": action_counts,
        "value_recovered": round(total_val, 2),
        "waste_avoided_kg": round(total_waste, 2),
        "carbon_avoided_kg": round(total_carbon, 2),
        "safety_violations": safety_violations,
        "safety_compliance": round(1.0 - (safety_violations / n), 4),
        "human_review_rate": round(human_reviews / n, 4),
        "average_value_per_container": round(total_val / n, 2),
        "average_waste_diverted_per_container_kg": round(total_waste / n, 2)
    }

    # Save to experiments directory
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Baseline results saved to {output_path}")

    # Also mirror to root experiments if in repackai or vice versa
    if output_path.startswith("experiments/"):
        alt_out = os.path.join("repackai", output_path)
        try:
            os.makedirs(os.path.dirname(os.path.abspath(alt_out)), exist_ok=True)
            with open(alt_out, "w") as f:
                json.dump(results, f, indent=2)
        except Exception:
            pass

    print("\n=== BASELINE HEURISTIC PERFORMANCE SUMMARY ===")
    print(f"Total Evaluated: {n}")
    print(f"Value Recovered: INR {results['value_recovered']:,.2f}")
    print(f"Waste Avoided:   {results['waste_avoided_kg']:,.2f} kg")
    print(f"Carbon Avoided:  {results['carbon_avoided_kg']:,.2f} kg CO2e")
    print(f"Safety Violations: {results['safety_violations']} (Compliance: {results['safety_compliance']*100:.1f}%)")
    print(f"Human Review Rate: {results['human_review_rate']*100:.2f}%")
    print("Disposition Breakdown:")
    for k, v in action_counts.items():
        print(f"  - {k}: {v} ({v/n*100:.1f}%)")
    print("==============================================\n")
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Baseline Heuristic Evaluator")
    parser.add_argument("--data", type=str, default="data/synthetic/synthetic_containers.csv")
    parser.add_argument("--output", type=str, default="experiments/baseline_results.json")
    args = parser.parse_args()
    run_baseline_heuristic(data_path=args.data, output_path=args.output)
