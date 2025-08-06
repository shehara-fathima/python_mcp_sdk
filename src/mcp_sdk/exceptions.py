class MCPError(Exception):
    """Raised when MCP API encounters an error"""
    pass


# aiden_mcp/utils.py
import asyncio
from functools import wraps

def retry_async(retries: int = 3, delay: float = 1.0):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == retries - 1:
                        raise
                    await asyncio.sleep(delay * (2 ** attempt))
        return wrapper
    return decorator