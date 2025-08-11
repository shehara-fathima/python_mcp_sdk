# MCP FastAPI Server

## Overview
This project is a scalable FastAPI server for handling Model Control Protocol (MCP) requests. It is designed to route requests to different AI model services (such as code generation and debugging), enforce API key security, and provide rate limiting and logging. The server is modular, extensible, and ready for production or research use.

## Features
- **FastAPI-based**: High-performance, async Python web server
- **API Key Security**: Protects endpoints with API key authentication
- **Rate Limiting**: Per-key or per-client rate limiting (Redis or in-memory)
- **Code Generation & Debugging**: Specialized endpoints for codegen and debugging models
- **Extensible Routers**: Easily add new model types or endpoints
- **Comprehensive Logging**: Info and error logs for all requests and errors
- **Health Checks**: Endpoints for service and model health
- **Environment-based Configuration**: Uses `.env` and `config.py` for settings

## Project Structure
```
MCP_SERVER/
├── __init__.py
├── auth.py              # API key management and authentication
├── codegen_router.py    # Endpoints for code generation
├── config.py            # App and environment configuration
├── degubber_router.py   # Endpoints for code debugging
├── main.py              # FastAPI app setup and router inclusion
├── middleware.py        # Custom middleware (rate limiting, logging)
├── models.py            # Pydantic models for requests/responses
├── requirements.txt     # Python dependencies
├── services.py          # Model routing and core logic
├── start_server.py      # Production server startup script
├── test_client.py       # (Legacy) server startup script
├── api_test_script.py   # Script to test all main endpoints
```

## Setup & Installation
1. **Clone the repository**
2. **Install dependencies**:
   ```sh
   pip install -r requirements.txt
   ```
3. **(Optional) Set environment variables** in a `.env` file or your shell (see `config.py` for options)

## Running the Server
- **Development:**
  ```sh
  python start_server.py
  ```
- The server will start on `http://localhost:8000` by default.
- API docs available at `http://localhost:8000/docs`

## API Usage
### Authentication
- All main endpoints require an API key in the `X-API-Key` header.
- Example keys are defined in `auth.py` (e.g., `mcp-key-dev-123`).

### Main Endpoints
- `GET /` — Root info
- `GET /health` — Server health
- `POST /mcp` — General MCP request (routes to appropriate model)
- `GET /api/v1/codegen/capabilities` — Codegen model capabilities
- `POST /api/v1/codegen/generate` — Generate code (requires `write` permission)
- `GET /api/v1/codegen/templates` — Code templates
- `GET /api/v1/codegen/health` — Codegen health
- `GET /api/v1/debugger/capabilities` — Debugger model capabilities
- `POST /api/v1/debugger/analyze` — Analyze code for bugs/errors
- `GET /api/v1/debugger/best-practices` — Coding best practices
- `GET /api/v1/debugger/health` — Debugger health

### Example Request (with `httpx`)
```python
import httpx
headers = {"X-API-Key": "mcp-key-dev-123"}
payload = {
    "model": "aiden-7b",
    "prompt": "Generate a Python function to add two numbers",
    "context": {"language": "python"}
}
resp = httpx.post("http://localhost:8000/api/v1/codegen/generate", headers=headers, json=payload)
print(resp.json())
```

## Testing
- Use `api_test_script.py` to test all main endpoints automatically:
  ```sh
  python api_test_script.py
  ```
- The script prints status and response for each endpoint.

## Extending the Project
- **Add new models**: Implement new handlers in `services.py` and register them in `ModelRouter`.
- **Add new endpoints**: Create new routers (see `codegen_router.py`, `degubber_router.py`).
- **Change rate limiting**: Update or extend `middleware.py`.
- **Change API key logic**: Update `auth.py`.

## Contributing
- Fork the repo and submit pull requests.
- Please include tests and update documentation for new features.

## License
MIT License (or specify your own) 