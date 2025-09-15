"""
enhanced_compare_snapshots.py
Enhanced snapshot comparison with structured change events and precise tracking.
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

import database, crud, schemas
from data_normalizer import DataNormalizer
from change_hash_utils import create_change_event_data, generate_change_hash


def generate_change_events(old_snapshot: List[Dict], new_snapshot: List[Dict]) -> List[Dict[str, Any]]:
    """
    Generate structured change events from snapshot comparison.
    
    Args:
        old_snapshot: Previous snapshot devices
        new_snapshot: Current snapshot devices
        
    Returns:
        List of ChangeEventItem dictionaries
    """
    change_events = []
    
    old_devices = {d["mac_address"]: d for d in old_snapshot}
    new_devices = {d["mac_address"]: d for d in new_snapshot}
    
    # New devices
    for mac, new_dev in new_devices.items():
        if mac not in old_devices:
            device_id = new_dev.get("system_uuid") or new_dev.get("mac_address") or "unknown"
            
            change_event = create_change_event_data(
                device_id=device_id,
                component="device",
                change_type="added",
                path="device",
                old_value=None,
                new_value=new_dev,
                agent_version=new_dev.get("agent_version")
            )
            change_events.append(change_event)
    
    # Removed devices
    for mac, old_dev in old_devices.items():
        if mac not in new_devices:
            device_id = old_dev.get("system_uuid") or old_dev.get("mac_address") or "unknown"
            
            change_event = create_change_event_data(
                device_id=device_id,
                component="device",
                change_type="removed",
                path="device",
                old_value=old_dev,
                new_value=None,
                agent_version=old_dev.get("agent_version")
            )
            change_events.append(change_event)
    
    # Modified devices
    for mac, old_dev in old_devices.items():
        if mac in new_devices:
            new_dev = new_devices[mac]
            device_id = new_dev.get("system_uuid") or new_dev.get("mac_address") or "unknown"
            
            # Normalize data before comparison
            normalized_old, normalized_new = DataNormalizer.normalize_for_comparison(old_dev, new_dev)
            
            # Generate component-level change events
            component_changes = _generate_component_changes(
                device_id, normalized_old, normalized_new, new_dev.get("agent_version")
            )
            change_events.extend(component_changes)
    
    return change_events


def _generate_component_changes(
    device_id: str, 
    old_data: Dict[str, Any], 
    new_data: Dict[str, Any],
    agent_version: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Generate component-level change events for a device.
    
    Args:
        device_id: Device identifier
        old_data: Normalized old device data
        new_data: Normalized new device data
        agent_version: Agent version
        
    Returns:
        List of component change events
    """
    changes = []
    
    # Hardware details changes
    if "hardware_details" in old_data and "hardware_details" in new_data:
        hw_old = old_data["hardware_details"]
        hw_new = new_data["hardware_details"]
        
        for component, old_value in hw_old.items():
            new_value = hw_new.get(component)
            
            if old_value != new_value:
                # Determine change type
                change_type = "modified"
                if old_value is None:
                    change_type = "added"
                elif new_value is None:
                    change_type = "removed"
                
                # Handle list components (disks, ram, etc.)
                if isinstance(old_value, list) and isinstance(new_value, list):
                    list_changes = _generate_list_component_changes(
                        device_id, component, old_value, new_value, agent_version
                    )
                    changes.extend(list_changes)
                else:
                    # Simple component change
                    change_event = create_change_event_data(
                        device_id=device_id,
                        component=component,
                        change_type=change_type,
                        path=f"hardware_details.{component}",
                        old_value=old_value,
                        new_value=new_value,
                        agent_version=agent_version
                    )
                    changes.append(change_event)
    
    # Direct device field changes
    for key, old_value in old_data.items():
        if key != "hardware_details":
            new_value = new_data.get(key)
            
            if old_value != new_value:
                change_type = "modified"
                if old_value is None:
                    change_type = "added"
                elif new_value is None:
                    change_type = "removed"
                
                change_event = create_change_event_data(
                    device_id=device_id,
                    component=key,
                    change_type=change_type,
                    path=key,
                    old_value=old_value,
                    new_value=new_value,
                    agent_version=agent_version
                )
                changes.append(change_event)
    
    return changes


