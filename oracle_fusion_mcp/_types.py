"""
Type compatibility shim — allows oracle_fusion_mcp to run without FastAPI.

In STDIO mode, requests are handled by a minimal mock object defined in
stdio_server.py. This module provides the Request type annotation used
throughout the tool handlers, falling back to a simple stub when FastAPI
is not installed.
"""

try:
    from fastapi import Request  # noqa: F401
except ImportError:
    class Request:  # type: ignore[no-redef]
        """Minimal request stub for type annotations (no FastAPI required)."""
        def __init__(self) -> None:
            from types import SimpleNamespace
            self.state = SimpleNamespace()
