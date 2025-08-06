from mcp_sdk.client import AidenMCP
from mcp_sdk.models import ModelType

client = AidenMCP(api_key="xxx-xxx-xxx", base_url="http://localhost:8000")

try:
    response = client.generate(model=ModelType.CODEGEN, prompt="Write a Python function to reverse a list")
    print("✅ SDK is working!")
    print("Generated code:", response.response)
except Exception as e:
    print("❌ SDK failed:", e)
