# Aiden MCP SDK

A simple Python SDK for interacting with the Aiden MCP FastAPI server.

## Installation
```bash
pip install .
```

## Usage
```python
from aiden_mcp.client import AidenMCP
client = AidenMCP(api_key="mcp-key-dev-123")

response = client.generate(
    model="debugger",
    prompt="Fix this error",
    context={"logs": "Traceback..."}
)
print(response.response)
```

### Async Version
```python
import asyncio
async def main():
    response = await client.async_generate(
        model="codegen",
        prompt="Generate Python class",
        context={}
    )
    print(response.response)

asyncio.run(main())
```

