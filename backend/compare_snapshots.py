# backend/compare_snapshots.py
import os
import json
from datetime import datetime
from sqlalchemy.orm import Session

import database, crud, schemas

EXPORT_DIR = os.path.join(os.path.dirname(__file__), "exports")

def load_snapshot(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        snapshot = json.load(f)
        # Se o snapshot tem a nova estrutura com metadados, retorna apenas os devices
        if isinstance(snapshot, dict) and "devices" in snapshot:
            return snapshot["devices"], snapshot.get("hash"), snapshot.get("timestamp")
        # Compatibilidade com snapshots antigos
        return snapshot, None, None

def compare_snapshots(old_snapshot, new_snapshot):
    changes = []

    old_devices = {d["mac_address"]: d for d in old_snapshot}
    new_devices = {d["mac_address"]: d for d in new_snapshot}

    # Novos dispositivos
    for mac, new_dev in new_devices.items():
        if mac not in old_devices:
            changes.append({
                "type": "NEW_DEVICE",
                "mac_address": mac,
                "changes": {"new": new_dev}
            })

    # Dispositivos removidos
    for mac, old_dev in old_devices.items():
        if mac not in new_devices:
            changes.append({
                "type": "REMOVED_DEVICE",
                "mac_address": mac,
                "changes": {"old": old_dev}
            })

    # Alterações em dispositivos existentes
    for mac, old_dev in old_devices.items():
        if mac in new_devices:
            new_dev = new_devices[mac]
            diff = {}
            for key, old_value in old_dev.items():
                if key == "hardware_details":
                    for hw_key, hw_old_val in old_value.items():
                        hw_new_val = new_dev.get("hardware_details", {}).get(hw_key)
                        if hw_old_val != hw_new_val:
                            diff[f"hardware.{hw_key}"] = {"old": hw_old_val, "new": hw_new_val}
                else:
                    if old_value != new_dev.get(key):
                        diff[key] = {"old": old_value, "new": new_dev.get(key)}
            if diff:
                changes.append({
                    "type": "UPDATED_DEVICE",
                    "mac_address": mac,
                    "changes": diff
                })

    return changes

def generate_comparison_report():
    """
    Compara os 2 snapshots mais recentes e grava as mudanças no banco (history_logs).
    Usa hash SHA256 para detecção rápida de mudanças.
    """
    snapshots = sorted(
        [f for f in os.listdir(EXPORT_DIR) if f.endswith(".json")],
        reverse=True
    )

    if len(snapshots) < 2:
        print("[COMPARE] Não há snapshots suficientes para comparação.")
        return None

    latest = os.path.join(EXPORT_DIR, snapshots[0])
    previous = os.path.join(EXPORT_DIR, snapshots[1])

    # Carrega snapshots com hash e metadados
    old_devices, old_hash, old_timestamp = load_snapshot(previous)
    new_devices, new_hash, new_timestamp = load_snapshot(latest)

    # Verificação rápida usando hash SHA256
    if old_hash and new_hash and old_hash == new_hash:
        print(f"[COMPARE] Hash SHA256 idêntico ({new_hash[:8]}...) - Nenhuma alteração detectada.")
        return None

    print(f"[COMPARE] Hash diferente - Old: {old_hash[:8] if old_hash else 'N/A'}... New: {new_hash[:8] if new_hash else 'N/A'}...")

    changes = compare_snapshots(old_devices, new_devices)

    if not changes:
        print("[COMPARE] Nenhuma alteração encontrada.")
        return None

    # Conectar no banco e registrar histórico
    db: Session = database.SessionLocal()
    try:
        for change in changes:
            mac = change["mac_address"]
            db_device = crud.get_device_by_ip_or_mac(db, ip_address=None, mac_address=mac)

            if db_device:
                log_entry = schemas.HistoryLogCreate(
                    change_type=change["type"],
                    description=json.dumps(change["changes"], ensure_ascii=False),
                    timestamp=datetime.now()
                )
                crud.create_history_log(db, log=log_entry, device_id=db_device.id)

        print(f"[COMPARE] {len(changes)} mudanças gravadas no banco (history_logs).")
    finally:
        db.close()

    return changes
