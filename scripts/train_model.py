import os
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix

# 1. Define Baseline Classifier class conforming to scikit-learn API
class BaselineClassifier:
    def fit(self, X, y):
        # Heuristics require no fitting
        return self
        
    def predict(self, X):
        predictions = []
        for _, row in X.iterrows():
            damage = str(row.get("damage_level", "None")).strip().lower()
            recyclable = row.get("recyclable")
            
            # Simple Baseline Heuristics
            if damage in ["none", "nan", "null"]:
                predictions.append("Resell")
            elif damage == "low":
                predictions.append("Repair")
            elif damage == "medium":
                predictions.append("Refurbish")
            elif recyclable == True or str(recyclable).strip().lower() == "true":
                predictions.append("Recycle")
            else:
                predictions.append("Dispose")
        return np.array(predictions)

def train_repack_model(data_path="data/synthetic/synthetic_containers.csv", model_dir="models"):
    os.makedirs(model_dir, exist_ok=True)
    os.makedirs("experiments", exist_ok=True)
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Dataset not found at {data_path}. Please run generate_dataset.py first.")
        
    df = pd.read_csv(data_path)
    
    # Target column is final_disposition
    X = df.drop(columns=["container_id", "final_disposition"])
    y = df["final_disposition"]
    
    # Perform train/test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    print("--------------------------------------------------")
    print("Evaluating Baseline Rule-Based Heuristic Classifier:")
    print("--------------------------------------------------")
    baseline = BaselineClassifier()
    y_pred_baseline = baseline.predict(X_test)
    
    # We standardise casing to match predictions and test labels
    y_test_clean = y_test.str.lower()
    y_pred_base_clean = pd.Series(y_pred_baseline).str.lower()
    
    print(f"Accuracy: {accuracy_score(y_test_clean, y_pred_base_clean):.4f}")
    print("\nClassification Report (Baseline):")
    print(classification_report(y_test_clean, y_pred_base_clean, zero_division=0))
    
    print("--------------------------------------------------")
    print("Training and Evaluating Random Forest Classifier:")
    print("--------------------------------------------------")
    
    # Identify numeric and categorical columns
    categorical_cols = X.select_dtypes(include=["object", "bool"]).columns.tolist()
    numeric_cols = X.select_dtypes(include=["int64", "float64"]).columns.tolist()
    
    # Build transformation pipeline
    numeric_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median"))
    ])
    
    categorical_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore"))
    ])
    
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_cols),
            ("cat", categorical_transformer, categorical_cols)
        ]
    )
    
    # Full machine learning pipeline
    model_pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("classifier", RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42))
    ])
    
    # Fit the ML pipeline
    model_pipeline.fit(X_train, y_train)
    
    # Predict and evaluate
    y_pred_ml = model_pipeline.predict(X_test)
    
    acc = accuracy_score(y_test, y_pred_ml)
    conf_mat = confusion_matrix(y_test, y_pred_ml)
    class_report = classification_report(y_test, y_pred_ml, output_dict=True)
    
    print(f"Accuracy: {acc:.4f}")
    print("\nClassification Report (Random Forest):")
    print(classification_report(y_test, y_pred_ml))
    print("\nConfusion Matrix:")
    print(conf_mat)
    
    # Save the intelligent ML model
    model_save_path = os.path.join(model_dir, "repack_model.joblib")
    joblib.dump(model_pipeline, model_save_path)
    print(f"\nTrained model pipeline saved successfully to {model_save_path}")
    
    # Write experiment logs
    with open("experiments/run_log.txt", "a") as f:
        f.write(f"Timestamp: {pd.Timestamp.now()}\n")
        f.write(f"Dataset Rows: {len(df)}\n")
        f.write(f"Test Accuracy: {acc:.4f}\n")
        f.write(f"Parameters: n_estimators=100, max_depth=12\n")
        f.write(f"Classification Report:\n{classification_report(y_test, y_pred_ml)}\n")
        f.write("="*50 + "\n\n")

if __name__ == "__main__":
    train_repack_model()
