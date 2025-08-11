
from fastapi import HTTPException, Security, Depends, status
from fastapi.security.api_key import APIKeyHeader
import os
import hashlib
import hmac
import time
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# API Key configuration
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Load valid API keys from environment or configuration
# In production, these should be loaded from a secure database or secrets manager
VALID_API_KEYS = {
    # Example API keys - replace with your actual keys
    "mcp-key-dev-123": {
        "name": "Development Key",
        "rate_limit": 100,  # requests per minute
        "permissions": ["read", "write"],
        "created": "2024-01-01"
    },
    "mcp-key-prod-456": {
        "name": "Production Key", 
        "rate_limit": 1000,
        "permissions": ["read", "write"],
        "created": "2024-01-01"
    }
}

# Load additional API keys from environment variables
env_api_key = os.getenv("MCP_API_KEY")
if env_api_key:
    VALID_API_KEYS[env_api_key] = {
        "name": "Environment Key",
        "rate_limit": 500,
        "permissions": ["read", "write"],
        "created": "2024-01-01"
    }

def validate_api_key(api_key: str) -> bool:
    """
    Validate API key against stored keys.

    Args:
        api_key: The API key to validate

    Returns:
        bool: True if valid, False otherwise
    """
    if not api_key:
        return False

    # Check against valid keys
    if api_key in VALID_API_KEYS:
        return True

    # In production, you might want to check against a database
    # or use more sophisticated validation (e.g., JWT tokens)
    return False

def get_api_key_info(api_key: str) -> Optional[dict]:
    """
    Get API key information including permissions and rate limits.

    Args:
        api_key: The API key

    Returns:
        dict: API key information or None if invalid
    """
    return VALID_API_KEYS.get(api_key)

async def get_api_key(api_key_header: str = Security(api_key_header)) -> str:
    """
    Dependency to extract and validate API key from request headers.

    Args:
        api_key_header: API key from request header

    Returns:
        str: Validated API key

    Raises:
        HTTPException: If API key is missing or invalid
    """
    if not api_key_header:
        logger.warning("API request without API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Please provide a valid API key in the X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if not validate_api_key(api_key_header):
        logger.warning(f"Invalid API key attempted: {api_key_header[:10]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key. Please check your API key and try again.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    logger.info(f"Valid API key authenticated: {api_key_header[:10]}...")
    return api_key_header

def generate_api_key(prefix: str = "mcp-key") -> str:
    """
    Generate a new API key.

    Args:
        prefix: Prefix for the API key

    Returns:
        str: Generated API key
    """
    import secrets
    import string

    # Generate a random suffix
    suffix = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    return f"{prefix}-{suffix}"

def hash_api_key(api_key: str, salt: str = None) -> str:
    """
    Hash an API key for secure storage.

    Args:
        api_key: The API key to hash
        salt: Optional salt for hashing

    Returns:
        str: Hashed API key
    """
    if salt is None:
        salt = os.getenv("API_KEY_SALT", "default-salt-change-in-production")

    return hashlib.pbkdf2_hex(
        api_key.encode('utf-8'),
        salt.encode('utf-8'),
        100000  # iterations
    )

class APIKeyManager:
    """Manager class for API key operations."""

    def __init__(self):
        self.keys = VALID_API_KEYS.copy()

    def add_key(self, api_key: str, info: dict) -> bool:
        """Add a new API key."""
        if api_key in self.keys:
            return False
        self.keys[api_key] = info
        return True

    def revoke_key(self, api_key: str) -> bool:
        """Revoke an API key."""
        if api_key in self.keys:
            del self.keys[api_key]
            return True
        return False

    def list_keys(self) -> dict:
        """List all API keys (without showing the actual keys)."""
        return {
            key[:10] + "...": info 
            for key, info in self.keys.items()
        }

    def get_key_permissions(self, api_key: str) -> list:
        """Get permissions for an API key."""
        info = self.keys.get(api_key, {})
        return info.get("permissions", [])

    def get_key_rate_limit(self, api_key: str) -> int:
        """Get rate limit for an API key."""
        info = self.keys.get(api_key, {})
        return info.get("rate_limit", 60)  # default 60 requests per minute

# Global API key manager instance
api_key_manager = APIKeyManager()

def require_permission(permission: str):
    """
    Dependency factory to require specific permissions.

    Args:
        permission: Required permission

    Returns:
        Dependency function
    """
    async def permission_checker(api_key: str = Depends(get_api_key)) -> str:
        permissions = api_key_manager.get_key_permissions(api_key)
        if permission not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {permission}"
            )
        return api_key

    return permission_checker
