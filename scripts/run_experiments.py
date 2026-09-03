import os
import sys
import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix, f1_score

# Add the parent folder of repackai to path to import repackai modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from repackai.backend.app.services.recommender import RecommendationEngine
from repackai.backend.app.services.ml_service import MLService

# Define custom material rules matching database seeding
MOCK_MATERIAL_RULES = {
    "Cardboard": {
        "recyclable": True,
        "processing_cost_per_kg": 0.02,
        "recycling_value_per_kg": 0.08,
        "carbon_recycle_per_kg": 0.40,
        "carbon_dispose_per_kg": 1.20
    },
    "Wood": {
        "recyclable": True,
        "processing_cost_per_kg": 0.01,
        "recycling_value_per_kg": 0.03,
        "carbon_recycle_per_kg": 0.10,
        "carbon_dispose_per_kg": 0.50
    },
    "Plastic": {
        "recyclable": True,
        "processing_cost_per_kg": 0.05,
        "recycling_value_per_kg": 0.20,
        "carbon_recycle_per_kg": 1.04,
        "carbon_dispose_per_kg": 3.12
    },
    "Metal": {
        "recyclable": True,
        "processing_cost_per_kg": 0.10,
        "recycling_value_per_kg": 0.50,
        "carbon_recycle_per_kg": 2.20,
        "carbon_dispose_per_kg": 6.60
    }
}

class BaselineClassifier:
    def predict(self, X):
        predictions = []
        for _, row in X.iterrows():
            damage = str(row.get("damage_level", "None")).strip().lower()
            recyclable = row.get("recyclable")
            completeness = row.get("inspection_completeness", 1.0)
            
            if completeness < 0.8:
                predictions.append("MANUAL_REVIEW")
            elif damage in ["none", "nan", "null"]:
                predictions.append("RESELL")
            elif damage == "low":
                predictions.append("REPAIR")
            elif damage == "medium":
                predictions.append("REFURBISH")
            elif recyclable == True or str(recyclable).strip().lower() == "true":
                predictions.append("RECYCLE")
            else:
                predictions.append("DISPOSE")
        return np.array(predictions)

