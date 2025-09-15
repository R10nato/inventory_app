# backend/alert_service.py
from sqlalchemy.orm import Session
import crud, schemas, database
from datetime import datetime


def create_system_alert(title: str, message: str, alert_type: str = "info", severity: str = "medium", 
                       source: str = "system", device_id: int = None, snapshot_id: int = None, 
                       metadata: dict = None):
    """
    Cria um alerta no sistema.
    """
    db: Session = database.SessionLocal()
    try:
        alert_data = schemas.AlertCreate(
            title=title,
            message=message,
            alert_type=alert_type,
            severity=severity,
            source=source,
            device_id=device_id,
            snapshot_id=snapshot_id,
            alert_metadata=metadata
        )
        
        alert = crud.create_alert(db, alert=alert_data)
        print(f"[ALERT] Criado: {title} (ID: {alert.id})")
        return alert
        
    except Exception as e:
        print(f"[ALERT][ERRO] Falha ao criar alerta: {e}")
        return None
    finally:
        db.close()


def analyze_changes_and_create_alerts(changes: list):
    """
    Analisa mudanças detectadas e cria alertas apropriados.
    """
    if not changes:
        return
    
    for change in changes:
        change_type = change.get("type")
        mac_address = change.get("mac_address")
        change_details = change.get("changes", {})
        
        # Buscar device_id pelo MAC address
        db: Session = database.SessionLocal()
        try:
            device = crud.get_device_by_ip_or_mac(db, ip_address=None, mac_address=mac_address)
            device_id = device.id if device else None
            device_name = device.name if device else mac_address
        finally:
            db.close()
        
        if change_type == "NEW_DEVICE":
            create_system_alert(
                title="Novo Dispositivo Detectado",
                message=f"Um novo dispositivo foi adicionado à rede: {device_name} ({mac_address})",
                alert_type="success",
                severity="medium",
                source="snapshot",
                device_id=device_id,
                metadata={
                    "change_type": change_type,
                    "mac_address": mac_address,
                    "device_details": change_details.get("new", {})
                }
            )
            
        elif change_type == "REMOVED_DEVICE":
            create_system_alert(
                title="Dispositivo Removido",
                message=f"O dispositivo {device_name} ({mac_address}) foi removido da rede",
                alert_type="warning",
                severity="high",
                source="snapshot",
                device_id=device_id,
                metadata={
                    "change_type": change_type,
                    "mac_address": mac_address,
                    "device_details": change_details.get("old", {})
                }
            )
            
        elif change_type == "UPDATED_DEVICE":
            # Analisar tipo de mudança para determinar severidade
            severity = "low"
            alert_type = "info"
            
            # Verificar mudanças críticas
            critical_changes = []
            important_changes = []
            
            for key, value in change_details.items():
                if "hardware" in key.lower():
                    if "cpu" in key.lower() or "ram" in key.lower() or "disk" in key.lower():
                        critical_changes.append(key)
                        severity = "high"
                        alert_type = "warning"
                    else:
                        important_changes.append(key)
                        if severity == "low":
                            severity = "medium"
                elif "temperature" in key.lower():
                    critical_changes.append(key)
                    severity = "high"
                    alert_type = "error"
                elif key in ["status", "last_seen"]:
                    important_changes.append(key)
                    if severity == "low":
                        severity = "medium"
            
            # Criar mensagem baseada nas mudanças
            if critical_changes:
                message = f"Mudanças críticas detectadas no dispositivo {device_name}: {', '.join(critical_changes)}"
            elif important_changes:
                message = f"Mudanças importantes detectadas no dispositivo {device_name}: {', '.join(important_changes)}"
            else:
                message = f"Mudanças detectadas no dispositivo {device_name}"
            
            create_system_alert(
                title="Dispositivo Atualizado",
                message=message,
                alert_type=alert_type,
                severity=severity,
                source="snapshot",
                device_id=device_id,
                metadata={
                    "change_type": change_type,
                    "mac_address": mac_address,
                    "changes": change_details,
                    "critical_changes": critical_changes,
                    "important_changes": important_changes
                }
            )


