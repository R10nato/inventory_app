"""
hmac_auth.py
HMAC authentication system for secure agent communication.
"""

import hmac
import hashlib
import json
import secrets
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

logger = logging.getLogger(__name__)


class HMACAuthenticator:
    """HMAC authentication for agent communications"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key.encode('utf-8')
    
    def generate_signature(self, payload: str) -> str:
        """
        Generate HMAC-SHA256 signature for payload.
        
        Args:
            payload: JSON string payload
            
        Returns:
            Hex-encoded HMAC signature
        """
        return hmac.new(
            self.secret_key,
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def verify_signature(self, payload: str, signature: str) -> bool:
        """
        Verify HMAC signature against payload.
        
        Args:
            payload: JSON string payload
            signature: Hex-encoded signature to verify
            
        Returns:
            True if signature is valid
        """
        expected_signature = self.generate_signature(payload)
        return hmac.compare_digest(expected_signature, signature)
    
    def create_signed_request(self, data: Dict[str, Any], api_token: str) -> Dict[str, str]:
        """
        Create headers for signed request.
        
        Args:
            data: Request data dictionary
            api_token: Bearer token
            
        Returns:
            Headers dictionary with authorization and signature
        """
        payload = json.dumps(data, sort_keys=True, default=str)
        signature = self.generate_signature(payload)
        
        return {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
            "X-Signature": signature,
            "X-Timestamp": datetime.utcnow().isoformat()
        }


class SecureEventReceiver:
    """Secure receiver for agent events with HMAC validation"""
    
    def __init__(self, secret_key: str, token_validator=None):
        self.authenticator = HMACAuthenticator(secret_key)
        self.token_validator = token_validator
        self.security = HTTPBearer()
    
    async def validate_request(self, request: Request, credentials: HTTPAuthorizationCredentials) -> Dict[str, Any]:
        """
        Validate incoming request with HMAC signature.
        
        Args:
            request: FastAPI request object
            credentials: Bearer token credentials
            
        Returns:
            Validated request data
            
        Raises:
            HTTPException: If validation fails
        """
        # Get signature from headers
        signature = request.headers.get("X-Signature")
        if not signature:
            raise HTTPException(status_code=401, detail="Missing X-Signature header")
        
        # Get timestamp for replay attack protection
        timestamp_str = request.headers.get("X-Timestamp")
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                if datetime.utcnow() - timestamp > timedelta(minutes=5):
                    raise HTTPException(status_code=401, detail="Request timestamp too old")
            except ValueError:
                raise HTTPException(status_code=401, detail="Invalid timestamp format")
        
        # Read request body
        body = await request.body()
        payload = body.decode('utf-8')
        
        # Verify HMAC signature
        if not self.authenticator.verify_signature(payload, signature):
            logger.warning(f"HMAC signature validation failed for token: {credentials.credentials[:8]}...")
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Validate bearer token if validator provided
        if self.token_validator:
            if not self.token_validator(credentials.credentials):
                raise HTTPException(status_code=401, detail="Invalid bearer token")
        
        # Parse and return validated data
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON payload")


def generate_agent_secret() -> str:
    """Generate cryptographically secure secret for agent."""
    return secrets.token_urlsafe(32)


def simple_token_validator(token: str) -> bool:
    """
    Simple token validator - replace with your authentication logic.
    
    Args:
        token: Bearer token to validate
        
    Returns:
        True if token is valid
    """
    # TODO: Implement proper token validation
    # This could check against database, JWT validation, etc.
    valid_tokens = {
        "agent_token_123",  # Example tokens
        "agent_token_456",
    }
    return token in valid_tokens


# Global authenticator instance
_authenticator: Optional[HMACAuthenticator] = None
_receiver: Optional[SecureEventReceiver] = None


def init_hmac_auth(secret_key: str, token_validator=None):
    """Initialize global HMAC authentication."""
    global _authenticator, _receiver
    _authenticator = HMACAuthenticator(secret_key)
    _receiver = SecureEventReceiver(secret_key, token_validator or simple_token_validator)


def get_authenticator() -> HMACAuthenticator:
    """Get global authenticator instance."""
    if _authenticator is None:
        raise RuntimeError("HMAC authenticator not initialized. Call init_hmac_auth() first.")
    return _authenticator


def get_receiver() -> SecureEventReceiver:
    """Get global secure receiver instance."""
    if _receiver is None:
        raise RuntimeError("Secure receiver not initialized. Call init_hmac_auth() first.")
    return _receiver


if __name__ == "__main__":
    # Test HMAC authentication
    secret = generate_agent_secret()
    print(f"Generated secret: {secret}")
    
    auth = HMACAuthenticator(secret)
    
    test_data = {"device_id": "test", "events": [{"type": "test"}]}
    test_payload = json.dumps(test_data, sort_keys=True)
    
    signature = auth.generate_signature(test_payload)
    print(f"Generated signature: {signature}")
    
    is_valid = auth.verify_signature(test_payload, signature)
    print(f"Signature valid: {is_valid}")
    
    # Test with wrong signature
    wrong_sig = auth.generate_signature('{"wrong": "data"}')
    is_invalid = auth.verify_signature(test_payload, wrong_sig)
    print(f"Wrong signature valid: {is_invalid}")
