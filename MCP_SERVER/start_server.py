#!/usr/bin/env python3
"""
Startup script for MCP FastAPI Server.

This script handles server initialization, configuration validation,
and graceful startup/shutdown.
"""

import asyncio
import signal
import sys
import uvicorn
from contextlib import asynccontextmanager
import logging

from config import settings, setup_logging, validate_settings
from main import app

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

class ServerManager:
    """Manages server lifecycle and graceful shutdown."""

    def __init__(self):
        self.should_exit = False
        self.server = None

    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.should_exit = True
        if self.server:
            self.server.should_exit = True

    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    async def start_server(self):
        """Start the FastAPI server."""
        try:
            # Validate configuration
            validate_settings()
            logger.info("Configuration validation passed")

            # Configure uvicorn
            config = uvicorn.Config(
                app=app,
                host=settings.host,
                port=settings.port,
                log_level=settings.log_level.lower(),
                reload=settings.reload,
                workers=1 if settings.reload else 4,
                access_log=True,
                server_header=False,
                date_header=False,
            )

            # Create and start server
            self.server = uvicorn.Server(config)

            logger.info(f"Starting MCP FastAPI Server on {settings.host}:{settings.port}")
            logger.info(f"Debug mode: {settings.debug}")
            logger.info(f"Reload mode: {settings.reload}")
            logger.info(f"Documentation available at: http://{settings.host}:{settings.port}/docs")

            await self.server.serve()

        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            sys.exit(1)

    def run(self):
        """Run the server with proper signal handling."""
        try:
            self.setup_signal_handlers()
            asyncio.run(self.start_server())
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        except Exception as e:
            logger.error(f"Server error: {e}")
            sys.exit(1)
        finally:
            logger.info("Server shutdown complete")

def main():
    """Main entry point."""
    print("🚀 MCP FastAPI Server")
    print(f"📋 Version: {settings.version}")
    print(f"🔧 Environment: {'Development' if settings.debug else 'Production'}")
    print("-" * 50)

    # Create and run server manager
    server_manager = ServerManager()
    server_manager.run()

if __name__ == "__main__":
    main()
