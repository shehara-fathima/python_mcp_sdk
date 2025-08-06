import asyncio
from mcp_sdk.client import AidenMCP
from mcp_sdk.models import ModelType

async def test_async():
    client = AidenMCP(api_key="xxx-xxx-xxx")
    response = await client.async_generate(model=ModelType.CODEGEN, prompt="Generate a Fibonacci sequence")
    print("Generated:", response.response)

asyncio.run(test_async())