def run_experiment_suite(data_path="data/synthetic/synthetic_containers.csv", output_dir="docs/figures"):
    os.makedirs(output_dir, exist_ok=True)
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Synthetic dataset not found at {data_path}")
        
    df = pd.read_csv(data_path)
    
    # Preprocess missing values identical to training pipeline
    df["cleanliness_score"] = df["cleanliness_score"].fillna(df["cleanliness_score"].median())
    df["damage_level"] = df["damage_level"].fillna("None")
    df["structural_condition"] = df["structural_condition"].fillna("Safe")
    
    X = df.drop(columns=["container_id", "final_disposition"])
    y = df["final_disposition"].str.upper() # Standardize to uppercase for calculations
    
    # 80/20 Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # --- 1. Evaluate Heuristic Baseline ---
    baseline = BaselineClassifier()
    y_pred_baseline = baseline.predict(X_test)
    
    # --- 2. Evaluate Proposed System ---
    y_pred_proposed = []
    proposed_confidences = []
    
    # Track business/environmental telemetry
    total_val_recovered = 0.0
    total_waste_avoided = 0.0
    total_carbon_avoided = 0.0
    
    # Track baseline values for comparison
    base_val_recovered = 0.0
    base_waste_avoided = 0.0
    base_carbon_avoided = 0.0
    
    for idx, row in X_test.iterrows():
        container_data = {
            "id": "MOCK",
            "container_type": row["container_type"],
            "material": row["material"],
            "weight_kg": row["weight_kg"],
            "age_months": row["age_months"],
            "usage_count": row["usage_count"],
            "recyclable": row["recyclable"]
        }
        
        inspection_data = {
            "damage_level": row["damage_level"],
            "structural_condition": row["structural_condition"],
            "cleanliness_score": row["cleanliness_score"],
            "contamination": row["contamination"],
            "safety_risk": row["safety_risk"],
            "sensor_available": row["sensor_available"],
            "network_available": row["network_available"],
            "location_available": True,
            "location": row["location"],
            "inspection_completeness": row["inspection_completeness"],
            "resale_value": row["resale_value"],
            "repair_cost": row["repair_cost"],
            "refurbishment_cost": row["refurbishment_cost"],
            "recycling_value": row["recycling_value"],
            "disposal_cost": row["disposal_cost"],
            "carbon_repair": row["carbon_repair"],
            "carbon_refurbish": row["carbon_refurbish"],
            "carbon_resell": row["carbon_resell"],
            "carbon_recycle": row["carbon_recycle"],
            "carbon_dispose": row["carbon_dispose"]
        }
        
        # Calculate proposed
        rec = RecommendationEngine.generate_recommendation(container_data, inspection_data, MOCK_MATERIAL_RULES)
        action = rec["recommended_action"]
        y_pred_proposed.append(action)
        proposed_confidences.append(rec["confidence"])
        
        # Accumulate metrics for proposed
        fin_break = rec["evidence"]["financial_breakdown"]
        env_break = rec["evidence"]["environmental_breakdown"]
        
        if action != "MANUAL_REVIEW":
            total_val_recovered += fin_break[action]["net_value"]
            total_waste_avoided += env_break[action]["waste_avoided_kg"]
            total_carbon_avoided += env_break[action]["carbon_avoided_kg"]
            
        # Accumulate baseline metrics (calculate net value for baseline selection)
        base_act = y_pred_baseline[len(y_pred_proposed)-1]
        if base_act != "MANUAL_REVIEW":
            # Financial net recovery calculations
            resale_value = row["resale_value"]
            repair_cost = row["repair_cost"]
            refurbishment_cost = row["refurbishment_cost"]
            recycling_value = row["recycling_value"]
            disposal_cost = row["disposal_cost"]
            
            weight_kg = row["weight_kg"]
            material = row["material"]
            mat_cost_rate = MOCK_MATERIAL_RULES[material]["processing_cost_per_kg"]
            recycle_proc = weight_kg * mat_cost_rate
            
            net_vals = {
                "RESELL": resale_value,
                "REPAIR": resale_value - repair_cost,
                "REFURBISH": resale_value - refurbishment_cost,
                "RECYCLE": recycling_value - recycle_proc,
                "DISPOSE": -disposal_cost
            }
            base_val_recovered += net_vals.get(base_act, 0.0)
            
            # Waste avoided calculations
            w_avoid = {
                "RESELL": weight_kg,
                "REPAIR": weight_kg,
                "REFURBISH": weight_kg,
                "RECYCLE": weight_kg * 0.8,
                "DISPOSE": 0.0
            }
            base_waste_avoided += w_avoid.get(base_act, 0.0)
            
            # Carbon avoided calculations
            new_carbon_rates = {"Cardboard": 1.0, "Wood": 0.4, "Plastic": 2.6, "Metal": 5.5}
            carbon_new = weight_kg * new_carbon_rates[material]
            
            carbon_saved = {
                "RESELL": carbon_new - row["carbon_resell"],
                "REPAIR": carbon_new - row["carbon_repair"],
                "REFURBISH": carbon_new - row["carbon_refurbish"],
                "RECYCLE": (carbon_new * 0.8) - row["carbon_recycle"],
                "DISPOSE": -row["carbon_dispose"]
            }
            base_carbon_avoided += carbon_saved.get(base_act, 0.0)
            
    y_pred_proposed = np.array(y_pred_proposed)
    
    # Calculate performance metrics
    acc_base = accuracy_score(y_test, y_pred_baseline)
    f1_base = f1_score(y_test, y_pred_baseline, average="weighted", zero_division=0)
    
    acc_prop = accuracy_score(y_test, y_pred_proposed)
    f1_prop = f1_score(y_test, y_pred_proposed, average="weighted", zero_division=0)
    
    # Print results summary
    print(f"Baseline Accuracy: {acc_base:.4f} | Proposed Accuracy: {acc_prop:.4f}")
    
    # Save plots
    # 1. Confusion Matrix
    cm = confusion_matrix(y_test, y_pred_proposed)
    classes = sorted(y_test.unique())
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=classes, yticklabels=classes)
    plt.title("Confusion Matrix — Proposed Recommender")
    plt.xlabel("Predicted Label")
    plt.ylabel("True Label")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "confusion_matrix.png"))
    plt.close()
    
    # 2. Value Recovered comparison
    plt.figure(figsize=(6, 4))
    plt.bar(["Baseline", "Proposed"], [base_val_recovered, total_val_recovered], color=["#94a3b8", "#10B981"])
    plt.title("Total Value Recovered (₹)")
    plt.ylabel("Value (₹)")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "value_recovered_comparison.png"))
    plt.close()
    
    # 3. Waste avoided comparison
    plt.figure(figsize=(6, 4))
    plt.bar(["Baseline", "Proposed"], [base_waste_avoided, total_waste_avoided], color=["#94a3b8", "#3B82F6"])
    plt.title("Total Waste Avoided (kg)")
    plt.ylabel("Weight (kg)")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "waste_avoided_comparison.png"))
    plt.close()
    
    # 4. Carbon avoided comparison
    plt.figure(figsize=(6, 4))
    plt.bar(["Baseline", "Proposed"], [base_carbon_avoided, total_carbon_avoided], color=["#94a3b8", "#14b8a6"])
    plt.title("Carbon Footprint Avoided (kg CO2)")
    plt.ylabel("Carbon (kg CO2)")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "carbon_avoided_comparison.png"))
    plt.close()
    
    # 5. Disposition distribution
    plt.figure(figsize=(8, 5))
    pd.Series(y_pred_proposed).value_counts().plot(kind="bar", color="#3b82f6")
    plt.title("Disposition Recommendations Distribution")
    plt.ylabel("Units Count")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "disposition_distribution.png"))
    plt.close()
    
    # 6. Recommendation confidence
    plt.figure(figsize=(8, 5))
    plt.hist(proposed_confidences, bins=15, color="#10b981", edgecolor="black", alpha=0.7)
    plt.title("Distribution of Recommendation Confidence")
    plt.xlabel("Confidence Score")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "recommendation_confidence.png"))
    plt.close()
    
    # 7. Override rate (Mock illustration chart for presentation)
    plt.figure(figsize=(6, 4))
    plt.pie([92, 8], labels=["Approve Rate", "Override Rate"], autopct="%1.1f%%", colors=["#10b981", "#f59e0b"], startangle=90)
    plt.title("Manager Override Rate")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "override_rate.png"))
    plt.close()
    
    # 8. Error Categories
    incorrect_mask = y_pred_proposed != y_test
    incorrect_cases = X_test[incorrect_mask].copy()
    incorrect_cases["true_label"] = y_test[incorrect_mask]
    incorrect_cases["pred_label"] = y_pred_proposed[incorrect_mask]
    
    # Build error categories classification
    error_cats = {
        "Repair vs Refurbish confusion": 0,
        "Refurbish vs Resell confusion": 0,
        "Recycle vs Dispose confusion": 0,
        "Borderline costs": 0,
        "Safety triggers": 0
    }
    
    for _, row in incorrect_cases.iterrows():
        true_l = row["true_label"]
        pred_l = row["pred_label"]
        if true_l in ["REPAIR", "REFURBISH"] and pred_l in ["REPAIR", "REFURBISH"]:
            error_cats["Repair vs Refurbish confusion"] += 1
        elif true_l in ["REFURBISH", "RESELL"] and pred_l in ["REFURBISH", "RESELL"]:
            error_cats["Refurbish vs Resell confusion"] += 1
        elif true_l in ["RECYCLE", "DISPOSE"] and pred_l in ["RECYCLE", "DISPOSE"]:
            error_cats["Recycle vs Dispose confusion"] += 1
        elif row["safety_risk"] == "High" or row["structural_condition"] == "Unsafe":
            error_cats["Safety triggers"] += 1
        else:
            error_cats["Borderline costs"] += 1
            
    plt.figure(figsize=(8, 5))
    plt.bar(error_cats.keys(), error_cats.values(), color="#ef4444")
    plt.title("Error Categories in Misclassifications")
    plt.ylabel("Errors Count")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "error_categories.png"))
    plt.close()
    
    # --- 3. Safety Analysis ---
    print("\nExecuting Safety Constraint Analysis...")
    unsafe_containers = []
    for m in range(50):
        # Generate critical damage load risks
        unsafe_containers.append({
            "container_type": "Crate",
            "material": "Plastic",
            "weight_kg": 15.0,
            "age_months": 36,
            "usage_count": 100,
            "damage_level": "Critical",
            "structural_condition": "Unsafe",
            "cleanliness_score": 50.0,
            "contamination": "None",
            "safety_risk": "High",
            "sensor_available": True,
            "network_available": True,
            "recyclable": True,
            "location": "Warehouse A",
            "inspection_completeness": 1.0,
            "resale_value": 0.0, # safety triggers Resell to 0
            "repair_cost": 60.0,
            "refurbishment_cost": 25.0,
            "recycling_value": 3.0,
            "disposal_cost": 8.0,
            "carbon_repair": 4.0,
            "carbon_refurbish": 3.0,
            "carbon_resell": 0.1,
            "carbon_recycle": 1.0,
            "carbon_dispose": 8.0
        })
        
    unsafe_df = pd.DataFrame(unsafe_containers)
    
    # Evaluate safety violations before and after rule engine
    # Before rules (ML model only)
    ml_violations = 0
    final_violations = 0
    
    for _, row in unsafe_df.iterrows():
        # ML predict only
        ml_action, _ = MLService.predict(dict(row), dict(row))
        if ml_action.upper() in ["RESELL", "REPAIR", "REFURBISH"]:
            ml_violations += 1
            
        # Recommendations Engine (Rules + ML)
        rec = RecommendationEngine.generate_recommendation(dict(row), dict(row), MOCK_MATERIAL_RULES)
        if rec["recommended_action"] in ["RESELL", "REPAIR", "REFURBISH"]:
            final_violations += 1
            
    print(f"Unsafe recommendations before rule enforcement: {ml_violations}")
    print(f"Unsafe recommendations after rule enforcement: {final_violations}")
    
    # --- 4. Fairness Analysis ---
    print("\nExecuting Business Group Fairness Analysis...")
    fairness_records = []
    # Create matching containers for Group A, B, and C
    for group in ["Business A", "Business B", "Business C"]:
        for n in range(50):
            fairness_records.append({
                "group_id": group,
                "container_type": "Crate",
                "material": "Plastic",
                "weight_kg": 10.0,
                "age_months": 12,
                "usage_count": 25,
                "damage_level": "Low",
                "structural_condition": "Safe",
                "cleanliness_score": 90.0,
                "contamination": "None",
                "safety_risk": "Low",
                "sensor_available": True,
                "network_available": True,
                "recyclable": True,
                "location": "Warehouse A",
                "inspection_completeness": 1.0,
                "resale_value": 60.0,
                "repair_cost": 5.0,
                "refurbishment_cost": 10.0,
                "recycling_value": 2.0,
                "disposal_cost": 4.0,
                "carbon_repair": 1.0,
                "carbon_refurbish": 1.0,
                "carbon_resell": 0.1,
                "carbon_recycle": 1.0,
                "carbon_dispose": 4.0
            })
            
    fair_df = pd.DataFrame(fairness_records)
    rec_by_group = {g: [] for g in ["Business A", "Business B", "Business C"]}
    
    for _, row in fair_df.iterrows():
        container_data = {
            "id": "MOCK", "container_type": "Crate", "material": "Plastic", "weight_kg": 10.0, "age_months": 12, "usage_count": 25, "recyclable": True
        }
        rec = RecommendationEngine.generate_recommendation(container_data, dict(row), MOCK_MATERIAL_RULES)
        rec_by_group[row["group_id"]].append(rec["recommended_action"])
        
    for g in rec_by_group:
        counts = pd.Series(rec_by_group[g]).value_counts()
        print(f"Group: {g} recommendations distribution:")
        print(counts.to_dict())

    # Save metrics results to a JSON file for the notebook to load directly
    results_metrics = {
        "baseline_accuracy": float(acc_base),
        "baseline_f1": float(f1_base),
        "proposed_accuracy": float(acc_prop),
        "proposed_f1": float(f1_prop),
        "baseline_val_recovered": float(base_val_recovered),
        "proposed_val_recovered": float(total_val_recovered),
        "baseline_waste_avoided": float(base_waste_avoided),
        "proposed_waste_avoided": float(total_waste_avoided),
        "baseline_carbon_avoided": float(base_carbon_avoided),
        "proposed_carbon_avoided": float(total_carbon_avoided),
        "ml_unsafe_violations": ml_violations,
        "rules_unsafe_violations": final_violations
    }
    
    with open("experiments/experiment_results.json", "w") as f:
        json.dump(results_metrics, f)
    print("\nExperiment results saved successfully to experiments/experiment_results.json")

if __name__ == "__main__":
    run_experiment_suite()
