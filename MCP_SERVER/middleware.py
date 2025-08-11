
import time
import json
import logging
from typing import Callable, Optional
from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using sliding window algorithm.

    Supports both Redis-based distributed rate limiting and 
    in-memory rate limiting for development.
    """

    def __init__(
        self,
        app,
        redis_client_getter: Callable[[], Optional[aioredis.Redis]] = None,
        default_rate_limit: int = 60,  # requests per minute
        window_size: int = 60,  # window size in seconds
    ):
        super().__init__(app)
        self.redis_client_getter = redis_client_getter
        self.default_rate_limit = default_rate_limit
        self.window_size = window_size

        # In-memory storage for when Redis is not available
        self.memory_store = defaultdict(list)
        self.memory_cleanup_time = time.time()

    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""

        # Skip rate limiting for health checks and docs
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        # Get client identifier (IP address or API key)
        client_id = self._get_client_id(request)

        # Get rate limit for this client
        rate_limit = await self._get_rate_limit(request)

        # Check rate limit
        allowed = await self._check_rate_limit(client_id, rate_limit)

        if not allowed:
            logger.warning(f"Rate limit exceeded for client: {client_id}")
            return Response(
                content=json.dumps({
                    "error": "rate_limit_exceeded",
                    "message": f"Rate limit of {rate_limit} requests per minute exceeded",
                    "retry_after": 60
                }),
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={
                    "Content-Type": "application/json",
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(rate_limit),
                    "X-RateLimit-Remaining": "0"
                }
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        remaining = await self._get_remaining_requests(client_id, rate_limit)
        response.headers["X-RateLimit-Limit"] = str(rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + self.window_size))

        return response

    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting."""
        # Try to get API key first
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api_key:{api_key[:10]}"

        # Fall back to IP address
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return f"ip:{forwarded_for.split(',')[0].strip()}"

        return f"ip:{request.client.host}"

    async def _get_rate_limit(self, request: Request) -> int:
        """Get rate limit for the request."""
        # Get API key info if available
        api_key = request.headers.get("X-API-Key")
        if api_key:
            # Import here to avoid circular imports
            from auth import api_key_manager
            try:
                return api_key_manager.get_key_rate_limit(api_key)
            except:
                pass

        return self.default_rate_limit

    async def _check_rate_limit(self, client_id: str, rate_limit: int) -> bool:
        """Check if request is within rate limit."""
        redis_client = self.redis_client_getter() if self.redis_client_getter else None

        if redis_client:
            return await self._check_rate_limit_redis(redis_client, client_id, rate_limit)
        else:
            return self._check_rate_limit_memory(client_id, rate_limit)

    async def _check_rate_limit_redis(
        self, 
        redis_client: aioredis.Redis, 
        client_id: str, 
        rate_limit: int
    ) -> bool:
        """Check rate limit using Redis sliding window."""
        try:
            current_time = time.time()
            window_start = current_time - self.window_size

            # Redis key for this client
            key = f"rate_limit:{client_id}"

            # Use Redis pipeline for atomic operations
            pipe = redis_client.pipeline()

            # Remove old entries
            pipe.zremrangebyscore(key, 0, window_start)

            # Count current requests in window
            pipe.zcard(key)

            # Add current request
            pipe.zadd(key, {str(current_time): current_time})

            # Set expiry
            pipe.expire(key, self.window_size)

            results = await pipe.execute()
            current_count = results[1]

            return current_count < rate_limit

        except Exception as e:
            logger.error(f"Redis rate limiting error: {e}")
            # Fall back to memory-based rate limiting
            return self._check_rate_limit_memory(client_id, rate_limit)

    def _check_rate_limit_memory(self, client_id: str, rate_limit: int) -> bool:
        """Check rate limit using in-memory storage."""
        current_time = time.time()
        window_start = current_time - self.window_size

        # Clean up old entries periodically
        if current_time - self.memory_cleanup_time > 300:  # Clean every 5 minutes
            self._cleanup_memory_store(current_time)
            self.memory_cleanup_time = current_time

        # Get request times for this client
        request_times = self.memory_store[client_id]

        # Remove old requests
        request_times[:] = [t for t in request_times if t > window_start]

        # Check if under limit
        if len(request_times) < rate_limit:
            request_times.append(current_time)
            return True

        return False

    def _cleanup_memory_store(self, current_time: float):
        """Clean up old entries from memory store."""
        window_start = current_time - self.window_size

        for client_id in list(self.memory_store.keys()):
            request_times = self.memory_store[client_id]
            request_times[:] = [t for t in request_times if t > window_start]

            # Remove empty entries
            if not request_times:
                del self.memory_store[client_id]

    async def _get_remaining_requests(self, client_id: str, rate_limit: int) -> int:
        """Get remaining requests for client."""
        redis_client = self.redis_client_getter() if self.redis_client_getter else None

        if redis_client:
            try:
                current_time = time.time()
                window_start = current_time - self.window_size
                key = f"rate_limit:{client_id}"

                # Count current requests
                current_count = await redis_client.zcount(key, window_start, current_time)
                return max(0, rate_limit - current_count)

            except Exception:
                pass

        # Fall back to memory store
        current_time = time.time()
        window_start = current_time - self.window_size
        request_times = self.memory_store[client_id]
        current_count = len([t for t in request_times if t > window_start])
        return max(0, rate_limit - current_count)

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive logging middleware for request/response tracking.
    """

    def __init__(self, app):
        super().__init__(app)
        self.logger = logging.getLogger("mcp_server.requests")

    async def dispatch(self, request: Request, call_next):
        """Process request with logging."""
        start_time = time.time()

        # Generate unique request ID
        request_id = f"req_{int(start_time * 1000)}"

        # Log request
        self.logger.info(
            f"Request started: {request_id} - {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": self._get_client_ip(request),
                "user_agent": request.headers.get("User-Agent", ""),
                "api_key": request.headers.get("X-API-Key", "")[:10] + "..." if request.headers.get("X-API-Key") else None
            }
        )

        # Process request
        try:
            response = await call_next(request)
            processing_time = time.time() - start_time

            # Log response
            self.logger.info(
                f"Request completed: {request_id} - {response.status_code} ({processing_time:.3f}s)",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "processing_time": processing_time,
                    "response_size": response.headers.get("Content-Length", "unknown")
                }
            )

            # Add processing time header
            response.headers["X-Processing-Time"] = f"{processing_time:.3f}s"
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            processing_time = time.time() - start_time

            # Log error
            self.logger.error(
                f"Request failed: {request_id} - {str(e)} ({processing_time:.3f}s)",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "processing_time": processing_time
                },
                exc_info=True
            )

            raise

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to responses.
    """

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        """Add security headers to response."""
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"

        return response
