"""PO write tool definitions and handlers (create, update distribution, change status)."""

from typing import Any, Dict
from oracle_fusion_mcp._types import Request
from ...auth.entra import ValidatedUser
from ...oracle.client import OracleClient
from ._helpers import _text_result

TOOLS = [
    {"name": "create_purchase_order", "description": "Create a new draft purchase order in Oracle Fusion. Requires MCP_MODE=full.", "inputSchema": {"type": "object", "properties": {"body": {"type": "object"}}, "required": ["body"]}},
    {"name": "update_po_distribution", "description": "Update a distribution on a draft PO line. Requires MCP_MODE=full.", "inputSchema": {"type": "object", "properties": {"po_header_id": {"type": "integer"}, "line_id": {"type": "integer"}, "schedule_id": {"type": "integer"}, "distribution_id": {"type": "integer"}, "updates": {"type": "object"}}, "required": ["po_header_id", "line_id", "schedule_id", "distribution_id", "updates"]}},
    {"name": "change_po_status", "description": "Change the status of a purchase order via Oracle action endpoints. Requires MCP_MODE=full.", "inputSchema": {"type": "object", "properties": {"po_header_id": {"type": "integer"}, "action": {"type": "string", "enum": ["CLOSE", "CANCEL", "FREEZE", "HOLD", "UNFREEZE", "RELEASE HOLD", "REOPEN"]}}, "required": ["po_header_id", "action"]}},
]

async def handle_create_purchase_order(request: Request, session: ValidatedUser, params: Dict[str, Any], oracle_client: OracleClient) -> Dict[str, Any]:
    return _text_result(await oracle_client.create_purchase_order(body=params["body"]))

async def handle_update_po_distribution(request: Request, session: ValidatedUser, params: Dict[str, Any], oracle_client: OracleClient) -> Dict[str, Any]:
    return _text_result(await oracle_client.update_po_distribution(po_header_id=params["po_header_id"], line_id=params["line_id"], schedule_id=params["schedule_id"], distribution_id=params["distribution_id"], updates=params["updates"]))

async def handle_change_po_status(request: Request, session: ValidatedUser, params: Dict[str, Any], oracle_client: OracleClient) -> Dict[str, Any]:
    return _text_result(await oracle_client.change_po_status(po_header_id=params["po_header_id"], action=params["action"]))

HANDLERS = {"create_purchase_order": handle_create_purchase_order, "update_po_distribution": handle_update_po_distribution, "change_po_status": handle_change_po_status}
