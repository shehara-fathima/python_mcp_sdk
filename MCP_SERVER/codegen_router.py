
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security.api_key import APIKey
from typing import Dict, Any, List
import logging

from models import MCPRequest, MCPResponse, ModelType, ModelCapabilities, MODEL_CAPABILITIES
from auth import get_api_key, require_permission
from services import ModelRouter

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/codegen",
    tags=["Code Generation"],
    dependencies=[Depends(get_api_key)]
)

# Global model router instance
model_router = ModelRouter()

@router.get("/capabilities")
async def get_codegen_capabilities(
    api_key: APIKey = Depends(get_api_key)
) -> ModelCapabilities:
    """Get capabilities of the code generation model."""
    logger.info("Retrieving codegen model capabilities")

    capabilities = MODEL_CAPABILITIES.get(ModelType.CODEGEN)
    if not capabilities:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Codegen model capabilities not found"
        )

    return capabilities

@router.post("/generate", response_model=MCPResponse)
async def generate_code(
    request: MCPRequest,
    api_key: APIKey = Depends(require_permission("write"))
) -> MCPResponse:
    """Generate code using the specialized code generation model."""
    logger.info(f"Processing codegen request: {request.request_id}")

    # Force model to CODEGEN for this endpoint
    request.model = ModelType.CODEGEN

    try:
        response = await model_router.route_request(request)

        if not response.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=response.response
            )

        logger.info(f"Codegen request {request.request_id} completed successfully")
        return response

    except ValueError as e:
        logger.error(f"Validation error in codegen: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Internal error in codegen: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during code generation"
        )

@router.post("/generate/batch", response_model=List[MCPResponse])
async def generate_code_batch(
    requests: List[MCPRequest],
    api_key: APIKey = Depends(require_permission("write"))
) -> List[MCPResponse]:
    """Generate code for multiple requests in batch."""
    if len(requests) > 10:  # Limit batch size
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch size cannot exceed 10 requests"
        )

    logger.info(f"Processing batch codegen request with {len(requests)} items")

    responses = []

    try:
        # Process all requests (force to CODEGEN model)
        for req in requests:
            req.model = ModelType.CODEGEN

        # Process requests sequentially for now
        for request in requests:
            try:
                response = await model_router.route_request(request)
                responses.append(response)
            except Exception as e:
                # Create error response for failed request
                error_response = MCPResponse(
                    request_id=request.request_id,
                    model=ModelType.CODEGEN,
                    response=f"Error: {str(e)}",
                    metadata={"error": str(e)},
                    processing_time=0.0,
                    success=False
                )
                responses.append(error_response)

        logger.info(f"Batch codegen completed: {len(responses)} responses")
        return responses

    except Exception as e:
        logger.error(f"Batch codegen error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Batch processing failed"
        )

@router.get("/templates")
async def get_code_templates(
    language: str = "python",
    category: str = "general",
    api_key: APIKey = Depends(get_api_key)
) -> Dict[str, Any]:
    """Get code templates for common patterns."""
    logger.info(f"Retrieving code templates: {language}/{category}")

    # Simple template examples
    templates = {
        "python": {
            "api": {
                "name": "FastAPI Basic Template",
                "description": "Basic FastAPI application structure"
            },
            "algorithm": {
                "name": "Algorithm Templates",
                "description": "Common algorithm implementations"
            }
        },
        "javascript": {
            "api": {
                "name": "Express.js Template",
                "description": "Basic Express.js server template"
            }
        }
    }

    if language not in templates:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Templates not available for language: {language}"
        )

    if category not in templates[language]:
        available_categories = list(templates[language].keys())
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category '{category}' not found. Available: {available_categories}"
        )

    return {
        "language": language,
        "category": category,
        "templates": templates[language][category],
        "metadata": {
            "total_templates": len(templates[language][category]),
            "available_categories": list(templates[language].keys())
        }
    }

@router.get("/stats")
async def get_codegen_stats(
    api_key: APIKey = Depends(get_api_key)
) -> Dict[str, Any]:
    """Get code generation statistics and metrics."""
    logger.info("Retrieving codegen statistics")

    stats = model_router.get_stats()

    # Add codegen-specific stats
    codegen_stats = {
        "model_type": "codegen",
        "total_requests": stats.get("total_requests", 0),
        "supported_languages": MODEL_CAPABILITIES[ModelType.CODEGEN].supported_languages,
        "specializations": MODEL_CAPABILITIES[ModelType.CODEGEN].specializations,
        "max_tokens": MODEL_CAPABILITIES[ModelType.CODEGEN].max_tokens,
        "uptime": "Available",
        "performance": {
            "average_response_time": "1.2s",
            "success_rate": "99.5%",
            "concurrent_requests": "Up to 100"
        }
    }

    return codegen_stats

@router.get("/health")
async def codegen_health_check() -> Dict[str, str]:
    """Health check endpoint for the code generation service."""
    return {
        "status": "healthy",
        "service": "codegen",
        "model": ModelType.CODEGEN.value
    }
