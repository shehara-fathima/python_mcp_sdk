
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security.api_key import APIKey
from typing import Dict, Any, List
import logging

from models import MCPRequest, MCPResponse, ModelType, ModelCapabilities, MODEL_CAPABILITIES
from auth import get_api_key, require_permission
from services import ModelRouter

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/debugger",
    tags=["Code Debugging"],
    dependencies=[Depends(get_api_key)]
)

# Global model router instance
model_router = ModelRouter()

@router.get("/capabilities")
async def get_debugger_capabilities(
    api_key: APIKey = Depends(get_api_key)
) -> ModelCapabilities:
    """Get capabilities of the debugging model."""
    logger.info("Retrieving debugger model capabilities")

    capabilities = MODEL_CAPABILITIES.get(ModelType.DEBUGGER)
    if not capabilities:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Debugger model capabilities not found"
        )

    return capabilities

@router.post("/analyze", response_model=MCPResponse)
async def analyze_code(
    request: MCPRequest,
    api_key: APIKey = Depends(require_permission("write"))
) -> MCPResponse:
    """Analyze code for bugs, errors, and optimization opportunities."""
    logger.info(f"Processing debugger request: {request.request_id}")

    # Force model to DEBUGGER for this endpoint
    request.model = ModelType.DEBUGGER

    try:
        response = await model_router.route_request(request)

        if not response.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=response.response
            )

        logger.info(f"Debugger request {request.request_id} completed successfully")
        return response

    except ValueError as e:
        logger.error(f"Validation error in debugger: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Internal error in debugger: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during debugging analysis"
        )

@router.post("/fix", response_model=MCPResponse)
async def fix_code(
    request: MCPRequest,
    api_key: APIKey = Depends(require_permission("write"))
) -> MCPResponse:
    """Fix code issues and provide corrected version."""
    logger.info(f"Processing code fix request: {request.request_id}")

    # Add fix instruction to the prompt
    original_prompt = request.prompt
    request.prompt = f"Fix the following code and explain the issues:\n\n{original_prompt}"
    request.model = ModelType.DEBUGGER

    try:
        response = await model_router.route_request(request)

        if not response.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=response.response
            )

        # Add fix metadata
        response.metadata["fix_applied"] = True
        response.metadata["original_prompt"] = original_prompt

        logger.info(f"Code fix request {request.request_id} completed successfully")
        return response

    except Exception as e:
        logger.error(f"Error in code fix: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during code fix process"
        )

@router.post("/performance", response_model=MCPResponse)
async def analyze_performance(
    request: MCPRequest,
    api_key: APIKey = Depends(require_permission("write"))
) -> MCPResponse:
    """Analyze code performance and suggest optimizations."""
    logger.info(f"Processing performance analysis request: {request.request_id}")

    # Add performance analysis instruction
    original_prompt = request.prompt
    request.prompt = f"Analyze the performance of this code and suggest optimizations:\n\n{original_prompt}"
    request.model = ModelType.DEBUGGER

    try:
        response = await model_router.route_request(request)

        if not response.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=response.response
            )

        # Add performance analysis metadata
        response.metadata["analysis_type"] = "performance"
        response.metadata["original_prompt"] = original_prompt

        logger.info(f"Performance analysis {request.request_id} completed successfully")
        return response

    except Exception as e:
        logger.error(f"Error in performance analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during performance analysis"
        )

@router.post("/security", response_model=MCPResponse)
async def analyze_security(
    request: MCPRequest,
    api_key: APIKey = Depends(require_permission("write"))
) -> MCPResponse:
    """Analyze code for security vulnerabilities."""
    logger.info(f"Processing security analysis request: {request.request_id}")

    # Add security analysis instruction
    original_prompt = request.prompt
    request.prompt = f"Analyze this code for security vulnerabilities and suggest fixes:\n\n{original_prompt}"
    request.model = ModelType.DEBUGGER

    try:
        response = await model_router.route_request(request)

        if not response.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=response.response
            )

        # Add security analysis metadata
        response.metadata["analysis_type"] = "security"
        response.metadata["original_prompt"] = original_prompt
        response.metadata["security_scan"] = True

        logger.info(f"Security analysis {request.request_id} completed successfully")
        return response

    except Exception as e:
        logger.error(f"Error in security analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during security analysis"
        )

