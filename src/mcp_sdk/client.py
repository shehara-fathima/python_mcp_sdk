import httpx
from typing import Optional, Dict, Any
from .models import MCPRequest, MCPResponse
from .exceptions import MCPError
from .utils import retry_async

class AidenMCP:
    def __init__(self, api_key: str, base_url: str = "http://localhost:8000"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}

    def generate(self, model: str, prompt: str, context: Optional[Dict[str, Any]] = None) -> MCPResponse:
        payload = MCPRequest(model=model, prompt=prompt, context=context or {})
        try:
            with httpx.Client() as client:
                resp = client.post(f"{self.base_url}/mcp", json=payload.dict(), headers=self.headers)
                resp.raise_for_status()
                return MCPResponse(**resp.json())
        except httpx.HTTPError as e:
            raise MCPError(f"HTTP error: {str(e)}")

    @retry_async(retries=3, delay=1)
    async def async_generate(self, model: str, prompt: str, context: Optional[Dict[str, Any]] = None) -> MCPResponse:
        payload = MCPRequest(model=model, prompt=prompt, context=context or {})
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{self.base_url}/mcp", json=payload.dict(), headers=self.headers)
            resp.raise_for_status()
            return MCPResponse(**resp.json())