def check_device_health_and_create_alerts():
    """
    Verifica a saúde dos dispositivos e cria alertas se necessário.
    """
    db: Session = database.SessionLocal()
    try:
        devices = crud.get_devices(db)
        
        for device in devices:
            if not device.hardware_details:
                continue
                
            # Verificar temperatura da CPU
            temp_info = device.hardware_details.temperature_info
            if temp_info and isinstance(temp_info, dict):
                cpu_temp = temp_info.get("cpu_temp")
                if cpu_temp and cpu_temp > 80:
                    create_system_alert(
                        title="Temperatura Alta Detectada",
                        message=f"CPU do dispositivo {device.name} está a {cpu_temp}°C (acima de 80°C)",
                        alert_type="error",
                        severity="critical",
                        source="monitoring",
                        device_id=device.id,
                        metadata={
                            "cpu_temperature": cpu_temp,
                            "threshold": 80,
                            "device_name": device.name
                        }
                    )
                elif cpu_temp and cpu_temp > 70:
                    create_system_alert(
                        title="Temperatura Elevada",
                        message=f"CPU do dispositivo {device.name} está a {cpu_temp}°C (acima de 70°C)",
                        alert_type="warning",
                        severity="medium",
                        source="monitoring",
                        device_id=device.id,
                        metadata={
                            "cpu_temperature": cpu_temp,
                            "threshold": 70,
                            "device_name": device.name
                        }
                    )
            
            # Verificar uso de disco
            disk_info = device.hardware_details.disk_info
            if disk_info and isinstance(disk_info, list):
                for disk in disk_info:
                    if isinstance(disk, dict) and "partitions" in disk:
                        for partition in disk.get("partitions", []):
                            if isinstance(partition, dict):
                                total_gb = partition.get("total_gb", 0)
                                free_gb = partition.get("free_gb", 0)
                                
                                if total_gb > 0:
                                    usage_percent = ((total_gb - free_gb) / total_gb) * 100
                                    
                                    if usage_percent > 90:
                                        create_system_alert(
                                            title="Disco Quase Cheio",
                                            message=f"Partição {partition.get('drive_letter', 'N/A')} do dispositivo {device.name} está {usage_percent:.1f}% cheia",
                                            alert_type="error",
                                            severity="high",
                                            source="monitoring",
                                            device_id=device.id,
                                            metadata={
                                                "partition": partition.get("drive_letter"),
                                                "usage_percent": usage_percent,
                                                "free_gb": free_gb,
                                                "total_gb": total_gb,
                                                "device_name": device.name
                                            }
                                        )
                                    elif usage_percent > 80:
                                        create_system_alert(
                                            title="Espaço em Disco Baixo",
                                            message=f"Partição {partition.get('drive_letter', 'N/A')} do dispositivo {device.name} está {usage_percent:.1f}% cheia",
                                            alert_type="warning",
                                            severity="medium",
                                            source="monitoring",
                                            device_id=device.id,
                                            metadata={
                                                "partition": partition.get("drive_letter"),
                                                "usage_percent": usage_percent,
                                                "free_gb": free_gb,
                                                "total_gb": total_gb,
                                                "device_name": device.name
                                            }
                                        )
            
            # Verificar se dispositivo está offline há muito tempo
            if device.status == "offline":
                from datetime import datetime, timedelta
                if device.last_seen:
                    time_offline = datetime.now() - device.last_seen.replace(tzinfo=None)
                    if time_offline > timedelta(hours=24):
                        create_system_alert(
                            title="Dispositivo Offline",
                            message=f"Dispositivo {device.name} está offline há {time_offline.days} dias",
                            alert_type="warning",
                            severity="medium",
                            source="monitoring",
                            device_id=device.id,
                            metadata={
                                "offline_duration_days": time_offline.days,
                                "last_seen": device.last_seen.isoformat() if device.last_seen else None,
                                "device_name": device.name
                            }
                        )
                        
    except Exception as e:
        print(f"[ALERT][ERRO] Falha na verificação de saúde: {e}")
    finally:
        db.close()


def create_snapshot_alert(snapshot_hash: str, device_count: int, changes_count: int = 0):
    """
    Cria alerta para snapshot criado.
    """
    if changes_count > 0:
        create_system_alert(
            title="Snapshot com Alterações",
            message=f"Novo snapshot criado com {changes_count} alteração(ões) detectada(s) em {device_count} dispositivo(s)",
            alert_type="info",
            severity="medium",
            source="snapshot",
            metadata={
                "snapshot_hash": snapshot_hash,
                "device_count": device_count,
                "changes_count": changes_count
            }
        )
    else:
        create_system_alert(
            title="Snapshot Criado",
            message=f"Novo snapshot criado com {device_count} dispositivo(s) - Nenhuma alteração detectada",
            alert_type="success",
            severity="low",
            source="snapshot",
            metadata={
                "snapshot_hash": snapshot_hash,
                "device_count": device_count,
                "changes_count": 0
            }
        )
