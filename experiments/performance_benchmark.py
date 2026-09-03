import os
import sys
import time
import json
import numpy as np
from fastapi.testclient import TestClient

# Add parent path to import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from repackai.backend.app.main import app
from repackai.backend.app.database import get_db

client = TestClient(app)

def run_telemetry_benchmark():
    print("Initializing RePackAI Performance Benchmark Telemetry...")
    
    # 1. Register test container & inspection
    container_id = "CON-PERF-99"
    # Ensure they exist in DB
    client.post("/api/containers", json={
        "id": container_id,
        "container_type": "Crate",
        "material": "Plastic",
        "weight_kg": 12.0,
        "age_months": 12,
        "usage_count": 30,
        "recyclable": True
    })
    
    insp_res = client.post("/api/inspections", json={
        "container_id": container_id,
        "damage_level": "Low",
        "structural_condition": "Safe",
        "cleanliness_score": 90.0,
        "contamination": "None",
        "safety_risk": "Low",
        "sensor_available": True,
        "network_available": True,
        "location": "Warehouse A",
        "inspection_completeness": 1.0,
        "raw_data_json": json.dumps({
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
    })
    
    inspection_id = insp_res.json()["id"]
    
    # 2. Benchmarking loop (100 requests)
    num_requests = 100
    latencies = []
    
    print(f"Executing batch of {num_requests} requests to /api/recommendations...")
    batch_start = time.time()
    
    for i in range(num_requests):
        req_start = time.time()
        res = client.post("/api/recommendations", json={
            "container_id": container_id,
            "inspection_id": inspection_id
        })
        req_end = time.time()
        
        assert res.status_code == 200, "API returned error during benchmark"
        latencies.append((req_end - req_start) * 1000) # in ms
        
    batch_end = time.time()
    total_duration_ms = (batch_end - batch_start) * 1000
    
    # Calculate stats
    avg_latency = np.mean(latencies)
    p95_latency = np.percentile(latencies, 95)
    throughput = num_requests / (total_duration_ms / 1000)
    
    print("\n--------------------------------------------------")
    print("Benchmark Telemetry Results:")
    print("--------------------------------------------------")
    print(f"Total Batch Requests:    {num_requests}")
    print(f"Total Batch Duration:    {total_duration_ms:.2f} ms")
    print(f"Average Response Latency: {avg_latency:.2f} ms")
    print(f"P95 Response Latency:     {p95_latency:.2f} ms")
    print(f"Throughput Rate:         {throughput:.2f} req/sec")
    print("--------------------------------------------------")
    
    # Save results
    bench_results = {
        "num_requests": num_requests,
        "total_duration_ms": total_duration_ms,
        "average_latency_ms": avg_latency,
        "p95_latency_ms": p95_latency,
        "throughput_req_sec": throughput
    }
    
    with open("experiments/benchmark_results.json", "w") as f:
        json.dump(bench_results, f)
        
if __name__ == "__main__":
    run_telemetry_benchmark()
