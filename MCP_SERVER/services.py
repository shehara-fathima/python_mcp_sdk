
import asyncio
import time
import logging
import traceback
from typing import Dict, Any, Optional
from models import MCPRequest, MCPResponse, ModelType, MODEL_CAPABILITIES

logger = logging.getLogger(__name__)

class ModelRouter:
    """
    Router service for handling MCP requests to different models.

    Routes requests to appropriate model handlers based on model type
    and manages the request processing pipeline.
    """

    def __init__(self):
        self.model_handlers = {
            ModelType.AIDEN_7B: self._handle_aiden_7b,
            ModelType.CODEGEN: self._handle_codegen,
            ModelType.DEBUGGER: self._handle_debugger
        }
        self.request_count = 0

    async def route_request(self, request: MCPRequest) -> MCPResponse:
        """
        Route MCP request to appropriate model handler.

        Args:
            request: The MCP request to process

        Returns:
            MCPResponse: The processed response

        Raises:
            ValueError: If model type is not supported
        """
        start_time = time.time()
        self.request_count += 1

        logger.info(f"Routing request {request.request_id} to model {request.model}")

        # Validate model type
        if request.model not in self.model_handlers:
            raise ValueError(f"Unsupported model type: {request.model}")

        # Check model capabilities
        capabilities = MODEL_CAPABILITIES.get(request.model)
        if not capabilities:
            raise ValueError(f"No capabilities defined for model: {request.model}")

        # Validate request against model capabilities
        if request.max_tokens > capabilities.max_tokens:
            request.max_tokens = capabilities.max_tokens
            logger.warning(f"Reduced max_tokens to {capabilities.max_tokens} for model {request.model}")

        try:
            # Route to appropriate handler
            handler = self.model_handlers[request.model]
            response_text = await handler(request)

            processing_time = time.time() - start_time

            # Create response
            response = MCPResponse(
                request_id=request.request_id,
                model=request.model,
                response=response_text,
                metadata={
                    "model_capabilities": capabilities.dict(),
                    "input_tokens": len(request.prompt.split()),
                    "output_tokens": len(response_text.split()),
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens
                },
                processing_time=processing_time,
                success=True
            )

            logger.info(f"Request {request.request_id} processed successfully in {processing_time:.3f}s")
            return response

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error processing request {request.request_id}: {e}")
            logger.error(traceback.format_exc())

            # Return error response
            return MCPResponse(
                request_id=request.request_id,
                model=request.model,
                response=f"Error processing request: {str(e)}",
                metadata={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "traceback": traceback.format_exc()
                },
                processing_time=processing_time,
                success=False
            )

    async def _handle_aiden_7b(self, request: MCPRequest) -> str:
        """Handle requests for the AIDEN-7B model."""
        logger.info(f"Processing with AIDEN-7B model: {request.request_id}")

        # Simulate model processing
        await asyncio.sleep(0.5)

        language = request.context.get("language", "python")

        # Generate response based on prompt content
        if any(keyword in request.prompt.lower() for keyword in ["debug", "fix", "error", "bug"]):
            return self._generate_debugging_response(request.prompt, language)
        elif any(keyword in request.prompt.lower() for keyword in ["generate", "create", "write"]):
            return self._generate_code_response(request.prompt, language)
        else:
            return self._generate_general_response(request.prompt, language)

    async def _handle_codegen(self, request: MCPRequest) -> str:
        """Handle requests for the CODEGEN model."""
        logger.info(f"Processing with CODEGEN model: {request.request_id}")
        await asyncio.sleep(1.0)

        language = request.context.get("language", "python")
        return self._generate_advanced_code_response(request.prompt, language)

    async def _handle_debugger(self, request: MCPRequest) -> str:
        """Handle requests for the DEBUGGER model."""
        logger.info(f"Processing with DEBUGGER model: {request.request_id}")
        await asyncio.sleep(0.8)

        language = request.context.get("language", "python")
        code_snippet = request.context.get("code", "")

        return self._generate_debugging_analysis(request.prompt, language, code_snippet)

    def _generate_code_response(self, prompt: str, language: str) -> str:
        """Generate a code response based on the prompt."""

        if "fibonacci" in prompt.lower() and language.lower() == "python":
            return '''def fibonacci(n):
    """Generate fibonacci sequence up to n terms."""
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]

    sequence = [0, 1]
    for i in range(2, n):
        sequence.append(sequence[i-1] + sequence[i-2])

    return sequence

# Example usage:
print(fibonacci(10))  # [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]'''

        elif "factorial" in prompt.lower() and language.lower() == "python":
            return '''def factorial(n):
    """Calculate factorial of n using recursion."""
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    elif n == 0 or n == 1:
        return 1
    else:
        return n * factorial(n - 1)

# Example usage:
print(factorial(5))  # 120'''

        else:
            return f'''# Generated {language} code for: {prompt}

def main():
    """Main function implementation."""
    print("Generated code based on prompt")
    # Add your implementation here
    pass

if __name__ == "__main__":
    main()
'''

    def _generate_debugging_response(self, prompt: str, language: str) -> str:
        """Generate a debugging response."""
        return f'''# Debugging Analysis for {language}

## Issue Analysis:
{prompt}

## Potential Issues:
1. Syntax Error: Check for missing colons, parentheses, or indentation issues
2. Logic Error: Verify the algorithm logic and edge cases
3. Type Error: Ensure variable types match expected operations
4. Runtime Error: Check for division by zero, index out of bounds, etc.

## Debugging Steps:
1. Add print statements to trace variable values
2. Use a debugger to step through the code
3. Check input validation and error handling
4. Verify function return types and values

## Best Practices:
- Always validate inputs
- Use meaningful variable names
- Add proper error handling
- Include unit tests
- Add logging for debugging
'''

    def _generate_general_response(self, prompt: str, language: str) -> str:
        """Generate a general purpose response."""
        return f'''# Response to: {prompt}

This is a general response for your query about {language} programming.

## Key Points:
- Understanding the problem requirements
- Choosing the right approach and data structures  
- Writing clean, readable code
- Testing and debugging thoroughly

## Next Steps:
1. Refine the requirements
2. Implement the solution
3. Test with various inputs
4. Optimize if needed

Would you like me to provide a more specific solution?
'''

    def _generate_advanced_code_response(self, prompt: str, language: str) -> str:
        """Generate advanced code response from CODEGEN model."""
        return f"""# Advanced {language} Code Generation
# Optimized for production use

\"\"\"
Generated code for: {prompt}
This implementation includes error handling, type hints, and best practices.
\"\"\"

import asyncio
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class AdvancedSolution:
    \"\"\"Production-ready implementation.\"\"\"

    def __init__(self):
        self.initialized = False
        self._setup()

    def _setup(self):
        \"\"\"Initialize the solution.\"\"\"
        logger.info("Setting up advanced solution")
        self.initialized = True

    async def process(self, data: Dict) -> Dict:
        \"\"\"Process input data and return results.\"\"\"
        if not self.initialized:
            raise RuntimeError("Solution not initialized")

        try:
            result = await self._process_data(data)
            logger.info("Processing completed")
            return result

        except Exception as e:
            logger.error(f"Processing failed: {{e}}")
            raise

    async def _process_data(self, data: Dict) -> Dict:
        \"\"\"Internal processing method.\"\"\"
        await asyncio.sleep(0.1)
        return {{\"processed\": True, \"input\": data}}

# Usage example
async def main():
    solution = AdvancedSolution()
    result = await solution.process({{\"key\": \"value\"}})
    print(f"Result: {{result}}")

if __name__ == \"__main__\":
    asyncio.run(main())
"""

    
    def _generate_debugging_analysis(self, prompt: str, language: str, code_snippet: str) -> str:
        """Generate detailed debugging analysis."""
        analysis = (
            f"""# Debugging Analysis Report
# Language: {language}
# Analysis for: {prompt}

## Code Analysis:
{code_snippet if code_snippet else "# No code snippet provided"}

## Detailed Issue Analysis:

### 1. Syntax Analysis
- Check for proper syntax structure
- Verify indentation consistency 
- Validate bracket/parentheses matching
- Review variable declarations

### 2. Logic Flow Analysis
- Entry Points: Verify function/method entry points
- Control Flow: Check if/else, loop conditions
- Return Statements: Ensure all code paths return values
- Edge Cases: Test boundary conditions

### 3. Common Issues Detected:
1. Variable Scope: Check if variables are defined in correct scope
2. Type Mismatches: Verify data types in operations
3. Null/None Handling: Add checks for null/undefined values
4. Resource Management: Ensure proper cleanup of resources

### 4. Debugging Recommendations:
- Add debugging prints and logging
- Use try/except blocks for error handling
- Include input validation
- Add unit tests for verification

### 5. Suggested Fix:
def corrected_function(input_data):
    \"\"\"Corrected version with error handling.\"\"\"
    if not input_data:
        raise ValueError("Input data cannot be empty")

    try:
        result = process_input(input_data)
        return result
    except Exception as e:
        logging.error(f"Processing failed: {{e}}")
        raise

## Summary:
The analysis identified areas for improvement. The corrected version addresses 
the main issues and includes proper error handling and validation.
"""
        )
        return analysis

    def get_stats(self) -> Dict[str, Any]:
        """Get router statistics."""
        return {
            "total_requests": self.request_count,
            "supported_models": list(self.model_handlers.keys()),
            "model_capabilities": {
                model.value: capabilities.dict() 
                for model, capabilities in MODEL_CAPABILITIES.items()
            }
        }
