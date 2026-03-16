"""Infrastructure/connectivity tool definitions and handlers."""

from typing import Any, Dict
from oracle_fusion_mcp._types import Request
from ...auth.entra import ValidatedUser
from ...oracle.client import OracleClient
from ._helpers import _text_result

TOOLS = [
    {"name": "test_oracle_connection", "description": "Test connectivity to Oracle Fusion REST API. Returns connection status and record counts. Use this first to verify the connection is working.", "inputSchema": {"type": "object", "properties": {}, "required": []}},
]

async def handle_test_oracle_connection(request: Request, session: ValidatedUser, params: Dict[str, Any], oracle_client: OracleClient) -> Dict[str, Any]:
    return _text_result(await oracle_client.test_connection())

HANDLERS = {"test_oracle_connection": handle_test_oracle_connection}
