import datetime
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

try:
    from backend.app.config import settings
    from backend.app.database import engine, Base, get_db
    from backend.app.api import routes
except ImportError:
    try:
        from app.config import settings
        from app.database import engine, Base, get_db
        from app.api import routes
    except ImportError:
        from repackai.backend.app.config import settings
        from repackai.backend.app.database import engine, Base, get_db
        from repackai.backend.app.api import routes

# Initialize database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Intelligent Reusable Packaging Disposition Recommender System",
    version="1.0.0"
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes under /api
app.include_router(routes.router, prefix="/api")

# Add alias /health at the root level
@app.get("/health")
def health_root(db: Session = Depends(get_db)):
    from sqlalchemy import text
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
        
    return {
        "status": "healthy" if db_ok else "unhealthy",
        "database": "connected" if db_ok else "disconnected",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
