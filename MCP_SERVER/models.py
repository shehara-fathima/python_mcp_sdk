
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional, Literal
from enum import Enum
import uuid

class ModelType(str, Enum):
    """Supported model types for routing."""
    AIDEN_7B = "aiden-7b"
    CODEGEN = "codegen"
    DEBUGGER = "debugger"

class MCPRequest(BaseModel):
    """MCP (Model Control Protocol) request model."""

    model: ModelType = Field(
        ...,
        description="Model identifier for request routing",
        example="aiden-7b"
    )

    prompt: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="The prompt/query to process",
        example="Generate a Python function to calculate fibonacci numbers"
    )

    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context for the request",
        example={"language": "python", "difficulty": "intermediate"}
    )

    request_id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique request identifier"
    )

    max_tokens: Optional[int] = Field(
        default=2048,
        ge=1,
        le=8192,
        description="Maximum number of tokens to generate"
    )

    temperature: Optional[float] = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature for generation"
    )

    @validator('prompt')
    def validate_prompt(cls, v):
        """Validate prompt content."""
        if not v.strip():
            raise ValueError("Prompt cannot be empty or only whitespace")
        return v.strip()

    @validator('context')
    def validate_context(cls, v):
        """Validate context object."""
        # Ensure context doesn't contain sensitive information
        sensitive_keys = ['password', 'api_key', 'secret', 'token']
        for key in v.keys():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                raise ValueError(f"Context cannot contain sensitive key: {key}")
        return v

class MCPResponse(BaseModel):
    """MCP (Model Control Protocol) response model."""

    request_id: str = Field(
        ...,
        description="Original request identifier"
    )

    model: ModelType = Field(
        ...,
        description="Model that processed the request"
    )

    response: str = Field(
        ...,
        description="Generated response from the model"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional response metadata"
    )

    processing_time: float = Field(
        ...,
        description="Processing time in seconds"
    )

    success: bool = Field(
        default=True,
        description="Whether the request was processed successfully"
    )

class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(
        ...,
        description="Error type"
    )

    message: str = Field(
        ...,
        description="Error message"
    )

    request_id: Optional[str] = Field(
        None,
        description="Request identifier if available"
    )

    timestamp: int = Field(
        ...,
        description="Error timestamp"
    )

class ModelCapabilities(BaseModel):
    """Model capabilities information."""

    model_type: ModelType
    max_tokens: int
    supported_languages: list[str]
    specializations: list[str]
    description: str

# Model registry for capabilities
MODEL_CAPABILITIES = {
    ModelType.AIDEN_7B: ModelCapabilities(
        model_type=ModelType.AIDEN_7B,
        max_tokens=4096,
        supported_languages=["python", "javascript", "java", "cpp", "rust", "go"],
        specializations=["general_coding", "code_generation", "debugging"],
        description="General-purpose 7B parameter model for code generation and debugging"
    ),
    ModelType.CODEGEN: ModelCapabilities(
        model_type=ModelType.CODEGEN,
        max_tokens=8192,
        supported_languages=["python", "javascript", "typescript", "java", "cpp", "c", "rust", "go"],
        specializations=["code_generation", "boilerplate", "algorithms", "data_structures"],
        description="Specialized model optimized for code generation tasks"
    ),
    ModelType.DEBUGGER: ModelCapabilities(
        model_type=ModelType.DEBUGGER,
        max_tokens=6144,
        supported_languages=["python", "javascript", "java", "cpp", "rust"],
        specializations=["debugging", "error_analysis", "code_review", "optimization"],
        description="Specialized model for debugging and code analysis tasks"
    )
}

class HealthResponse(BaseModel):
    """Health check response model."""

    status: Literal["healthy", "unhealthy"]
    redis: Literal["connected", "disconnected", "error"]
    timestamp: int
    uptime: Optional[float] = None
    requests_processed: Optional[int] = None
