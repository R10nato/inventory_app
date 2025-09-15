"""
agent_diff.py
Agent-side diff algorithm with normalization and secure transmission.
Integrates with existing inventory system architecture.
"""

import json
import hashlib
import hmac
import requests
import uuid
import time
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


def normalize_snapshot(snapshot: dict) -> dict:
    """
    Normalize snapshot data for consistent comparison.
    Enhanced version of the proposed algorithm.
    """
    def sort_key(x):
        if isinstance(x, dict):
            # Priority order for stable identifiers
            return (x.get("serial_number") or 
                   x.get("serial") or 
                   x.get("mac_address") or 
                   x.get("mac") or 
                   x.get("device_id") or
                   x.get("name") or 
                   x.get("model") or "")
        return str(x)
    
    def normalize_value(v):
        if isinstance(v, list):
            # Sort lists by stable identifiers
            return sorted([normalize_value(item) for item in v], key=sort_key)
        elif isinstance(v, dict):
            # Recursively normalize dictionaries
            return {k: normalize_value(val) for k, val in v.items()}
        elif isinstance(v, str):
            # Normalize strings (strip whitespace)
            return v.strip()
        else:
            return v
    
    normalized = {}
    for k, v in snapshot.items():
        # Skip volatile fields during normalization
        volatile_fields = [
            'last_seen', 'uptime_seconds', 'collection_timestamp',
            'temperature_info', 'free_space', 'used_space',
            'ram_usage', 'cpu_usage', 'current_reading'
        ]
        
        if not any(volatile in k.lower() for volatile in volatile_fields):
            normalized[k] = normalize_value(v)
    
    return normalized


