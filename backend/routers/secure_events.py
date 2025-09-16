"""
secure_events.py
Secure API endpoint for receiving agent change events with HMAC authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Dict, Any
import logging

from database import get_db, Device, HistoryLog
from hmac_auth import get_receiver, SecureEventReceiver
from schemas import ChangeEventItem, ChangeEventItemCreate
import json
from datetime import datetime
import models, schemas, database, crud

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/events", tags=["secure_events"])
security = HTTPBearer()


@router.post("/changes", response_model=Dict[str, Any])
async def receive_change_events(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Receive and process change events from agents with HMAC authentication.
    
    Expected payload:
    {
        "events": [
            {
                "device_id": "uuid-or-mac",
                "component": "disk",
                "change_type": "modified",
                "path": "hardware.disks[0].serial",
                "old_value": "OLD123",
                "new_value": "NEW456",
                "change_hash": "sha256-hash",
                "evidence": {...},
                "agent_version": "1.0.0"
            }
        ]
    }
    """
    try:
        # Get secure receiver and validate request
        receiver = get_receiver()
        validated_data = await receiver.validate_request(request, credentials)
        
        events = validated_data.get("events", [])
        if not events:
            raise HTTPException(status_code=400, detail="No events provided")
        
        processed_count = 0
        duplicate_count = 0
        error_count = 0
        
        for event_data in events:
            try:
                # Find device by device_id (system_uuid or mac_address)
                device_id_str = event_data.get("device_id")
                if not device_id_str:
                    logger.warning("Event missing device_id")
                    error_count += 1
                    continue
                
                # Try to find device by system_uuid first, then mac_address
                db_device = db.query(Device).filter(
                    Device.system_uuid == device_id_str
                ).first()
                
                if not db_device:
                    db_device = db.query(Device).filter(
                        Device.mac_address == device_id_str
                    ).first()
                
                if not db_device:
                    logger.warning(f"Device not found: {device_id_str}")
                    error_count += 1
                    continue
                
                # Create enhanced history log entry
                log_entry = HistoryLog(
                    device_id=db_device.id,
                    timestamp=datetime.fromisoformat(
                        event_data.get("timestamp", datetime.utcnow().isoformat()).replace('Z', '+00:00')
                    ),
                    component=event_data.get("component", "unknown"),
                    change_description=f"{event_data.get('change_type', 'unknown').title()} in {event_data.get('component', 'unknown')}",
                    change_hash=event_data.get("change_hash"),
                    change_type=event_data.get("change_type"),
                    path=event_data.get("path"),
                    old_value=event_data.get("old_value"),
                    new_value=event_data.get("new_value"),
                    evidence=event_data.get("evidence"),
                    agent_version=event_data.get("agent_version")
                )
                
                db.add(log_entry)
                processed_count += 1
                
            except IntegrityError as e:
                # Duplicate change_hash for this device
                db.rollback()
                duplicate_count += 1
                logger.debug(f"Duplicate event ignored: {event_data.get('change_hash', 'unknown')}")
                
            except Exception as e:
                db.rollback()
                error_count += 1
                logger.error(f"Error processing event: {e}")
        
        # Commit all successful events
        try:
            db.commit()
            logger.info(f"Processed {processed_count} events, {duplicate_count} duplicates, {error_count} errors")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to commit events: {e}")
            raise HTTPException(status_code=500, detail="Failed to save events")
        
        # Generate alerts for significant changes if needed
        if processed_count > 0:
            try:
                from alert_service import create_change_alert
                
                # Create summary alert for batch of changes
                alert_message = f"Received {processed_count} change events from agent"
                create_change_alert(
                    db=db,
                    title="Agent Changes Received",
                    message=alert_message,
                    device_id=db_device.id if db_device else None,
                    severity="info"
                )
                
            except Exception as e:
                logger.warning(f"Failed to create alert: {e}")
        
        return {
            "status": "success",
            "processed": processed_count,
            "duplicates": duplicate_count,
            "errors": error_count,
            "total_received": len(events)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in receive_change_events: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/heartbeat", response_model=Dict[str, Any])
async def agent_heartbeat(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Agent heartbeat endpoint with HMAC authentication.
    
    Expected payload:
    {
        "device_id": "uuid-or-mac",
        "agent_version": "1.0.0",
        "status": "online",
        "last_snapshot_hash": "sha256-hash"
    }
    """
    try:
        # Validate request
        receiver = get_receiver()
        validated_data = await receiver.validate_request(request, credentials)
        
        device_id_str = validated_data.get("device_id")
        if not device_id_str:
            raise HTTPException(status_code=400, detail="Missing device_id")
        
        # Find and update device
        db_device = db.query(Device).filter(
            Device.system_uuid == device_id_str
        ).first()
        
        if not db_device:
            db_device = db.query(Device).filter(
                Device.mac_address == device_id_str
            ).first()
        
        if db_device:
            # Update device status and last_seen
            db_device.status = validated_data.get("status", "online")
            db_device.agent_version = validated_data.get("agent_version")
            db_device.last_seen = datetime.utcnow()
            
            db.commit()
            
            return {
                "status": "success",
                "device_id": device_id_str,
                "message": "Heartbeat received"
            }
        else:
            return {
                "status": "warning",
                "device_id": device_id_str,
                "message": "Device not found in database"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in agent_heartbeat: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/status")
async def get_endpoint_status():
    """Get status of secure events endpoint."""
    return {
        "status": "active",
        "endpoint": "secure_events",
        "authentication": "HMAC-SHA256",
        "version": "1.0.0"
    }
