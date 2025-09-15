"""
change_hash_utils.py
Utilities for generating change hashes for deduplication and idempotency.
"""

import hashlib
import json
from typing import Any, Dict, Optional
from datetime import datetime
import uuid


def generate_change_hash(
    device_id: str,
    component: str,
    change_type: str,
    path: str,
    old_value: Optional[Any] = None,
    new_value: Optional[Any] = None
) -> str:
    """
    Generate SHA256 hash for a change event to enable deduplication.
    
    Args:
        device_id: Device identifier
        component: Component type (ram, disk, nic, etc.)
        change_type: Type of change (added, removed, modified, replaced)
        path: Path in snapshot (hardware.disks[0].serial)
        old_value: Previous value
        new_value: New value
        
    Returns:
        SHA256 hash string for the change
    """
    # Create normalized change data for hashing
    change_data = {
        "device_id": str(device_id).strip(),
        "component": str(component).strip().lower(),
        "change_type": str(change_type).strip().lower(),
        "path": str(path).strip(),
        "old_value": _normalize_value_for_hash(old_value),
        "new_value": _normalize_value_for_hash(new_value)
    }
    
    # Convert to JSON with sorted keys for consistent hashing
    json_str = json.dumps(change_data, sort_keys=True, ensure_ascii=False)
    
    # Generate SHA256 hash
    return hashlib.sha256(json_str.encode('utf-8')).hexdigest()


def generate_snapshot_hash(hardware_data: Dict[str, Any]) -> str:
    """
    Generate SHA256 hash for snapshot data.
    
    Args:
        hardware_data: Normalized hardware data dictionary
        
    Returns:
        SHA256 hash string for the snapshot
    """
    # Convert to JSON with sorted keys for consistent hashing
    json_str = json.dumps(hardware_data, sort_keys=True, ensure_ascii=False)
    
    # Generate SHA256 hash
    return hashlib.sha256(json_str.encode('utf-8')).hexdigest()


def generate_change_id() -> str:
    """
    Generate unique change ID using UUID4.
    
    Returns:
        UUID4 string for change identification
    """
    return str(uuid.uuid4())


def _normalize_value_for_hash(value: Any) -> Any:
    """
    Normalize a value for consistent hashing.
    
    Args:
        value: Value to normalize
        
    Returns:
        Normalized value
    """
    if value is None:
        return None
    elif isinstance(value, str):
        return value.strip()
    elif isinstance(value, (int, float, bool)):
        return value
    elif isinstance(value, (list, tuple)):
        return [_normalize_value_for_hash(item) for item in value]
    elif isinstance(value, dict):
        return {k: _normalize_value_for_hash(v) for k, v in value.items()}
    else:
        # Convert other types to string
        return str(value).strip()


def create_change_event_data(
    device_id: str,
    component: str,
    change_type: str,
    path: str,
    old_value: Optional[Any] = None,
    new_value: Optional[Any] = None,
    evidence: Optional[Dict] = None,
    agent_version: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create complete change event data with generated hash and ID.
    
    Args:
        device_id: Device identifier
        component: Component type
        change_type: Type of change
        path: Path in snapshot
        old_value: Previous value
        new_value: New value
        evidence: Raw evidence data
        agent_version: Agent version
        
    Returns:
        Complete change event data dictionary
    """
    change_hash = generate_change_hash(
        device_id=device_id,
        component=component,
        change_type=change_type,
        path=path,
        old_value=old_value,
        new_value=new_value
    )
    
    change_id = generate_change_id()
    
    return {
        "change_id": change_id,
        "device_id": device_id,
        "timestamp": datetime.utcnow(),
        "component": component,
        "change_type": change_type,
        "path": path,
        "old_value": old_value,
        "new_value": new_value,
        "evidence": evidence,
        "change_hash": change_hash,
        "agent_version": agent_version
    }


def is_duplicate_change(
    existing_hashes: set,
    device_id: str,
    component: str,
    change_type: str,
    path: str,
    old_value: Optional[Any] = None,
    new_value: Optional[Any] = None
) -> bool:
    """
    Check if a change is duplicate based on existing hashes.
    
    Args:
        existing_hashes: Set of existing change hashes
        device_id: Device identifier
        component: Component type
        change_type: Type of change
        path: Path in snapshot
        old_value: Previous value
        new_value: New value
        
    Returns:
        True if change is duplicate, False otherwise
    """
    change_hash = generate_change_hash(
        device_id=device_id,
        component=component,
        change_type=change_type,
        path=path,
        old_value=old_value,
        new_value=new_value
    )
    
    return change_hash in existing_hashes


if __name__ == "__main__":
    # Test hash generation
    test_change = create_change_event_data(
        device_id="test-device",
        component="disk",
        change_type="modified",
        path="hardware.disks[0].serial",
        old_value="OLD123",
        new_value="NEW456",
        agent_version="1.0.0"
    )
    
    print("Test change event:")
    print(json.dumps(test_change, indent=2, default=str))
    print(f"\nChange hash: {test_change['change_hash']}")
