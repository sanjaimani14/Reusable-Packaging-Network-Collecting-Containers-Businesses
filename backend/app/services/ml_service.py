import os
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
from repackai.backend.app.config import settings

class MLService:
    _model = None

    @classmethod
    def load_model(cls):
        if cls._model is None:
            model_path = settings.MODEL_PATH
            # Ensure path is resolved relative to the repackai project directory
            if not os.path.exists(model_path):
                # Try relative to workspace
                alt_path = os.path.join(os.getcwd(), "repackai", model_path)
                if os.path.exists(alt_path):
                    model_path = alt_path
                else:
                    alt_path_2 = os.path.join(os.getcwd(), model_path)
                    if os.path.exists(alt_path_2):
                        model_path = alt_path_2

            if os.path.exists(model_path):
                try:
                    cls._model = joblib.load(model_path)
                    print(f"ML Model loaded successfully from {model_path}")
                except Exception as e:
                    print(f"Error loading ML model from {model_path}: {e}")
            else:
                print(f"Warning: ML Model not found at {model_path}. Using baseline heuristics for inference.")
        return cls._model

    @classmethod
    def predict(cls, container_data: Dict[str, Any], inspection_data: Dict[str, Any]) -> Tuple[str, float]:
        model = cls.load_model()
        
        # Prepare input features mapping (must match features in generate_dataset)
        input_data = {
            "container_type": container_data.get("container_type"),
            "material": container_data.get("material"),
            "weight_kg": container_data.get("weight_kg"),
            "age_months": container_data.get("age_months"),
            "usage_count": container_data.get("usage_count"),
            "damage_level": inspection_data.get("damage_level"),
            "structural_condition": inspection_data.get("structural_condition"),
            "cleanliness_score": inspection_data.get("cleanliness_score"),
            "contamination": inspection_data.get("contamination"),
            "repair_required": inspection_data.get("repair_required", False),
            "repair_cost": inspection_data.get("repair_cost", 0.0),
            "refurbishment_cost": inspection_data.get("refurbishment_cost", 0.0),
            "resale_value": inspection_data.get("resale_value", 0.0),
            "recycling_value": inspection_data.get("recycling_value", 0.0),
            "disposal_cost": inspection_data.get("disposal_cost", 0.0),
            "carbon_repair": inspection_data.get("carbon_repair", 0.0),
            "carbon_refurbish": inspection_data.get("carbon_refurbish", 0.0),
            "carbon_resell": inspection_data.get("carbon_resell", 0.0),
            "carbon_recycle": inspection_data.get("carbon_recycle", 0.0),
            "carbon_dispose": inspection_data.get("carbon_dispose", 0.0),
            "recyclable": container_data.get("recyclable", True),
            "safety_risk": inspection_data.get("safety_risk"),
            "location": inspection_data.get("location"),
            "sensor_available": inspection_data.get("sensor_available", True),
            "network_available": inspection_data.get("network_available", True),
            "inspection_completeness": inspection_data.get("inspection_completeness", 1.0)
        }
        
        # Convert to DataFrame
        df_input = pd.DataFrame([input_data])
        
        if model is not None:
            try:
                prediction = model.predict(df_input)[0]
                # Get prediction probabilities
                prob = model.predict_proba(df_input)[0]
                classes = model.classes_
                # Match predicted label to its probability
                pred_index = list(classes).index(prediction)
                confidence = float(prob[pred_index])
                return str(prediction), confidence
            except Exception as e:
                print(f"ML Inference failed, falling back to heuristic: {e}")
                
        # Heuristic/Baseline fallback if model fails or isn't loaded
        damage = str(inspection_data.get("damage_level", "None")).strip().lower()
        recyclable = container_data.get("recyclable", True)
        
        if damage in ["none", "nan", "null"]:
            return "Resell", 0.70
        elif damage == "low":
            return "Repair", 0.70
        elif damage == "medium":
            return "Refurbish", 0.70
        elif recyclable:
            return "Recycle", 0.75
        else:
            return "Dispose", 0.80
