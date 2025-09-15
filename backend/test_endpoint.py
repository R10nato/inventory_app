from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
import database, models, crud

app = FastAPI()

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/test-devices")
def test_devices(db: Session = Depends(get_db)):
    """Endpoint de teste simples para devices"""
    try:
        devices = db.query(models.Device).limit(5).all()
        return {
            "status": "success",
            "count": len(devices),
            "devices": [{"id": d.id, "name": d.name, "ip": d.ip_address} for d in devices]
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/test-devices-full")
def test_devices_full(db: Session = Depends(get_db)):
    """Teste com serialização completa usando schemas"""
    try:
        import schemas
        devices = crud.get_devices(db, limit=5)
        # Tentar serializar usando o schema Pydantic
        serialized = []
        for device in devices:
            try:
                device_dict = schemas.Device.model_validate(device).model_dump()
                serialized.append(device_dict)
            except Exception as e:
                return {"status": "serialization_error", "device_id": device.id, "error": str(e)}
        
        return {
            "status": "success",
            "count": len(serialized),
            "devices": serialized
        }
    except Exception as e:
        import traceback
        return {"status": "error", "message": str(e), "traceback": traceback.format_exc()}

@app.get("/test-health")
def test_health():
    """Endpoint de saúde básico"""
    return {"status": "ok", "message": "Server is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
