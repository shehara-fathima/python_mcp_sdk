from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from enum import Enum
import uuid

class ModelType(str, Enum):
    AIDEN_7B = "aiden-7b"
    CODEGEN = "codegen"
    DEBUGGER = "debugger"

class MCPRequest(BaseModel):
    model: str
    prompt: str
    context: Dict[str, Any] = Field(default_factory=dict)
    request_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    max_tokens: int = 2048
    temperature: float = 0.7

class MCPResponse(BaseModel):
    request_id: str
    model: str
    response: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    processing_time: float
    success: bool