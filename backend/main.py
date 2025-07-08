from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import models, database, schemas # schemas will be created next

# Create database tables on startup (for development only, use Alembic for production)
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(
    title="Inventory & Monitoring API",
    description="API for managing network device inventory and hardware details.",
    version="0.1.0"
)

# Dependency to get DB session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", tags=["Root"])
def read_root():
    """Provides a simple welcome message."""
    return {"message": "Welcome to the Inventory & Monitoring API"}

# Placeholder for future routers/endpoints
from routers import devices # Example: Routers will be added later
app.include_router(devices.router)
# app.include_router(history.router)

# Note: Pydantic schemas (schemas.py) need to be created for request/response validation.
# Note: Routers for specific functionalities (devices, history, etc.) will be added in the next steps.

