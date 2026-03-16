"""Requisition write tool definitions and handlers (create, change status)."""

from typing import Any, Dict
from oracle_fusion_mcp._types import Request
from ...auth.entra import ValidatedUser
from ...oracle.client import OracleClient
from ._helpers import _text_result

TOOLS = [
    {"name": "create_requisition", "description": "Create a new purchase requisition in Oracle Fusion. Requires MCP_MODE=full.", "inputSchema": {"type": "object", "properties": {"body": {"type": "object"}}, "required": ["body"]}},
    {"name": "change_requisition_status", "description": "Change the status of a purchase requisition. Requires MCP_MODE=full.", "inputSchema": {"type": "object", "properties": {"requisition_id": {"type": "integer"}, "action": {"type": "string", "enum": ["WITHDRAW", "CANCEL"]}}, "required": ["requisition_id", "action"]}},
]

async def handle_create_requisition(request: Request, session: ValidatedUser, params: Dict[str, Any], oracle_client: OracleClient) -> Dict[str, Any]:
    return _text_result(await oracle_client.create_requisition(body=params["body"]))

async def handle_change_requisition_status(request: Request, session: ValidatedUser, params: Dict[str, Any], oracle_client: OracleClient) -> Dict[str, Any]:
    return _text_result(await oracle_client.change_requisition_status(requisition_id=params["requisition_id"], action=params["action"]))

HANDLERS = {"create_requisition": handle_create_requisition, "change_requisition_status": handle_change_requisition_status}