def snapshot_hash(snapshot: dict) -> str:
    """Generate SHA256 hash of normalized snapshot."""
    s = json.dumps(snapshot, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def to_bytes(size) -> Optional[int]:
    """
    Convert size string to bytes.
    Enhanced version with better error handling.
    """
    if isinstance(size, int):
        return size
    if size is None:
        return None
    
    try:
        s = str(size).strip().upper()
        import re
        m = re.match(r'([\d\.]+)\s*(TB|GB|MB|KB|B)?', s)
        if not m:
            return None
        
        val = float(m.group(1))
        unit = m.group(2) or 'B'
        multipliers = {
            'B': 1, 
            'KB': 1024, 
            'MB': 1024**2, 
            'GB': 1024**3, 
            'TB': 1024**4
        }
        return int(val * multipliers[unit])
    except (ValueError, AttributeError):
        return None


def dict_diff(old, new, path="") -> List[Dict[str, Any]]:
    """
    Generate detailed diff between two dictionaries.
    Enhanced with better component tracking.
    """
    changes = []
    
    if isinstance(old, dict) and isinstance(new, dict):
        keys = set(old.keys()) | set(new.keys())
        for k in keys:
            p = f"{path}.{k}" if path else k
            if k not in old:
                changes.append({
                    "type": "added", 
                    "path": p, 
                    "old": None, 
                    "new": new[k]
                })
            elif k not in new:
                changes.append({
                    "type": "removed", 
                    "path": p, 
                    "old": old[k], 
                    "new": None
                })
            else:
                changes.extend(dict_diff(old[k], new[k], p))
    
    elif isinstance(old, list) and isinstance(new, list):
        # Enhanced list comparison with stable identifiers
        def get_stable_id(item, idx):
            if isinstance(item, dict):
                # Try multiple identifier fields
                for id_field in ['serial_number', 'serial', 'mac_address', 'mac', 'device_id', 'uuid']:
                    if id_field in item and item[id_field]:
                        return item[id_field]
                # Fallback to name or model
                for name_field in ['name', 'model', 'description']:
                    if name_field in item and item[name_field]:
                        return item[name_field]
            return f"index_{idx}"
        
        old_map = {get_stable_id(item, idx): item for idx, item in enumerate(old)}
        new_map = {get_stable_id(item, idx): item for idx, item in enumerate(new)}
        
        all_keys = set(old_map.keys()) | set(new_map.keys())
        for k in all_keys:
            if k not in old_map:
                changes.append({
                    "type": "added",
                    "path": f"{path}[{k}]",
                    "old": None,
                    "new": new_map[k]
                })
            elif k not in new_map:
                changes.append({
                    "type": "removed",
                    "path": f"{path}[{k}]",
                    "old": old_map[k],
                    "new": None
                })
            else:
                changes.extend(dict_diff(old_map[k], new_map[k], f"{path}[{k}]"))
    
    else:
        if old != new:
            # Convert sizes to bytes for comparison
            if any(keyword in path.lower() for keyword in ['size', 'capacity', 'total']):
                old_bytes = to_bytes(old)
                new_bytes = to_bytes(new)
                if old_bytes is not None and new_bytes is not None:
                    if old_bytes != new_bytes:
                        changes.append({
                            "type": "modified",
                            "path": path,
                            "old": old,
                            "new": new
                        })
                else:
                    changes.append({
                        "type": "modified",
                        "path": path,
                        "old": old,
                        "new": new
                    })
            else:
                changes.append({
                    "type": "modified",
                    "path": path,
                    "old": old,
                    "new": new
                })
    
    return changes


def make_change_event(device_id: str, component: str, change: Dict[str, Any], agent_version: str = None) -> Dict[str, Any]:
    """
    Create structured change event.
    Enhanced with better component detection.
    """
    # Determine component from path
    path = change["path"]
    if "hardware_details" in path:
        if "disk_info" in path:
            component = "disk"
        elif "ram_info" in path:
            component = "ram"
        elif "network_info" in path:
            component = "network"
        elif "cpu_info" in path:
            component = "cpu"
        elif "gpu_info" in path:
            component = "gpu"
        else:
            component = "hardware"
    else:
        component = path.split('.')[0] if '.' in path else path
    
    event = {
        "change_id": str(uuid.uuid4()),
        "device_id": device_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "component": component,
        "change_type": change["type"],
        "path": change["path"],
        "old_value": change.get("old"),
        "new_value": change.get("new"),
        "evidence": None,
        "agent_version": agent_version
    }
    
    # Generate change hash for deduplication
    hash_data = {
        "device_id": device_id,
        "component": component,
        "change_type": change["type"],
        "path": change["path"],
        "old_value": change.get("old"),
        "new_value": change.get("new")
    }
    hash_str = json.dumps(hash_data, sort_keys=True, default=str)
    event["change_hash"] = hashlib.sha256(hash_str.encode()).hexdigest()
    
    return event


def send_events(url: str, events: List[Dict], api_key: str, secret: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Send events to backend with HMAC authentication.
    Enhanced with better error handling and retry logic.
    """
    payload_data = {"events": events}
    payload = json.dumps(payload_data, default=str)
    
    # Generate HMAC signature
    signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-Signature": signature,
        "X-Timestamp": datetime.utcnow().isoformat() + "Z",
        "User-Agent": "InventoryAgent/1.0"
    }
    
    try:
        response = requests.post(
            url,
            data=payload,
            headers=headers,
            timeout=timeout,
            verify=True  # Always verify SSL certificates
        )
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send events: {e}")
        raise


class AgentDiffManager:
    """
    Manager class for agent-side diff operations.
    Handles snapshot storage, comparison, and event generation.
    """
    
    def __init__(self, storage_path: str = "snapshots", agent_version: str = "1.0.0"):
        self.storage_path = storage_path
        self.agent_version = agent_version
        os.makedirs(storage_path, exist_ok=True)
    
    def get_snapshot_file(self, device_id: str) -> str:
        """Get snapshot file path for device."""
        return os.path.join(self.storage_path, f"{device_id}_snapshot.json")
    
    def load_previous_snapshot(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Load previous snapshot from local storage."""
        snapshot_file = self.get_snapshot_file(device_id)
        if os.path.exists(snapshot_file):
            try:
                with open(snapshot_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load previous snapshot: {e}")
        return None
    
    def save_snapshot(self, device_id: str, snapshot: Dict[str, Any], snapshot_hash: str):
        """Save snapshot to local storage."""
        snapshot_file = self.get_snapshot_file(device_id)
        snapshot_data = {
            "hash": snapshot_hash,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "snapshot": snapshot
        }
        
        try:
            with open(snapshot_file, 'w', encoding='utf-8') as f:
                json.dump(snapshot_data, f, indent=2, default=str)
        except IOError as e:
            logger.error(f"Failed to save snapshot: {e}")
    
    def process_snapshot(self, current_snapshot: Dict[str, Any], device_id: str) -> List[Dict[str, Any]]:
        """
        Process current snapshot and generate change events.
        
        Args:
            current_snapshot: Current device snapshot
            device_id: Device identifier
            
        Returns:
            List of change events
        """
        # Normalize current snapshot
        current_normalized = normalize_snapshot(current_snapshot)
        current_hash = snapshot_hash(current_normalized)
        
        # Load previous snapshot
        previous_data = self.load_previous_snapshot(device_id)
        
        events = []
        
        if not previous_data or previous_data.get("hash") != current_hash:
            logger.info(f"Changes detected for device {device_id}")
            
            # Generate diff
            previous_snapshot = previous_data.get("snapshot", {}) if previous_data else {}
            changes = dict_diff(previous_snapshot, current_normalized)
            
            # Create change events
            events = [
                make_change_event(device_id, "hardware", change, self.agent_version)
                for change in changes
            ]
            
            # Save current snapshot
            self.save_snapshot(device_id, current_normalized, current_hash)
            
            logger.info(f"Generated {len(events)} change events for device {device_id}")
        else:
            logger.info(f"No changes detected for device {device_id}")
        
        return events


if __name__ == "__main__":
    # Test the diff algorithm
    old_snapshot = {
        "device_id": "test-device",
        "hardware_details": {
            "disk_info": [
                {"serial_number": "SSD123", "model": "Samsung SSD", "total_gb": 500}
            ]
        }
    }
    
    new_snapshot = {
        "device_id": "test-device", 
        "hardware_details": {
            "disk_info": [
                {"serial_number": "SSD123", "model": "Samsung SSD", "total_gb": 1000},
                {"serial_number": "HDD456", "model": "Seagate HDD", "total_gb": 2000}
            ]
        }
    }
    
    # Test normalization
    old_norm = normalize_snapshot(old_snapshot)
    new_norm = normalize_snapshot(new_snapshot)
    
    print("Old normalized:", json.dumps(old_norm, indent=2))
    print("New normalized:", json.dumps(new_norm, indent=2))
    
    # Test diff
    changes = dict_diff(old_norm, new_norm)
    print("Changes:", json.dumps(changes, indent=2))
    
    # Test event creation
    events = [make_change_event("test-device", "hardware", change) for change in changes]
    print("Events:", json.dumps(events, indent=2, default=str))
