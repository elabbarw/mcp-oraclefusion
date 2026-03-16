"""Accounts Receivable tool definitions and handlers."""

from typing import Any, Dict
from oracle_fusion_mcp._types import Request
from ...auth.entra import ValidatedUser
from ...oracle.client import OracleClient
from ._helpers import _text_result

TOOLS = [
    {"name": "search_ar_invoices", "description": "Search Accounts Receivable invoices (customer billing) in Oracle Fusion.", "inputSchema": {"type": "object", "properties": {"customer": {"type": "string"}, "business_unit": {"type": "string"}, "date_from": {"type": "string"}, "date_to": {"type": "string"}, "status": {"type": "string"}, "q": {"type": "string"}, "limit": {"type": "integer", "default": 25}, "offset": {"type": "integer", "default": 0}}, "required": []}},
    {"name": "get_ar_invoice_details", "description": "Get full details for a single AR invoice by its numeric CustomerTransactionId.", "inputSchema": {"type": "object", "properties": {"transaction_id": {"type": "integer"}, "expand_lines": {"type": "boolean", "default": False}}, "required": ["transaction_id"]}},
    {"name": "search_receipts", "description": "Search AR receipts (customer payments received) in Oracle Fusion.", "inputSchema": {"type": "object", "properties": {"customer": {"type": "string"}, "receipt_number": {"type": "string"}, "business_unit": {"type": "string"}, "date_from": {"type": "string"}, "date_to": {"type": "string"}, "q": {"type": "string"}, "limit": {"type": "integer", "default": 25}, "offset": {"type": "integer", "default": 0}}, "required": []}},
]

async def handle_search_ar_invoices(request: Request, session: ValidatedUser, params: Dict[str, Any], oracle_client: OracleClient) -> Dict[str, Any]:
    records, has_more, total = await oracle_client.search_ar_invoices(customer=params.get("customer"), business_unit=params.get("business_unit"), date_from=params.get("date_from"), date_to=params.get("date_to"), status=params.get("status"), q=params.get("q"), limit=params.get("limit", 25), offset=params.get("offset", 0))
    return _text_result({"records": records, "has_more": has_more, "total": total})

async def handle_get_ar_invoice_details(request: Request, session: ValidatedUser, params: Dict[str, Any], oracle_client: OracleClient) -> Dict[str, Any]:
    return _text_result(await oracle_client.get_ar_invoice(transaction_id=params["transaction_id"], expand_lines=params.get("expand_lines", False)))

async def handle_search_receipts(request: Request, session: ValidatedUser, params: Dict[str, Any], oracle_client: OracleClient) -> Dict[str, Any]:
    records, has_more, total = await oracle_client.search_receipts(customer=params.get("customer"), date_from=params.get("date_from"), date_to=params.get("date_to"), receipt_number=params.get("receipt_number"), business_unit=params.get("business_unit"), q=params.get("q"), limit=params.get("limit", 25), offset=params.get("offset", 0))
    return _text_result({"records": records, "has_more": has_more, "total": total})

HANDLERS = {"search_ar_invoices": handle_search_ar_invoices, "get_ar_invoice_details": handle_get_ar_invoice_details, "search_receipts": handle_search_receipts}
