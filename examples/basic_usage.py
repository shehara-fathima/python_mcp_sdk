from mcp_sdk.client import AidenMCP
import asyncio

client = AidenMCP(api_key="xxx-xxx-xxx")

# Sync call
response = client.generate(model="debugger", prompt="Fix this error", context={"logs": "stacktrace here"})
print("Sync response:", response.response)

# Async call
async def main():
    response = await client.async_generate(model="codegen", prompt="Generate a class in Python", context={})
    print("Async response:", response.response)

asyncio.run(main())
