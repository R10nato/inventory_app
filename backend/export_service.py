# backend/export_service.py
import os
import json
import hashlib
from datetime import datetime
from sqlalchemy.orm import Session
import crud, database, schemas

EXPORT_DIR = os.path.join(os.path.dirname(__file__), "exports")
os.makedirs(EXPORT_DIR, exist_ok=True)

def generate_snapshot_hash(data):
    """
    Gera hash SHA256 de um snapshot para detecção rápida de mudanças.
    """
    # Converte os dados para JSON string de forma determinística
    json_string = json.dumps(data, sort_keys=True, ensure_ascii=False)
    # Gera o hash SHA256
    return hashlib.sha256(json_string.encode('utf-8')).hexdigest()

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

        # Gera hash SHA256 do snapshot
        snapshot_hash = generate_snapshot_hash(export_data)
        
        # Cria estrutura final do snapshot com metadados
        snapshot_with_metadata = {
            "timestamp": datetime.now().isoformat(),
            "hash": snapshot_hash,
            "device_count": len(export_data),
            "devices": export_data
        }

        # Nome do arquivo
        filename = f"devices_snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(EXPORT_DIR, filename)

        # Salva o JSON
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(snapshot_with_metadata, f, indent=4, ensure_ascii=False)

        print(f"[EXPORT] Snapshot exportado para {filepath}")
        print(f"[EXPORT] Hash SHA256: {snapshot_hash}")
        print(f"[EXPORT] Dispositivos: {len(export_data)}")

        # Registra o snapshot no banco de dados
        try:
            file_size = os.path.getsize(filepath) if os.path.exists(filepath) else None
            
            snapshot_data = schemas.SnapshotCreate(
                hash_sha256=snapshot_hash,
                device_count=len(export_data),
                file_path=filepath,
                file_size=file_size
            )
            
            # Usa a mesma sessão do banco
            created_snapshot = crud.create_snapshot(db, snapshot=snapshot_data)
            print(f"[EXPORT] Snapshot registrado no banco com ID: {created_snapshot.id}")
            
        except Exception as e:
            print(f"[EXPORT][AVISO] Falha ao registrar snapshot no banco: {e}")

        return filepath, snapshot_hash

    except Exception as e:
        print(f"[EXPORT][ERRO] Falha ao exportar snapshot: {e}")
        return None, None
    finally:
        db.close()
