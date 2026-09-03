import sys
import os
from sqlalchemy.orm import Session

# Add the parent folder to path to import repackai modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from repackai.backend.app.database import engine, Base, SessionLocal
from repackai.backend.app.models import domain
import hashlib

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def seed_database():
    print("Initializing and seeding database...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if users already seeded to avoid duplicate entries
        if db.query(domain.User).first() is not None:
            print("Database already seeded. Skipping.")
            return

        # 1. Seed Users
        print("Seeding users...")
        admin_user = domain.User(
            username="admin",
            email="admin@repack.ai",
            hashed_password=hash_password("adminpassword"),
            role="admin"
        )
        operator_user = domain.User(
            username="operator",
            email="operator@repack.ai",
            hashed_password=hash_password("operatorpassword"),
            role="operator"
        )
        db.add(admin_user)
        db.add(operator_user)

        # 2. Seed Material Rules
        print("Seeding material rules...")
        materials = [
            domain.MaterialRule(
                material_name="Cardboard",
                recyclable=True,
                processing_cost_per_kg=0.02,
                recycling_value_per_kg=0.08,
                carbon_recycle_per_kg=0.40,
                carbon_dispose_per_kg=1.20
            ),
            domain.MaterialRule(
                material_name="Wood",
                recyclable=True,
                processing_cost_per_kg=0.01,
                recycling_value_per_kg=0.03,
                carbon_recycle_per_kg=0.10,
                carbon_dispose_per_kg=0.50
            ),
            domain.MaterialRule(
                material_name="Plastic",
                recyclable=True,
                processing_cost_per_kg=0.05,
                recycling_value_per_kg=0.20,
                carbon_recycle_per_kg=1.04,
                carbon_dispose_per_kg=3.12
            ),
            domain.MaterialRule(
                material_name="Metal",
                recyclable=True,
                processing_cost_per_kg=0.10,
                recycling_value_per_kg=0.50,
                carbon_recycle_per_kg=2.20,
                carbon_dispose_per_kg=6.60
            )
        ]
        db.add_all(materials)

        # 3. Seed Disposal Rules
        print("Seeding disposal rules...")
        disposals = [
            domain.DisposalRule(
                contamination_type="None",
                disposal_cost_multiplier=1.0,
                is_hazardous=False,
                requires_special_handling=False
            ),
            domain.DisposalRule(
                contamination_type="Organic",
                disposal_cost_multiplier=1.5,
                is_hazardous=False,
                requires_special_handling=False
            ),
            domain.DisposalRule(
                contamination_type="Chemical",
                disposal_cost_multiplier=2.5,
                is_hazardous=True,
                requires_special_handling=True
            ),
            domain.DisposalRule(
                contamination_type="Hazardous",
                disposal_cost_multiplier=6.0,
                is_hazardous=True,
                requires_special_handling=True
            )
        ]
        db.add_all(disposals)

        # 4. Seed Sample Containers for verification
        print("Seeding sample containers...")
        sample_containers = [
            domain.Container(
                id="CON-200001",
                container_type="Crate",
                material="Plastic",
                weight_kg=12.5,
                age_months=12,
                usage_count=45,
                recyclable=True,
                status="synced"
            ),
            domain.Container(
                id="CON-200002",
                container_type="Pallet",
                material="Wood",
                weight_kg=22.0,
                age_months=24,
                usage_count=98,
                recyclable=True,
                status="synced"
            ),
            domain.Container(
                id="CON-200003",
                container_type="Drum",
                material="Metal",
                weight_kg=35.0,
                age_months=36,
                usage_count=120,
                recyclable=True,
                status="synced"
            )
        ]
        db.add_all(sample_containers)

        db.commit()
        print("Database seeded successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