def _generate_list_component_changes(
    device_id: str,
    component: str,
    old_list: List[Dict],
    new_list: List[Dict],
    agent_version: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Generate changes for list components (disks, RAM, etc.).
    
    Args:
        device_id: Device identifier
        component: Component name
        old_list: Old component list
        new_list: New component list
        agent_version: Agent version
        
    Returns:
        List of change events
    """
    changes = []
    
    # Create maps by stable identifiers
    old_map = _create_component_map(old_list)
    new_map = _create_component_map(new_list)
    
    # Find added components
    for key, new_item in new_map.items():
        if key not in old_map:
            change_event = create_change_event_data(
                device_id=device_id,
                component=component,
                change_type="added",
                path=f"hardware_details.{component}[{key}]",
                old_value=None,
                new_value=new_item,
                agent_version=agent_version
            )
            changes.append(change_event)
    
    # Find removed components
    for key, old_item in old_map.items():
        if key not in new_map:
            change_event = create_change_event_data(
                device_id=device_id,
                component=component,
                change_type="removed",
                path=f"hardware_details.{component}[{key}]",
                old_value=old_item,
                new_value=None,
                agent_version=agent_version
            )
            changes.append(change_event)
    
    # Find modified components
    for key, old_item in old_map.items():
        if key in new_map:
            new_item = new_map[key]
            if old_item != new_item:
                change_event = create_change_event_data(
                    device_id=device_id,
                    component=component,
                    change_type="modified",
                    path=f"hardware_details.{component}[{key}]",
                    old_value=old_item,
                    new_value=new_item,
                    agent_version=agent_version
                )
                changes.append(change_event)
    
    return changes


def _create_component_map(component_list: List[Dict]) -> Dict[str, Dict]:
    """
    Create a map of components by stable identifier.
    
    Args:
        component_list: List of component dictionaries
        
    Returns:
        Map of components by stable key
    """
    component_map = {}
    
    for i, component in enumerate(component_list):
        # Try to find stable identifier
        key = None
        for id_field in ['serial_number', 'serial', 'mac_address', 'device_id', 'uuid']:
            if id_field in component and component[id_field]:
                key = component[id_field]
                break
        
        # Fallback to index if no stable identifier
        if key is None:
            key = f"index_{i}"
        
        component_map[str(key)] = component
    
    return component_map


def save_change_events_to_db(change_events: List[Dict[str, Any]], db: Session) -> int:
    """
    Save change events to database as enhanced history logs.
    
    Args:
        change_events: List of change event dictionaries
        db: Database session
        
    Returns:
        Number of events saved
    """
    saved_count = 0
    
    for event in change_events:
        try:
            # Find device by system_uuid or mac_address
            device_id_str = event["device_id"]
            db_device = None
            
            # Try to find by system_uuid first
            if device_id_str != "unknown":
                db_device = db.query(database.Device).filter(
                    database.Device.system_uuid == device_id_str
                ).first()
                
                # Fallback to mac_address
                if not db_device:
                    db_device = db.query(database.Device).filter(
                        database.Device.mac_address == device_id_str
                    ).first()
            
            if db_device:
                # Create enhanced history log
                log_entry = database.HistoryLog(
                    device_id=db_device.id,
                    timestamp=event["timestamp"],
                    component=event["component"],
                    change_description=f"{event['change_type'].title()} in {event['component']}",
                    change_hash=event["change_hash"],
                    change_type=event["change_type"],
                    path=event["path"],
                    old_value=event["old_value"],
                    new_value=event["new_value"],
                    evidence=event.get("evidence"),
                    agent_version=event.get("agent_version")
                )
                
                db.add(log_entry)
                saved_count += 1
        
        except Exception as e:
            print(f"[ENHANCED_COMPARE] Error saving change event: {e}")
            continue
    
    try:
        db.commit()
        print(f"[ENHANCED_COMPARE] Saved {saved_count} change events to database")
    except Exception as e:
        db.rollback()
        print(f"[ENHANCED_COMPARE] Error committing change events: {e}")
        saved_count = 0
    
    return saved_count


def enhanced_comparison_report():
    """
    Enhanced comparison using structured change events.
    """
    snapshots = sorted(
        [f for f in os.listdir(EXPORT_DIR) if f.endswith(".json")],
        reverse=True
    )

    if len(snapshots) < 2:
        print("[ENHANCED_COMPARE] Insufficient snapshots for comparison.")
        return None

    latest = os.path.join(EXPORT_DIR, snapshots[0])
    previous = os.path.join(EXPORT_DIR, snapshots[1])

    # Load snapshots
    old_devices, old_hash, old_timestamp = load_snapshot(previous)
    new_devices, new_hash, new_timestamp = load_snapshot(latest)

    # Quick hash check
    if old_hash and new_hash and old_hash == new_hash:
        print(f"[ENHANCED_COMPARE] Identical hash ({new_hash[:8]}...) - No changes detected.")
        return None

    print(f"[ENHANCED_COMPARE] Generating structured change events...")

    # Generate structured change events
    change_events = generate_change_events(old_devices, new_devices)

    if not change_events:
        print("[ENHANCED_COMPARE] No change events generated.")
        return None

    # Save to database
    db: Session = database.SessionLocal()
    try:
        saved_count = save_change_events_to_db(change_events, db)
        
        # Apply intelligent filtering
        try:
            from intelligent_change_filter import filter_changes_intelligently
            
            # Convert change events to legacy format for filtering
            legacy_changes = _convert_to_legacy_format(change_events)
            
            # Load device context
            devices_context = {}
            for device_data in new_devices:
                mac = device_data.get('mac_address')
                if mac:
                    devices_context[mac] = device_data
            
            # Apply filter
            filtered_changes = filter_changes_intelligently(legacy_changes, devices_context)
            
            print(f"[ENHANCED_COMPARE] Intelligent filter: {len(legacy_changes)} → {len(filtered_changes)} significant changes")
            
            # Generate alerts for significant changes
            if filtered_changes:
                from alert_service import analyze_changes_and_create_alerts
                analyze_changes_and_create_alerts(filtered_changes)
                print(f"[ENHANCED_COMPARE] Alerts generated for {len(filtered_changes)} significant changes.")
            
        except Exception as e:
            print(f"[ENHANCED_COMPARE] Warning - Filter/alert error: {e}")
    
    finally:
        db.close()

    print(f"[ENHANCED_COMPARE] Processed {len(change_events)} change events successfully.")
    return change_events


def _convert_to_legacy_format(change_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert change events to legacy format for compatibility with existing filters."""
    legacy_changes = []
    
    for event in change_events:
        if event["change_type"] == "added" and event["component"] == "device":
            legacy_changes.append({
                "type": "NEW_DEVICE",
                "mac_address": event["device_id"],
                "changes": {"new": event["new_value"]}
            })
        elif event["change_type"] == "removed" and event["component"] == "device":
            legacy_changes.append({
                "type": "REMOVED_DEVICE", 
                "mac_address": event["device_id"],
                "changes": {"old": event["old_value"]}
            })
        else:
            # Convert component changes to legacy format
            legacy_changes.append({
                "type": "UPDATED_DEVICE",
                "mac_address": event["device_id"],
                "changes": {
                    event["path"]: {
                        "old": event["old_value"],
                        "new": event["new_value"]
                    }
                }
            })
    
    return legacy_changes


def load_snapshot(filepath):
    """Load snapshot with backward compatibility."""
    with open(filepath, "r", encoding="utf-8") as f:
        snapshot = json.load(f)
        if isinstance(snapshot, dict) and "devices" in snapshot:
            return snapshot["devices"], snapshot.get("hash"), snapshot.get("timestamp")
        return snapshot, None, None


if __name__ == "__main__":
    # Test enhanced comparison
    enhanced_comparison_report()
