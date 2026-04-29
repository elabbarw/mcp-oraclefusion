"""
Oracle Fusion MCP Server — STDIO transport (packaged entry point)

Runs the full Oracle Fusion tool suite locally with your own Oracle
credentials. No central server or authentication service required.

Quick start
-----------
    export ORACLE_FUSION_BASE_URL=https://your-oracle-instance.example.com
    export ORACLE_USERNAME=your.name@example.com
    export ORACLE_PASSWORD=your_oracle_password
    python stdio_server.py

Or install via uvx and configure your MCP client:

    {
      "mcpServers": {
        "oracle-fusion": {
          "command": "uvx",
          "args": ["mcp-oraclefusion"],
          "env": {
            "ORACLE_FUSION_BASE_URL": "https://your-oracle-instance.example.com",
            "ORACLE_USERNAME": "your.name@example.com",
            "ORACLE_PASSWORD": "your_oracle_password"
          }
        }
      }
    }

All 24 read tools (and 7 write tools when MCP_MODE=full) are available.
Oracle credentials are read from env at startup and injected into every
tool call. Supports Oracle JWT auth (private key + certificate) or
Basic Auth (username + password) — JWT is tried first.
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, Optional


# ---------------------------------------------------------------------------
# Logging: send to stderr so stdout stays clean for JSON-RPC
# ---------------------------------------------------------------------------

logging.basicConfig(
    stream=sys.stderr,
    level=os.environ.get("LOG_LEVEL", "WARNING"),
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger("oracle_stdio")


# ---------------------------------------------------------------------------
# Minimal request/state mock
# ---------------------------------------------------------------------------

class _State:
    """Attribute bag — mirrors starlette.datastructures.State."""
    pass


class _MockRequest:
    """
    Stand-in for a web framework Request used only for request.state access.

    The tool dispatcher in oracle_fusion_mcp/mcp/tools/__init__.py reads:
        basic_auth = getattr(request.state, "basic_auth", None)
    and builds an OracleClient from those credentials. Setting
    request.state.basic_auth here is the only integration point needed.
    """
    def __init__(self) -> None:
        self.state = _State()


# ---------------------------------------------------------------------------
# JSON-RPC I/O helpers
# ---------------------------------------------------------------------------

def _write(obj: Dict[str, Any]) -> None:
    """Serialise a JSON-RPC object and write it as one line to stdout."""
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def _error(request_id: Any, code: int, message: str) -> Dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }


# ---------------------------------------------------------------------------
# Main async loop
# ---------------------------------------------------------------------------

async def _run(username: str, password: str) -> None:
    """
    Read JSON-RPC messages from stdin one line at a time, dispatch to the
    existing tool package, and write responses to stdout.
    """
    # Lazy imports after env is loaded — keeps startup fast and avoids
    # triggering get_settings() before the caller has set env vars.
    from oracle_fusion_mcp.config.settings import get_settings
    from oracle_fusion_mcp.auth.entra import ValidatedUser
    from oracle_fusion_mcp.auth.oracle_jwt import get_oracle_jwt_signer
    from oracle_fusion_mcp.mcp.tools import get_tools_list, handle_tool_call

    settings = get_settings()
    mode = settings.MCP_MODE

    # Build the mock request once; credentials are reused for every tool call.
    request = _MockRequest()

    # Try JWT auth first, fall back to basic auth.
    jwt_signer = get_oracle_jwt_signer()
    if jwt_signer:
        request.state.oracle_jwt = True
        auth_method = "Oracle JWT"
    else:
        if not password:
            sys.stdout.write(json.dumps(_error(
                None, -32603,
                "No auth configured. Set ORACLE_JWT_* env vars for JWT auth, "
                "or ORACLE_PASSWORD for Basic Auth."
            )) + "\n")
            sys.stdout.flush()
            sys.exit(1)
        request.state.basic_auth = (username, password)
        auth_method = "Basic Auth"

    # ValidatedUser is required by handle_tool_call's signature. In JWT mode
    # the email is used to mint per-request Oracle tokens.
    session = ValidatedUser(sub=username, email=username, name=username)

    logger.info(
        "Oracle Fusion STDIO MCP server ready (mode=%s, user=%s, auth=%s)",
        mode,
        username,
        auth_method,
    )

    loop = asyncio.get_event_loop()

    while True:
        try:
            line = await loop.run_in_executor(None, sys.stdin.readline)
        except Exception as exc:
            logger.error("stdin read error: %s", exc)
            break

        if not line:  # EOF — client closed the connection
            break

        line = line.strip()
        if not line:
            continue

        try:
            msg = json.loads(line)
        except json.JSONDecodeError as exc:
            logger.warning("JSON parse error: %s", exc)
            _write(_error(None, -32700, "Parse error"))
            continue

        method = msg.get("method", "")
        request_id = msg.get("id")  # None for notifications
        params: Dict[str, Any] = msg.get("params") or {}

        try:
            if method == "notifications/initialized":
                # Notifications expect no response
                continue

            elif method == "initialize":
                _write({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": settings.MCP_VERSION,
                        "capabilities": {
                            "tools": {"listChanged": True},
                            "resources": {},
                            "prompts": {},
                        },
                        "serverInfo": {
                            "name": settings.MCP_SERVER_NAME,
                            "version": settings.MCP_SERVER_VERSION,
                        },
                    },
                })

            elif method == "tools/list":
                result = await get_tools_list(mode=mode)
                _write({"jsonrpc": "2.0", "id": request_id, "result": result})

            elif method == "tools/call":
                tool_name: Optional[str] = params.get("name")
                tool_arguments: Dict[str, Any] = params.get("arguments") or {}
                result = await handle_tool_call(
                    request, session, tool_name, tool_arguments
                )
                _write({"jsonrpc": "2.0", "id": request_id, "result": result})

            elif method == "resources/list":
                _write({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {"resources": []},
                })

            elif method == "prompts/list":
                _write({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {"prompts": []},
                })

            else:
                _write(_error(request_id, -32601, f"Method not found: {method}"))

        except Exception as exc:
            logger.error("Error handling %s: %s", method, exc, exc_info=True)
            _write(_error(request_id, -32603, f"Internal error: {exc}"))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Validate required env vars and start the STDIO event loop."""
    username = os.environ.get("ORACLE_USERNAME", "").strip()
    password = os.environ.get("ORACLE_PASSWORD", "").strip()
    base_url = os.environ.get("ORACLE_FUSION_BASE_URL", "").strip()

    if not username:
        sys.stdout.write(json.dumps(_error(
            None, -32603,
            "ORACLE_USERNAME env var is required for STDIO mode"
        )) + "\n")
        sys.stdout.flush()
        sys.exit(1)

    if not base_url:
        sys.stdout.write(json.dumps(_error(
            None, -32603,
            "ORACLE_FUSION_BASE_URL env var is required"
        )) + "\n")
        sys.stdout.flush()
        sys.exit(1)

    # Password is optional — JWT auth can be used instead.
    asyncio.run(_run(username, password))


if __name__ == "__main__":
    main()
