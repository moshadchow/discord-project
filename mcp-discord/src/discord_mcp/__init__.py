"""Discord integration for Model Context Protocol."""

import asyncio
import importlib
import sys
import warnings
import tracemalloc

__version__ = "0.1.0"

def main():
    """Main entry point for the package."""
    # Enable tracemalloc for better debugging
    tracemalloc.start()
    _configure_windows_event_loop()
    
    # Suppress PyNaCl warning since we don't use voice features
    warnings.filterwarnings('ignore', module='discord.client', message='PyNaCl is not installed')
    
    try:
        server = importlib.import_module(".server", __name__)
        # Properly handle async execution
        asyncio.run(server.main())
    except KeyboardInterrupt:
        print("\nShutting down Discord MCP server...")
    except Exception as e:
        print(f"Error running Discord MCP server: {e}")
        raise

# Expose important items at package level
__all__ = ['main', 'server', 'api']


def _configure_windows_event_loop():
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def __getattr__(name):
    if name == "server":
        return importlib.import_module(".server", __name__)
    if name == "api":
        return importlib.import_module(".api", __name__)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
