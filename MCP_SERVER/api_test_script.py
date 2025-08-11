import httpx

API_KEY = "mcp-key-dev-123"  # Use a valid key from your auth.py
BASE_URL = "http://localhost:8000"

headers = {"X-API-Key": API_KEY}

def print_result(endpoint, resp):
    print(f"\n=== {endpoint} ===")
    print(f"Status: {resp.status_code}")
    try:
        print(resp.json())
    except Exception:
        print(resp.text)

def main():
    with httpx.Client() as client:
        # Test root
        resp = client.get(f"{BASE_URL}/", headers=headers)
        print_result("/", resp)

        # Test health
        resp = client.get(f"{BASE_URL}/health", headers=headers)
        print_result("/health", resp)

        # Test codegen capabilities
        resp = client.get(f"{BASE_URL}/api/v1/codegen/capabilities", headers=headers)
        print_result("/api/v1/codegen/capabilities", resp)

        # Test codegen generate
        payload = {
            "model": "aiden-7b",
            "prompt": "Generate a Python function to add two numbers",
            "context": {"language": "python"},
        }
        resp = client.post(f"{BASE_URL}/api/v1/codegen/generate", headers=headers, json=payload)
        print_result("/api/v1/codegen/generate", resp)

        # Test codegen templates
        resp = client.get(f"{BASE_URL}/api/v1/codegen/templates?language=python&category=api", headers=headers)
        print_result("/api/v1/codegen/templates", resp)

        # Test codegen health
        resp = client.get(f"{BASE_URL}/api/v1/codegen/health", headers=headers)
        print_result("/api/v1/codegen/health", resp)

        # Test debugger capabilities
        resp = client.get(f"{BASE_URL}/api/v1/debugger/capabilities", headers=headers)
        print_result("/api/v1/debugger/capabilities", resp)

        # Test debugger analyze
        payload = {
            "model": "aiden-7b",
            "prompt": "Find bugs in this code: def foo(x): return x+1",
            "context": {"language": "python"},
        }
        resp = client.post(f"{BASE_URL}/api/v1/debugger/analyze", headers=headers, json=payload)
        print_result("/api/v1/debugger/analyze", resp)

        # Test debugger best-practices
        resp = client.get(f"{BASE_URL}/api/v1/debugger/best-practices?language=python&category=general", headers=headers)
        print_result("/api/v1/debugger/best-practices", resp)

        # Test debugger health
        resp = client.get(f"{BASE_URL}/api/v1/debugger/health", headers=headers)
        print_result("/api/v1/debugger/health", resp)

if __name__ == "__main__":
    main() 