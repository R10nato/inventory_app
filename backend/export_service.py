# backend/export_service.py
import os
import json
from datetime import datetime
from sqlalchemy.orm import Session
import crud, database

EXPORT_DIR = os.path.join(os.path.dirname(__file__), "exports")
os.makedirs(EXPORT_DIR, exist_ok=True)

def export_devices_snapshot():
    """
    Exporta um snapshot completo de todos os dispositivos
    e seus detalhes de hardware para um arquivo JSON.
    """
    db: Session = database.SessionLocal()
    try:
        devices = crud.get_devices(db)

        # Serializa os dispositivos para JSON
        export_data = []
        for device in devices:
            device_dict = {
                "id": device.id,
                "name": device.name,
                "ip_address": device.ip_address,
                "mac_address": device.mac_address,
                "device_type": device.device_type,
                "os": device.os,
                "status": device.status,
                "last_seen": device.last_seen.isoformat() if device.last_seen else None,
                "created_at": device.created_at.isoformat() if device.created_at else None,
                "hardware_details": {}
            }
            if device.hardware_details:
                device_dict["hardware_details"] = {
                    key: getattr(device.hardware_details, key)
                    for key in device.hardware_details.__dict__
                    if not key.startswith("_") and key != "device_id"
                }
            export_data.append(device_dict)

        # Nome do arquivo
        filename = f"devices_snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(EXPORT_DIR, filename)

        # Salva o JSON
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=4, ensure_ascii=False)

        print(f"[EXPORT] Snapshot exportado para {filepath}")

        return filepath

    except Exception as e:
        print(f"[EXPORT][ERRO] Falha ao exportar snapshot: {e}")
    finally:
        db.close()
