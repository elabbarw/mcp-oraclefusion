"""AP invoice write tool definitions and handlers (create, change status)."""

from typing import Any, Dict
from oracle_fusion_mcp._types import Request
from ...auth.entra import ValidatedUser
from ...oracle.client import OracleClient
from ._helpers import _text_result

TOOLS = [
    {"name": "create_invoice", "description": "Create a new Accounts Payable invoice in Oracle Fusion. Requires MCP_MODE=full.", "inputSchema": {"type": "object", "properties": {"body": {"type": "object", "description": "Invoice payload matching Oracle invoices REST schema."}}, "required": ["body"]}},
    {"name": "change_invoice_status", "description": "Change the status of an AP invoice via Oracle action endpoints. Requires MCP_MODE=full.", "inputSchema": {"type": "object", "properties": {"invoice_id": {"type": "integer"}, "action": {"type": "string", "enum": ["CANCEL", "VALIDATE"]}, "reason": {"type": "string"}}, "required": ["invoice_id", "action"]}},
]

async def handle_create_invoice(request: Request, session: ValidatedUser, params: Dict[str, Any], oracle_client: OracleClient) -> Dict[str, Any]:
    return _text_result(await oracle_client.create_invoice(body=params["body"]))

async def handle_change_invoice_status(request: Request, session: ValidatedUser, params: Dict[str, Any], oracle_client: OracleClient) -> Dict[str, Any]:
    return _text_result(await oracle_client.change_invoice_status(invoice_id=params["invoice_id"], action=params["action"], reason=params.get("reason")))

HANDLERS = {"create_invoice": handle_create_invoice, "change_invoice_status": handle_change_invoice_status}
