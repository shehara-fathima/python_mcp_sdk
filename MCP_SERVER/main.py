
from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.security.api_key import APIKeyHeader, APIKey
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import redis.asyncio as aioredis
from typing import Dict, Any, Optional
import json
import time
import logging
import os
from dataclasses import dataclass

from models import MCPRequest, MCPResponse, ModelType
from codegen_router import router as codegen_router
from degubber_router import router as debugger_router
from middleware import RateLimitMiddleware, LoggingMiddleware
from auth import get_api_key
from services import ModelRouter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Application state
@dataclass
class AppState:
    redis_client: Optional[aioredis.Redis] = None
    model_router: Optional[ModelRouter] = None

app_state = AppState()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    # Startup
    logger.info("Starting FastAPI MCP Server...")

    # Initialize Redis connection for rate limiting
    try:
        app_state.redis_client = await aioredis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379"),
            encoding="utf-8",
            decode_responses=True
        )
        await app_state.redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}. Rate limiting will use in-memory storage.")
        app_state.redis_client = None

    # Initialize model router
    app_state.model_router = ModelRouter()

    logger.info("FastAPI MCP Server startup complete")

    yield

    # Shutdown
    logger.info("Shutting down FastAPI MCP Server...")
    if app_state.redis_client:
        await app_state.redis_client.close()
    logger.info("FastAPI MCP Server shutdown complete")

# Create FastAPI app with lifespan
app = FastAPI(
    title="MCP FastAPI Server",
    description="Scalable FastAPI server for handling MCP (Model Control Protocol) requests",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(
    RateLimitMiddleware,
    redis_client_getter=lambda: app_state.redis_client
)
app.add_middleware(LoggingMiddleware)

# Include routers
app.include_router(codegen_router, prefix="/api/v1")
app.include_router(debugger_router, prefix="/api/v1")

@app.get("/")
async def root():
    """Root endpoint with server information."""
    return {
        "message": "MCP FastAPI Server",
        "version": "1.0.0",
        "status": "running",
        "documentation": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    redis_status = "connected" if app_state.redis_client else "disconnected"
    return {
        "status": "healthy",
        "redis": redis_status,
        "timestamp": int(time.time())
    }

@app.post("/mcp", response_model=MCPResponse)
async def handle_mcp_request(
    request: MCPRequest,
    api_key: APIKey = Depends(get_api_key)
) -> MCPResponse:
    """
    Handle MCP (Model Control Protocol) requests.

    Routes requests to appropriate models (codegen/debugger) based on the request.
    """
    try:
        logger.info(f"Processing MCP request for model: {request.model}")

        # Route to appropriate model handler
        response = await app_state.model_router.route_request(request)

        logger.info(f"MCP request processed successfully for model: {request.model}")
        return response

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Internal error processing MCP request: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