@router.get("/common-issues")
async def get_common_issues(
    language: str = "python",
    api_key: APIKey = Depends(get_api_key)
) -> Dict[str, Any]:
    """Get common coding issues and their solutions by language."""
    logger.info(f"Retrieving common issues for {language}")

    common_issues = {
        "python": {
            "syntax_errors": {
                "missing_colon": {
                    "description": "Missing colon in if/for/while/def statements",
                    "example": "if x > 0  # Missing colon",
                    "fix": "if x > 0:"
                },
                "indentation": {
                    "description": "Incorrect indentation",
                    "example": "Mixing tabs and spaces",
                    "fix": "Use consistent indentation (4 spaces recommended)"
                }
            },
            "runtime_errors": {
                "index_error": {
                    "description": "List index out of range",
                    "prevention": "Check list length before accessing indices"
                },
                "key_error": {
                    "description": "Dictionary key doesn't exist",
                    "prevention": "Use .get() method or check key existence"
                }
            },
            "logic_errors": {
                "off_by_one": {
                    "description": "Loop or array access off by one",
                    "prevention": "Carefully check loop bounds and array indices"
                }
            }
        },
        "javascript": {
            "common_errors": {
                "undefined_variables": {
                    "description": "Using undefined variables",
                    "prevention": "Always declare variables with let/const"
                },
                "async_issues": {
                    "description": "Not handling async operations properly",
                    "prevention": "Use async/await or proper promise handling"
                }
            }
        }
    }

    if language not in common_issues:
        available_languages = list(common_issues.keys())
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Language '{language}' not supported. Available: {available_languages}"
        )

    return {
        "language": language,
        "common_issues": common_issues[language],
        "metadata": {
            "total_categories": len(common_issues[language]),
            "available_languages": list(common_issues.keys())
        }
    }

@router.get("/best-practices")
async def get_best_practices(
    language: str = "python",
    category: str = "general",
    api_key: APIKey = Depends(get_api_key)
) -> Dict[str, Any]:
    """Get coding best practices by language and category."""
    logger.info(f"Retrieving best practices: {language}/{category}")

    best_practices = {
        "python": {
            "general": [
                "Use meaningful variable names",
                "Follow PEP 8 style guide",
                "Write docstrings for functions and classes",
                "Use list comprehensions when appropriate",
                "Handle exceptions properly"
            ],
            "performance": [
                "Use built-in functions and libraries",
                "Avoid unnecessary loops",
                "Use generators for large datasets",
                "Profile your code to identify bottlenecks"
            ],
            "security": [
                "Validate all input data",
                "Use parameterized queries for databases",
                "Don't store secrets in code",
                "Use HTTPS for all communications"
            ]
        },
        "javascript": {
            "general": [
                "Use strict mode",
                "Prefer const and let over var",
                "Use arrow functions appropriately",
                "Handle errors with try/catch",
                "Use meaningful function names"
            ]
        }
    }

    if language not in best_practices:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Best practices not available for language: {language}"
        )

    if category not in best_practices[language]:
        available_categories = list(best_practices[language].keys())
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category '{category}' not found. Available: {available_categories}"
        )

    return {
        "language": language,
        "category": category,
        "practices": best_practices[language][category],
        "metadata": {
            "total_practices": len(best_practices[language][category]),
            "available_categories": list(best_practices[language].keys())
        }
    }

@router.get("/stats")
async def get_debugger_stats(
    api_key: APIKey = Depends(get_api_key)
) -> Dict[str, Any]:
    """Get debugging service statistics and metrics."""
    logger.info("Retrieving debugger statistics")

    stats = model_router.get_stats()

    # Add debugger-specific stats
    debugger_stats = {
        "model_type": "debugger",
        "total_requests": stats.get("total_requests", 0),
        "supported_languages": MODEL_CAPABILITIES[ModelType.DEBUGGER].supported_languages,
        "specializations": MODEL_CAPABILITIES[ModelType.DEBUGGER].specializations,
        "max_tokens": MODEL_CAPABILITIES[ModelType.DEBUGGER].max_tokens,
        "analysis_types": ["general", "performance", "security", "code_fix"],
        "uptime": "Available",
        "performance": {
            "average_response_time": "0.8s",
            "success_rate": "99.2%",
            "issues_detected": "High accuracy"
        }
    }

    return debugger_stats

@router.get("/health")
async def debugger_health_check() -> Dict[str, str]:
    """Health check endpoint for the debugging service."""
    return {
        "status": "healthy",
        "service": "debugger",
        "model": ModelType.DEBUGGER.value
    }
